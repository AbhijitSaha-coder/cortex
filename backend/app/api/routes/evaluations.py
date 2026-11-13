import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.evaluation import EvaluationDataset, EvaluationRun
from app.schemas.evaluation import (
    EvaluationRunRequest,
    EvaluationRunResponse,
    EvaluationDatasetResponse,
    EvaluationDatasetCreate,
)
from app.services.evaluation_service import EvaluationFramework

router = APIRouter(prefix="/evaluations", tags=["Evaluation & Benchmarking"])


@router.get("/datasets", response_model=List[EvaluationDatasetResponse])
def list_datasets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists available evaluation datasets and benchmarks."""
    framework = EvaluationFramework(db, current_user.id)
    # Ensure default dataset exists
    framework.get_or_create_default_dataset()

    datasets = db.query(EvaluationDataset).all()
    return datasets


@router.post("/run", response_model=EvaluationRunResponse, status_code=status.HTTP_201_CREATED)
def trigger_evaluation_run(
    payload: EvaluationRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Executes an empirical RAG evaluation run measuring Recall@K, MRR, relevance,
    groundedness, latency, and token consumption on actual queries.
    """
    framework = EvaluationFramework(db, current_user.id)
    run = framework.run_evaluation(
        dataset_id=payload.dataset_id,
        top_k=payload.top_k,
        retrieval_mode=payload.retrieval_mode,
    )

    results = json.loads(run.results_json) if run.results_json else []
    return EvaluationRunResponse(
        id=run.id,
        dataset_id=run.dataset_id,
        status=run.status,
        recall_at_k=run.recall_at_k,
        mrr=run.mrr,
        relevance_score=run.relevance_score,
        citation_precision=run.citation_precision,
        groundedness_score=run.groundedness_score,
        avg_latency_ms=run.avg_latency_ms,
        total_tokens=run.total_tokens,
        estimated_cost_usd=run.estimated_cost_usd,
        sample_count=len(results),
        results=results,
        created_at=run.created_at,
    )


@router.get("", response_model=List[EvaluationRunResponse])
def list_evaluation_runs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists historical evaluation runs."""
    runs = (
        db.query(EvaluationRun)
        .filter(EvaluationRun.user_id == current_user.id)
        .order_by(EvaluationRun.created_at.desc())
        .limit(20)
        .all()
    )
    res = []
    for r in runs:
        results = json.loads(r.results_json) if r.results_json else []
        res.append(
            EvaluationRunResponse(
                id=r.id,
                dataset_id=r.dataset_id,
                status=r.status,
                recall_at_k=r.recall_at_k,
                mrr=r.mrr,
                relevance_score=r.relevance_score,
                citation_precision=r.citation_precision,
                groundedness_score=r.groundedness_score,
                avg_latency_ms=r.avg_latency_ms,
                total_tokens=r.total_tokens,
                estimated_cost_usd=r.estimated_cost_usd,
                sample_count=len(results),
                results=results,
                created_at=r.created_at,
            )
        )
    return res

