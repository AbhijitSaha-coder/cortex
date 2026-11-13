from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class ReportGenerateRequest(BaseModel):
    research_question: str = Field(..., min_length=5, description="Primary research objective or question")
    title: Optional[str] = Field(None, max_length=200, description="Optional title for the report")
    focus_areas: Optional[List[str]] = Field(None, description="Key topics, aspects or angles to examine")
    document_ids: Optional[List[str]] = Field(None, description="Optional document filter")


class ReportResponse(BaseModel):
    id: str
    title: str
    research_question: str
    executive_summary: Optional[str] = None
    main_findings: Optional[str] = None
    detailed_analysis: Optional[str] = None
    contradictory_findings: Optional[str] = None
    limitations: Optional[str] = None
    unanswered_questions: Optional[str] = None
    conclusion: Optional[str] = None
    markdown_content: str
    citations: Optional[List[Dict[str, Any]]] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportExportResponse(BaseModel):
    id: str
    title: str
    markdown_content: str
    file_name: str

