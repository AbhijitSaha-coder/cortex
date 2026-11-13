import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.session import Base


class AgentToolExecution(Base):
    __tablename__ = "agent_tool_executions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True, index=True)
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False)
    tool_input_json = Column(Text, nullable=True)
    tool_output_json = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="success", nullable=False)  # success, error, timeout
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    conversation = relationship("Conversation", back_populates="agent_executions")
    message = relationship("Message", back_populates="agent_executions")

    __table_args__ = (
        Index("idx_tool_exec_user", "user_id", "created_at"),
    )

