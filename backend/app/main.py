from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base

import app.models  # noqa: F401 — ensure all models are registered

from app.api.auth import router as auth_router
from app.api.companies import router as companies_router
from app.api.documents import router as documents_router
from app.api.analysis import router as analysis_router
from app.api.chat import router as chat_router

try:
    Base.metadata.create_all(bind=engine)
except Exception:
    pass

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise AI platform for financial due diligence — RAG + LangGraph agents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(companies_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.APP_NAME}
