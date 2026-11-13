import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import logger
from app.core.errors import IngestionError
from app.models.document import Document, DocumentChunk, IngestionJob
from app.services.ingestion.extractor import (
    extract_text_from_pdf,
    extract_text_from_txt,
    extract_text_from_markdown,
    extract_text_from_url,
)
from app.services.ingestion.chunker import TextChunker
from app.services.ai.embeddings import embedding_service


class IngestionPipeline:
    def __init__(self, db: Session):
        self.db = db
        self.chunker = TextChunker(chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)

    def _generate_summary(self, chunks: List[Dict[str, Any]]) -> str:
        """Generates a concise 2-3 sentence overview from the first chunks."""
        if not chunks:
            return "No content available."
        sample_text = " ".join([c["content"] for c in chunks[:3]])
        sentences = [s.strip() for s in sample_text.split(".") if s.strip()]
        if len(sentences) >= 2:
            return ". ".join(sentences[:2]) + "."
        return sample_text[:200] + "..."

    def process_file_content(
        self,
        document_id: str,
        user_id: str,
        file_bytes: bytes,
        file_name: str,
        file_type: str,
    ) -> Document:
        """
        Runs the full ingestion pipeline for an uploaded file document.
        """
        doc = self.db.query(Document).filter(Document.id == document_id, Document.user_id == user_id).first()
        if not doc:
            raise IngestionError(f"Document {document_id} not found")

        job = self.db.query(IngestionJob).filter(IngestionJob.document_id == document_id).first()
        if not job:
            job = IngestionJob(
                document_id=document_id,
                user_id=user_id,
                status="processing",
                progress_percent=10,
                started_at=datetime.now(timezone.utc)
            )
            self.db.add(job)
        else:
            job.status = "processing"
            job.progress_percent = 10
            job.started_at = datetime.now(timezone.utc)
        
        doc.status = "processing"
        self.db.commit()

        try:
            # Step 1: Content Hash for Duplicate Detection
            content_hash = hashlib.sha256(file_bytes).hexdigest()
            doc.content_hash = content_hash
            job.progress_percent = 25
            self.db.commit()

            # Step 2: Extraction
            logger.info(f"Extracting content for document {document_id} ({file_name}, {file_type})")
            if file_type.lower() == "pdf":
                pages = extract_text_from_pdf(file_bytes)
            elif file_type.lower() == "txt":
                pages = extract_text_from_txt(file_bytes.decode("utf-8", errors="replace"))
            elif file_type.lower() in ("md", "markdown"):
                pages = extract_text_from_markdown(file_bytes.decode("utf-8", errors="replace"))
            else:
                raise IngestionError(f"Unsupported file type: {file_type}")

            if not pages:
                raise IngestionError("No readable text found in document.")

            job.progress_percent = 45
            self.db.commit()

            # Step 3: Chunking
            chunks_data = self.chunker.chunk_pages(pages)
            if not chunks_data:
                raise IngestionError("Document produced 0 valid chunks.")

            total_words = sum(c["word_count"] for c in chunks_data)
            doc.chunk_count = len(chunks_data)
            doc.word_count = total_words
            doc.summary = self._generate_summary(chunks_data)
            job.progress_percent = 60
            self.db.commit()

            # Step 4: Embedding generation in batches
            logger.info(f"Generating embeddings for {len(chunks_data)} chunks of doc {document_id}")
            chunk_texts = [c["content"] for c in chunks_data]
            
            # Batch embedding to stay well within API limits
            batch_size = 50
            all_embeddings = []
            for i in range(0, len(chunk_texts), batch_size):
                batch = chunk_texts[i : i + batch_size]
                emb_batch = embedding_service.embed_texts(batch)
                all_embeddings.extend(emb_batch)

            job.progress_percent = 85
            self.db.commit()

            # Step 5: Save Chunks in DB
            for chunk_dict, emb in zip(chunks_data, all_embeddings):
                chunk = DocumentChunk(
                    document_id=doc.id,
                    user_id=user_id,
                    chunk_index=chunk_dict["chunk_index"],
                    content=chunk_dict["content"],
                    word_count=chunk_dict["word_count"],
                    page_number=chunk_dict["page_number"],
                    embedding=emb,
                    metadata_json=json.dumps({
                        "file_name": file_name,
                        "file_type": file_type,
                        "page_number": chunk_dict["page_number"],
                    })
                )
                self.db.add(chunk)

            # Step 6: Finalize Status
            doc.status = "completed"
            job.status = "completed"
            job.progress_percent = 100
            job.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(doc)
            logger.info(f"Successfully completed ingestion for doc {document_id}")
            return doc

        except Exception as e:
            self.db.rollback()
            error_msg = str(e)
            logger.error(f"Ingestion failed for doc {document_id}: {error_msg}")
            doc.status = "failed"
            doc.error_message = error_msg
            if job:
                job.status = "failed"
                job.error_log = error_msg
                job.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            raise IngestionError(error_msg)

    def process_url(
        self,
        document_id: str,
        user_id: str,
        url: str,
    ) -> Document:
        """
        Runs the full ingestion pipeline for an imported web URL.
        """
        doc = self.db.query(Document).filter(Document.id == document_id, Document.user_id == user_id).first()
        if not doc:
            raise IngestionError(f"Document {document_id} not found")

        job = IngestionJob(
            document_id=document_id,
            user_id=user_id,
            status="processing",
            progress_percent=10,
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(job)
        doc.status = "processing"
        self.db.commit()

        try:
            # SSRF-safe extraction
            title, pages, metadata = extract_text_from_url(url)
            if not doc.title or doc.title == url:
                doc.title = title

            doc.metadata_json = json.dumps(metadata)
            job.progress_percent = 40
            self.db.commit()

            chunks_data = self.chunker.chunk_pages(pages)
            if not chunks_data:
                raise IngestionError("Website produced 0 readable text chunks.")

            total_words = sum(c["word_count"] for c in chunks_data)
            doc.chunk_count = len(chunks_data)
            doc.word_count = total_words
            doc.summary = self._generate_summary(chunks_data)
            job.progress_percent = 65
            self.db.commit()

            # Embeddings
            chunk_texts = [c["content"] for c in chunks_data]
            all_embeddings = embedding_service.embed_texts(chunk_texts)
            job.progress_percent = 85
            self.db.commit()

            for chunk_dict, emb in zip(chunks_data, all_embeddings):
                chunk = DocumentChunk(
                    document_id=doc.id,
                    user_id=user_id,
                    chunk_index=chunk_dict["chunk_index"],
                    content=chunk_dict["content"],
                    word_count=chunk_dict["word_count"],
                    page_number=chunk_dict["page_number"],
                    embedding=emb,
                    metadata_json=json.dumps({
                        "source_url": url,
                        "title": title,
                    })
                )
                self.db.add(chunk)

            doc.status = "completed"
            job.status = "completed"
            job.progress_percent = 100
            job.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(doc)
            return doc

        except Exception as e:
            self.db.rollback()
            error_msg = str(e)
            logger.error(f"URL ingestion failed for doc {document_id}: {error_msg}")
            doc.status = "failed"
            doc.error_message = error_msg
            job.status = "failed"
            job.error_log = error_msg
            job.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            raise IngestionError(error_msg)
