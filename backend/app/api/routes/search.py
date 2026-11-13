from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.search import SearchRequest, SearchResponse
from app.services.retrieval.hybrid_search import HybridSearchEngine

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
def search(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Modular retrieval endpoint supporting hybrid search (RRF), semantic search,
    and full-text keyword search with optional cross-encoder reranking.
    """
    engine = HybridSearchEngine(db)
    results = engine.search(
        query=request.query,
        user_id=current_user.id,
        mode=request.mode,
        top_k=request.top_k,
        document_ids=request.document_ids,
        rerank=request.rerank,
    )
    return results

