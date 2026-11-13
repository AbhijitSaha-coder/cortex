from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    title: Optional[str] = Field("New Research Session", max_length=200)
    model: Optional[str] = "default"


class CitationResponse(BaseModel):
    id: str
    chunk_id: Optional[str] = None
    document_id: str
    document_title: str
    citation_index: int
    excerpt: str
    page_number: Optional[int] = None
    similarity_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    reasoning_content: Optional[str] = None
    tokens_used: int = 0
    created_at: datetime
    citations: List[CitationResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: str
    title: str
    model: str
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[MessageResponse]] = None

    model_config = ConfigDict(from_attributes=True)


class ChatMessageRequest(BaseModel):
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID or null to create new")
    message: str = Field(..., min_length=1, description="User prompt or research question")
    mode: str = Field("rag", description="Execution mode: 'rag' or 'agent'")
    document_ids: Optional[List[str]] = Field(None, description="Scope query to specific documents")
    stream: bool = Field(False, description="Whether to stream the response via SSE")

