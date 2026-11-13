import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.document import Document, DocumentChunk, IngestionJob
from app.schemas.document import (
    DocumentResponse,
    DocumentChunkResponse,
    DocumentStatusResponse,
    DocumentPreviewResponse,
    URLImportRequest,
)
from app.core.config import settings
from app.workers.tasks import ingest_file_task, ingest_url_task
from app.services.ingestion.pipeline import IngestionPipeline
from app.core.logging import logger

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Uploads a document (PDF, TXT, MD) and enqueues it for background ingestion and vectorization.
    """
    filename = file.filename or "uploaded_document"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Permitted extensions: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    file_bytes = await file.read()
    file_size = len(file_bytes)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    # Save to disk
    safe_name = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Create document record
    doc = Document(
        user_id=current_user.id,
        title=filename.rsplit(".", 1)[0].replace("_", " ").title(),
        file_name=filename,
        file_path=file_path,
        file_type=ext,
        file_size_bytes=file_size,
        status="queued",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # If celery is running or task_always_eager is enabled, dispatch task
    try:
        if settings.TASK_ALWAYS_EAGER:
            pipeline = IngestionPipeline(db)
            pipeline.process_file_content(
                document_id=doc.id,
                user_id=current_user.id,
                file_bytes=file_bytes,
                file_name=filename,
                file_type=ext,
            )
            db.refresh(doc)
        else:
            ingest_file_task.delay(doc.id, current_user.id, file_path, filename, ext)
    except Exception as e:
        logger.error(f"Failed to dispatch ingestion task: {e}")
        doc.status = "failed"
        doc.error_message = str(e)
        db.commit()

    return doc


@router.post("/import-url", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def import_url(
    payload: URLImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Imports and ingests content from a web URL with SSRF safeguards.
    """
    url_str = str(payload.url)
    doc_title = payload.title or url_str

    doc = Document(
        user_id=current_user.id,
        title=doc_title,
        file_name=url_str,
        file_type="url",
        source_url=url_str,
        file_size_bytes=0,
        status="queued",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        if settings.TASK_ALWAYS_EAGER:
            pipeline = IngestionPipeline(db)
            pipeline.process_url(document_id=doc.id, user_id=current_user.id, url=url_str)
            db.refresh(doc)
        else:
            ingest_url_task.delay(doc.id, current_user.id, url_str)
    except Exception as e:
        logger.error(f"Failed to dispatch URL task: {e}")
        doc.status = "failed"
        doc.error_message = str(e)
        db.commit()

    return doc


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Filter by title"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists all documents belonging to the authenticated user."""
    query = db.query(Document).filter(Document.user_id == current_user.id)
    if file_type:
        query = query.filter(Document.file_type == file_type.lower())
    if status:
        query = query.filter(Document.status == status.lower())
    if search:
        query = query.filter(Document.title.ilike(f"%{search}%"))

    docs = query.order_by(Document.created_at.desc()).offset(offset).limit(limit).all()
    return docs


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Gets details of a single document with user isolation."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deletes a document and automatically cascades vector chunks deletion."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Remove physical file if exists
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            logger.warning(f"Could not remove local file {doc.file_path}: {e}")

    db.delete(doc)
    db.commit()
    return None


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns ingestion progress and status for a document."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    job = db.query(IngestionJob).filter(IngestionJob.document_id == document_id).order_by(IngestionJob.created_at.desc()).first()
    progress = job.progress_percent if job else (100 if doc.status == "completed" else 0)

    return DocumentStatusResponse(
        id=doc.id,
        status=doc.status,
        progress_percent=progress,
        chunk_count=doc.chunk_count,
        error_message=doc.error_message,
    )


@router.get("/{document_id}/preview", response_model=DocumentPreviewResponse)
def get_document_preview(
    document_id: str,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns document metadata and its first chunks for inspection."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id, DocumentChunk.user_id == current_user.id)
        .order_by(DocumentChunk.chunk_index.asc())
        .limit(limit)
        .all()
    )

    return DocumentPreviewResponse(
        document=DocumentResponse.from_orm(doc),
        chunks=[DocumentChunkResponse.from_orm(c) for c in chunks],
        total_chunks=doc.chunk_count,
    )
