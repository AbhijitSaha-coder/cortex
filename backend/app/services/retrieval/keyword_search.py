import re
import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.document import DocumentChunk, Document
from app.core.logging import logger


class KeywordSearchService:
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
        Executes full-text keyword retrieval.
        Uses PostgreSQL tsvector/tsquery where available, with BM25-style frequency scoring fallback.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        is_postgres = self.db.bind.dialect.name == "postgresql"

        if is_postgres:
            try:
                doc_filter_sql = ""
                params = {"user_id": user_id, "query": clean_query, "top_k": top_k}
                if document_ids:
                    doc_filter_sql = "AND c.document_id = ANY(:doc_ids)"
                    params["doc_ids"] = document_ids

                sql = f"""
                    SELECT c.id as chunk_id, c.document_id, c.chunk_index, c.content,
                           c.page_number, d.title as document_title,
                           ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', :query)) as score
                    FROM document_chunks c
                    JOIN documents d ON c.document_id = d.id
                    WHERE c.user_id = :user_id
                      AND to_tsvector('english', c.content) @@ plainto_tsquery('english', :query)
                      {doc_filter_sql}
                    ORDER BY score DESC
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
                        "retrieval_source": "keyword",
                    })
                return results
            except Exception as e:
                logger.warning(f"Native postgres full-text query failed ({e}), using term-frequency fallback.")

        # SQLite fallback: Term-frequency & keyword scoring
        query_terms = [re.escape(w.lower()) for w in re.findall(r"\w+", clean_query) if len(w) > 1]
        if not query_terms:
            return []

        query_stmt = self.db.query(DocumentChunk, Document.title).join(Document, DocumentChunk.document_id == Document.id).filter(
            DocumentChunk.user_id == user_id
        )
        if document_ids:
            query_stmt = query_stmt.filter(DocumentChunk.document_id.in_(document_ids))

        all_chunks = query_stmt.all()
        scored = []

        for chunk, title in all_chunks:
            text_lower = chunk.content.lower()
            title_lower = title.lower()

            matches = 0
            for term in query_terms:
                term_count = len(re.findall(r"\b" + term + r"\b", text_lower))
                if term in title_lower:
                    term_count += 3  # Title match boost
                matches += term_count

            if matches > 0:
                # Log-scaled frequency score normalized by document length
                doc_len = max(10, len(chunk.content.split()))
                score = (math.log(1 + matches) / math.log(1 + doc_len)) * 10.0
                scored.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "document_title": title,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "page_number": chunk.page_number,
                    "score": round(score, 4),
                    "retrieval_source": "keyword",
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
