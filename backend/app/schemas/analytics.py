from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    total_documents: int
    processed_documents: int
    failed_documents: int
    total_chunks: int
    total_conversations: int
    total_reports: int
    storage_bytes: int
    recent_activity: List[Dict[str, Any]]


class UsageSummaryResponse(BaseModel):
    total_requests: int
    total_tokens: int
    estimated_cost_usd: float
    usage_by_type: Dict[str, int]
    recent_usage: List[Dict[str, Any]]

