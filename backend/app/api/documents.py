import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentOut
from app.services.storage import store_document, delete_document as storage_delete
from app.worker.tasks import process_document_local, process_document

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_TYPES = {"application/pdf"}
MAX_FILE_SIZE = 50 * 1024 * 1024


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    company_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 50 MB limit")

    doc_id = str(uuid.uuid4())
    safe_name = file.filename or "unknown.pdf"

    file_url, storage_ref = store_document(file_bytes, safe_name, doc_id, company_id)

    document = Document(
        id=doc_id,
        company_id=company_id,
        file_name=safe_name,
        file_url=file_url,
        file_size=len(file_bytes),
        status="pending",
        uploaded_by=current_user.id,
        created_at=datetime.utcnow(),
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    if settings.STORAGE_BACKEND == "s3":
        process_document.delay(document_id=doc_id, s3_key=storage_ref)
    else:
        process_document_local.delay(document_id=doc_id, file_path=storage_ref)

    return document


@router.get("/{document_id}/download")
def download_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if settings.STORAGE_BACKEND == "s3":
        from app.services.s3_service import s3_service
        presigned_url = s3_service.get_presigned_url(doc.file_url)
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=presigned_url)
    else:
        file_path = Path(doc.file_url)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")
        return FileResponse(
            path=str(file_path),
            filename=doc.file_name,
            media_type="application/pdf",
        )


@router.get("/", response_model=list[DocumentOut])
def list_documents(
    company_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Document)
    if company_id:
        query = query.filter(Document.company_id == company_id)
    return query.order_by(Document.created_at.desc()).all()


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    storage_ref = doc.file_url
    db.delete(doc)
    db.commit()
    try:
        storage_delete(storage_ref)
    except Exception:
        pass
