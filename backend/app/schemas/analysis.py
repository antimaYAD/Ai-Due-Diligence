from datetime import datetime
from typing import Any
from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    company_id: str
    analysis_type: str


class AnalysisOut(BaseModel):
    id: str
    company_id: str
    analysis_type: str
    status: str
    result: dict[str, Any] | None
    summary: str | None
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class ReportOut(BaseModel):
    id: str
    company_id: str
    title: str
    report_type: str | None
    file_url: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    question: str
    company_id: str | None = None


class SourceRef(BaseModel):
    document_name: str
    page_number: int | None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceRef]
    message_id: str


class ChatMessageOut(BaseModel):
    id: str
    role: str
    content: str
    sources: list | None
    created_at: datetime

    class Config:
        from_attributes = True
