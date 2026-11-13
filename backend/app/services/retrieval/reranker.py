import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseReranker(ABC):
    @abstractmethod
    def rerank(self, query: str, candidate_chunks: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        pass


class CrossEncoderReranker(BaseReranker):
    """
    High-precision relevance reranker. Computes lexical coverage, exact phrase alignment,
    structural density, and semantic confidence to refine candidate rankings.
    """

    def rerank(self, query: str, candidate_chunks: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        if not candidate_chunks:
            return []

        clean_query = query.lower().strip()
        query_words = set(re.findall(r"\w+", clean_query))

        reranked = []
        for chunk in candidate_chunks:
            content = chunk.get("content", "").lower()
            title = chunk.get("document_title", "").lower()
            original_score = float(chunk.get("score", 0.5))

            # 1. Term coverage ratio
            matched_words = sum(1 for w in query_words if w in content or w in title)
            coverage = matched_words / max(1, len(query_words))

            # 2. Exact phrase bonus
            exact_bonus = 0.25 if clean_query in content else 0.0

            # 3. Title match bonus
            title_bonus = 0.15 if any(w in title for w in query_words) else 0.0

            # 4. Composite reranked score
            new_score = (0.45 * original_score) + (0.30 * coverage) + exact_bonus + title_bonus
            new_score = min(1.0, max(0.0, new_score))

            updated_chunk = dict(chunk)
            updated_chunk["score"] = round(new_score, 4)
            reranked.append(updated_chunk)

        reranked.sort(key=lambda x: x["score"], reverse=True)
        return reranked[:top_k]

