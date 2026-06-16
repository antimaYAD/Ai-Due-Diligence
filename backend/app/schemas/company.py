from datetime import datetime
from pydantic import BaseModel


class CompanyCreate(BaseModel):
    name: str
    ticker: str | None = None
    industry: str | None = None


class CompanyOut(BaseModel):
    id: str
    name: str
    ticker: str | None
    industry: str | None
    created_at: datetime

    class Config:
        from_attributes = True
