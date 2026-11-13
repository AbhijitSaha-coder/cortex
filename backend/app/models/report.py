import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.session import Base


class ResearchReport(Base):
    __tablename__ = "research_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    research_question = Column(Text, nullable=False)
    executive_summary = Column(Text, nullable=True)
    main_findings = Column(Text, nullable=True)
    detailed_analysis = Column(Text, nullable=True)
    contradictory_findings = Column(Text, nullable=True)
    limitations = Column(Text, nullable=True)
    unanswered_questions = Column(Text, nullable=True)
    conclusion = Column(Text, nullable=True)
    citations_json = Column(Text, nullable=True)  # JSON-encoded citations list
    markdown_content = Column(Text, nullable=False)
    status = Column(String(50), default="completed", nullable=False)  # generating, completed, failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="reports")

    __table_args__ = (
        Index("idx_reports_user_created", "user_id", "created_at"),
    )
