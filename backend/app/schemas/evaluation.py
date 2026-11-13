from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EvaluationSample(BaseModel):
    query: str
    ground_truth_answer: str
    expected_document_titles: Optional[List[str]] = None
    expected_chunk_ids: Optional[List[str]] = None


class EvaluationDatasetCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    samples: List[EvaluationSample] = Field(..., min_length=1)


class EvaluationDatasetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    sample_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class EvaluationRunRequest(BaseModel):
    dataset_id: Optional[str] = None  # If omitted, uses default built-in benchmark
    top_k: int = 5
    retrieval_mode: str = "hybrid"


class EvaluationRunResponse(BaseModel):
    id: str
    dataset_id: str
    status: str
    recall_at_k: float
    mrr: float
    relevance_score: float
    citation_precision: float
    groundedness_score: float
    avg_latency_ms: float
    total_tokens: int
    estimated_cost_usd: float
    sample_count: int
    results: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    class Config:
        from_attributes = True

