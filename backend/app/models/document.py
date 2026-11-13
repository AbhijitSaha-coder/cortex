import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, BigInteger, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.vector_type import VectorType
from app.core.config import settings


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=True)
    file_type = Column(String(50), nullable=False)  # pdf, txt, md, url
    source_url = Column(String(2000), nullable=True)
    file_size_bytes = Column(BigInteger, default=0, nullable=False)
    content_hash = Column(String(64), nullable=True, index=True)
    summary = Column(Text, nullable=True)
    status = Column(String(50), default="queued", nullable=False, index=True)  # queued, processing, completed, failed
    error_message = Column(Text, nullable=True)
    chunk_count = Column(Integer, default=0, nullable=False)
    word_count = Column(Integer, default=0, nullable=False)
    metadata_json = Column(Text, nullable=True)  # JSON-encoded extra metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan", order_by="DocumentChunk.chunk_index")
    ingestion_jobs = relationship("IngestionJob", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_docs_user_created", "user_id", "created_at"),
        Index("idx_docs_user_hash", "user_id", "content_hash"),
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    word_count = Column(Integer, default=0, nullable=False)
    page_number = Column(Integer, nullable=True)
    metadata_json = Column(Text, nullable=True)
    embedding = Column(VectorType(settings.EMBEDDING_DIMENSION), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks")
    citations = relationship("MessageCitation", back_populates="chunk")

    __table_args__ = (
        Index("idx_chunks_user_doc", "user_id", "document_id"),
        Index("idx_chunks_doc_index", "document_id", "chunk_index"),
    )


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="queued", nullable=False)  # queued, processing, completed, failed
    progress_percent = Column(Integer, default=0, nullable=False)
    error_log = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("Document", back_populates="ingestion_jobs")
