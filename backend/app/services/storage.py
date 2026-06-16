"""
Storage abstraction — swap STORAGE_BACKEND env var to switch between local disk
and AWS S3 without touching any other code.
"""
from pathlib import Path

from app.core.config import settings


def _upload_local(file_bytes: bytes, filename: str, doc_id: str) -> tuple[str, str]:
    upload_dir = Path(settings.LOCAL_UPLOAD_DIR)
    upload_dir.mkdir(exist_ok=True)
    local_path = upload_dir / f"{doc_id}_{filename}"
    local_path.write_bytes(file_bytes)
    return str(local_path), str(local_path)


def _upload_s3(file_bytes: bytes, filename: str, doc_id: str, company_id: str) -> tuple[str, str]:
    from app.services.s3_service import s3_service

    s3_key = f"documents/{company_id}/{doc_id}/{filename}"
    file_url = s3_service.upload_file(
        file_bytes=file_bytes,
        key=s3_key,
        content_type="application/pdf",
    )
    return file_url, s3_key


def store_document(
    file_bytes: bytes,
    filename: str,
    doc_id: str,
    company_id: str,
) -> tuple[str, str]:
    """
    Returns (file_url, storage_ref) where:
      - file_url   : URL or local path stored in the DB
      - storage_ref: local path (local mode) or S3 key (s3 mode) passed to tasks
    """
    if settings.STORAGE_BACKEND == "s3":
        return _upload_s3(file_bytes, filename, doc_id, company_id)
    return _upload_local(file_bytes, filename, doc_id)


def delete_document(storage_ref: str) -> None:
    """Delete from whichever backend is active."""
    if settings.STORAGE_BACKEND == "s3":
        from app.services.s3_service import s3_service
        s3_service.delete_file(storage_ref)
    else:
        path = Path(storage_ref)
        if path.exists():
            path.unlink()
