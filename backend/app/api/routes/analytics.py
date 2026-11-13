from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.document import Document, DocumentChunk
from app.models.conversation import Conversation, Message
from app.models.report import ResearchReport
from app.models.evaluation import UsageRecord
from app.schemas.analytics import DashboardStatsResponse, UsageSummaryResponse

router = APIRouter(prefix="/analytics", tags=["Analytics & Usage"])


@router.get("/dashboard", response_model=DashboardStatsResponse)
def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aggregates high-level telemetry and knowledge base statistics."""
    total_docs = db.query(Document).filter(Document.user_id == current_user.id).count()
    completed_docs = db.query(Document).filter(Document.user_id == current_user.id, Document.status == "completed").count()
    failed_docs = db.query(Document).filter(Document.user_id == current_user.id, Document.status == "failed").count()
    total_chunks = db.query(DocumentChunk).filter(DocumentChunk.user_id == current_user.id).count()
    total_convs = db.query(Conversation).filter(Conversation.user_id == current_user.id).count()
    total_reports = db.query(ResearchReport).filter(ResearchReport.user_id == current_user.id).count()

    total_storage = (
        db.query(func.sum(Document.file_size_bytes))
        .filter(Document.user_id == current_user.id)
        .scalar()
        or 0
    )

    # Recent activity items
    recent_docs = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .limit(5)
        .all()
    )
    recent_activity = [
        {
            "id": d.id,
            "type": "document_ingested",
            "title": d.title,
            "timestamp": d.created_at.isoformat(),
            "status": d.status,
            "extra": f"{d.chunk_count} chunks indexed",
        }
        for d in recent_docs
    ]

    return DashboardStatsResponse(
        total_documents=total_docs,
        processed_documents=completed_docs,
        failed_documents=failed_docs,
        total_chunks=total_chunks,
        total_conversations=total_convs,
        total_reports=total_reports,
        storage_bytes=total_storage,
        recent_activity=recent_activity,
    )


@router.get("/usage", response_model=UsageSummaryResponse)
def get_usage_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Summarizes API usage, token consumption, and estimated costs."""
    records = (
        db.query(UsageRecord)
        .filter(UsageRecord.user_id == current_user.id)
        .order_by(UsageRecord.created_at.desc())
        .all()
    )

    total_requests = len(records)
    total_tokens = sum(r.total_tokens for r in records)
    total_cost = sum(r.estimated_cost for r in records)

    usage_by_type: Dict[str, int] = {}
    for r in records:
        usage_by_type[r.request_type] = usage_by_type.get(r.request_type, 0) + r.total_tokens

    recent = [
        {
            "id": r.id,
            "request_type": r.request_type,
            "total_tokens": r.total_tokens,
            "estimated_cost": r.estimated_cost,
            "model_name": r.model_name,
            "created_at": r.created_at.isoformat(),
        }
        for r in records[:15]
    ]

    return UsageSummaryResponse(
        total_requests=total_requests,
        total_tokens=total_tokens,
        estimated_cost_usd=round(total_cost, 4),
        usage_by_type=usage_by_type,
        recent_usage=recent,
    )

