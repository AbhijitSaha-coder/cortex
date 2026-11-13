from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query string")
    mode: str = Field("hybrid", description="Retrieval mode: 'hybrid', 'semantic', or 'keyword'")
    top_k: int = Field(5, ge=1, le=50, description="Number of results to retrieve")
    document_ids: Optional[List[str]] = Field(None, description="Optional document ID filter")
    rerank: bool = Field(True, description="Whether to apply cross-encoder / reciprocal reranking")


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    content: str
    page_number: Optional[int] = None
    chunk_index: int
    score: float
    retrieval_source: str  # semantic, keyword, hybrid_rrf
    metadata: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    query: str
    mode: str
    top_k: int
    total_results: int
    execution_time_ms: float
    results: List[SearchResultItem]
