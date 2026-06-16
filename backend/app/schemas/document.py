from datetime import datetime
from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    company_id: str
    file_name: str
    file_url: str | None
    file_size: int | None
    page_count: int | None
    status: str
    created_at: datetime
    processed_at: datetime | None

    class Config:
        from_attributes = True


class DocumentChunkOut(BaseModel):
    id: str
    document_id: str
    content: str
    page_number: int | None
    chunk_index: int | None

    class Config:
        from_attributes = True
