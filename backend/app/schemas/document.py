from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, HttpUrl, Field


class URLImportRequest(BaseModel):
    url: str = Field(..., description="Valid HTTP or HTTPS web URL to scrape and ingest")
    title: Optional[str] = Field(None, description="Optional custom document title")


class DocumentResponse(BaseModel):
    id: str
    title: str
    file_name: str
    file_type: str
    source_url: Optional[str] = None
    file_size_bytes: int
    summary: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    chunk_count: int
    word_count: int
    metadata_json: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    content: str
    word_count: int
    page_number: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentStatusResponse(BaseModel):
    id: str
    status: str
    progress_percent: int
    chunk_count: int
    error_message: Optional[str] = None


class DocumentPreviewResponse(BaseModel):
    document: DocumentResponse
    chunks: List[DocumentChunkResponse]
    total_chunks: int
