import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.session import Base


class EvaluationDataset(Base):
    __tablename__ = "evaluation_datasets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    sample_count = Column(Integer, default=0, nullable=False)
    samples_json = Column(Text, nullable=False)  # JSON list of test queries, ground truths, doc IDs
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    runs = relationship("EvaluationRun", back_populates="dataset", cascade="all, delete-orphan")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("evaluation_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="completed", nullable=False)  # running, completed, failed
    recall_at_k = Column(Float, default=0.0, nullable=False)
    mrr = Column(Float, default=0.0, nullable=False)
    relevance_score = Column(Float, default=0.0, nullable=False)
    citation_precision = Column(Float, default=0.0, nullable=False)
    groundedness_score = Column(Float, default=0.0, nullable=False)
    avg_latency_ms = Column(Float, default=0.0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    estimated_cost_usd = Column(Float, default=0.0, nullable=False)
    results_json = Column(Text, nullable=True)  # Detailed per-query breakdown
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    dataset = relationship("EvaluationDataset", back_populates="runs")

    __table_args__ = (
        Index("idx_eval_runs_user", "user_id", "created_at"),
    )


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    request_type = Column(String(50), nullable=False)  # chat, embedding, report, agent
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    estimated_cost = Column(Float, default=0.0, nullable=False)
    model_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="usage_records")

    __table_args__ = (
        Index("idx_usage_user_created", "user_id", "created_at"),
    )
