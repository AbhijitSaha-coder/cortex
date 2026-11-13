import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.document import DocumentChunk, Document
from app.services.ai.embeddings import embedding_service
from app.core.logging import logger


class VectorSearchService:
    def __init__(self, db: Session):
        self.db = db

    def search(
        self,
        query: str,
        user_id: str,
        top_k: int = 10,
        document_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes semantic vector search.
        Uses native pgvector distance operator on PostgreSQL,
        or numpy cosine similarity when running on SQLite / development mode.
        """
        query_vec = embedding_service.embed_query(query)
        is_postgres = self.db.bind.dialect.name == "postgresql"

        if is_postgres:
            try:
                # PostgreSQL pgvector cosine distance: embedding <=> :query_vec
                # Cosine similarity = 1 - cosine_distance
                doc_filter_sql = ""
                params = {"user_id": user_id, "query_vec": str(query_vec), "top_k": top_k}
                if document_ids:
                    doc_filter_sql = "AND c.document_id = ANY(:doc_ids)"
                    params["doc_ids"] = document_ids

                sql = f"""
                    SELECT c.id as chunk_id, c.document_id, c.chunk_index, c.content,
                           c.page_number, d.title as document_title,
                           1 - (c.embedding <=> CAST(:query_vec AS vector)) as score
                    FROM document_chunks c
                    JOIN documents d ON c.document_id = d.id
                    WHERE c.user_id = :user_id {doc_filter_sql}
                    ORDER BY c.embedding <=> CAST(:query_vec AS vector) ASC
                    LIMIT :top_k
                """
                rows = self.db.execute(text(sql), params).fetchall()
                results = []
                for row in rows:
                    results.append({
                        "chunk_id": row.chunk_id,
                        "document_id": row.document_id,
                        "document_title": row.document_title,
                        "chunk_index": row.chunk_index,
                        "content": row.content,
                        "page_number": row.page_number,
                        "score": float(row.score),
                        "retrieval_source": "semantic",
                    })
                return results
            except Exception as e:
                self.db.rollback()
                logger.warning(f"Native pgvector query failed ({e}), falling back to Python cosine similarity.")

        # SQLite / In-memory fallback
        query_stmt = self.db.query(DocumentChunk, Document.title).join(Document, DocumentChunk.document_id == Document.id).filter(
            DocumentChunk.user_id == user_id
        )
        if document_ids:
            query_stmt = query_stmt.filter(DocumentChunk.document_id.in_(document_ids))

        chunks_and_titles = query_stmt.all()
        if not chunks_and_titles:
            return []

        q_arr = np.array(query_vec, dtype=np.float32)
        q_norm = np.linalg.norm(q_arr)
        if q_norm == 0:
            return []

        scored = []
        for chunk, title in chunks_and_titles:
            if not chunk.embedding:
                continue
            c_arr = np.array(chunk.embedding, dtype=np.float32)
            c_norm = np.linalg.norm(c_arr)
            sim = 0.0
            if c_norm > 0:
                sim = float(np.dot(q_arr, c_arr) / (q_norm * c_norm))

            scored.append({
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "document_title": title,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "page_number": chunk.page_number,
                "score": sim,
                "retrieval_source": "semantic",
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

