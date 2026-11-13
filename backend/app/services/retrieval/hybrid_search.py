import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.retrieval.vector_search import VectorSearchService
from app.services.retrieval.keyword_search import KeywordSearchService
from app.services.retrieval.reranker import CrossEncoderReranker


class HybridSearchEngine:
    """
    Hybrid Search Engine implementing Reciprocal Rank Fusion (RRF).
    Combines dense semantic vector retrieval with sparse lexical full-text retrieval,
    followed by an optional cross-encoder reranking pass.
    """

    def __init__(self, db: Session):
        self.db = db
        self.vector_search = VectorSearchService(db)
        self.keyword_search = KeywordSearchService(db)
        self.reranker = CrossEncoderReranker()
        self.rrf_k = settings.RRF_K

    def _reciprocal_rank_fusion(
        self,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Calculates RRF score:
        RRF_Score(d) = sum_{method} 1 / (k + rank_method(d))
        """
        fused_scores: Dict[str, float] = {}
        chunks_map: Dict[str, Dict[str, Any]] = {}

        # 1. Process Semantic Ranks
        for rank, item in enumerate(semantic_results, 1):
            cid = item["chunk_id"]
            chunks_map[cid] = item
            fused_scores[cid] = fused_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))

        # 2. Process Keyword Ranks
        for rank, item in enumerate(keyword_results, 1):
            cid = item["chunk_id"]
            if cid not in chunks_map:
                chunks_map[cid] = item
            fused_scores[cid] = fused_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))

        # 3. Create sorted combined list
        combined = []
        for cid, score in fused_scores.items():
            entry = dict(chunks_map[cid])
            entry["score"] = round(score, 6)
            entry["retrieval_source"] = "hybrid_rrf"
            combined.append(entry)

        combined.sort(key=lambda x: x["score"], reverse=True)
        return combined

    def search(
        self,
        query: str,
        user_id: str,
        mode: str = "hybrid",
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
        rerank: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes search under requested mode ('hybrid', 'semantic', or 'keyword').
        """
        start_time = time.time()
        fetch_limit = top_k * 3 if mode == "hybrid" or rerank else top_k

        if mode == "semantic":
            candidates = self.vector_search.search(
                query=query, user_id=user_id, top_k=fetch_limit, document_ids=document_ids
            )
        elif mode == "keyword":
            candidates = self.keyword_search.search(
                query=query, user_id=user_id, top_k=fetch_limit, document_ids=document_ids
            )
        else:  # hybrid
            sem_results = self.vector_search.search(
                query=query, user_id=user_id, top_k=fetch_limit, document_ids=document_ids
            )
            kw_results = self.keyword_search.search(
                query=query, user_id=user_id, top_k=fetch_limit, document_ids=document_ids
            )
            candidates = self._reciprocal_rank_fusion(sem_results, kw_results)

        # Optional Reranking stage
        if rerank and candidates:
            final_results = self.reranker.rerank(query, candidates, top_k=top_k)
        else:
            final_results = candidates[:top_k]

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "query": query,
            "mode": mode,
            "top_k": top_k,
            "total_results": len(final_results),
            "execution_time_ms": elapsed_ms,
            "results": final_results,
        }
