import uuid
from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ticker: Mapped[str] = mapped_column(String(20), nullable=True, index=True)
    industry: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    documents: Mapped[list["Document"]] = relationship("Document", back_populates="company")
    analyses: Mapped[list["Analysis"]] = relationship("Analysis", back_populates="company")
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="company")
    chat_messages: Mapped[list["ChatMessage"]] = relationship("ChatMessage", back_populates="company")
