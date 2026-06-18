import uuid
from datetime import datetime
from pathlib import Path

from app.worker.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.document import Document, DocumentChunk
from app.services.document_processor import extract_text_from_pdf, process_document_pages


@celery_app.task(bind=True, name="process_document_local", max_retries=3)
def process_document_local(self, document_id: str, file_path: str):
    """Process a PDF from local disk — no S3 or embeddings required."""
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return {"error": f"Document {document_id} not found"}

        document.status = "processing"
        db.commit()

        file_bytes = Path(file_path).read_bytes()
        pages = extract_text_from_pdf(file_bytes)
        document.page_count = len(pages)
        db.commit()

        chunk_dicts = list(process_document_pages(pages))

        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        for chunk_data in chunk_dicts:
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=document_id,
                content=chunk_data["content"],
                page_number=chunk_data["page_number"],
                chunk_index=chunk_data["chunk_index"],
            )
            db.add(chunk)

        document.status = "processed"
        document.processed_at = datetime.utcnow()
        db.commit()
        return {"document_id": document_id, "chunks": len(chunk_dicts), "status": "processed"}

    except Exception as exc:
        db.rollback()
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "error"
            db.commit()
        raise self.retry(exc=exc, countdown=5, max_retries=1)
    finally:
        db.close()


@celery_app.task(bind=True, name="process_document", max_retries=3)
def process_document(self, document_id: str, s3_key: str):
    """
    Full document processing pipeline:
    1. Download PDF from S3
    2. Extract text per page
    3. Chunk text
    4. Generate embeddings in batches
    5. Store chunks + embedding IDs in PostgreSQL
    6. Update document status
    """
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return {"error": f"Document {document_id} not found"}

        document.status = "processing"
        db.commit()

        file_bytes = _download_from_s3(s3_key)

        pages = extract_text_from_pdf(file_bytes)
        document.page_count = len(pages)
        db.commit()

        chunk_dicts = list(process_document_pages(pages))

        batch_size = 20
        all_embeddings = []
        for i in range(0, len(chunk_dicts), batch_size):
            batch_texts = [c["content"] for c in chunk_dicts[i : i + batch_size]]
            embeddings = generate_embeddings_batch(batch_texts)
            all_embeddings.extend(embeddings)

        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        for chunk_data, embedding in zip(chunk_dicts, all_embeddings):
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=document_id,
                content=chunk_data["content"],
                page_number=chunk_data["page_number"],
                chunk_index=chunk_data["chunk_index"],
                embedding_id=str(uuid.uuid4()),
            )
            db.add(chunk)

        document.status = "processed"
        document.processed_at = datetime.utcnow()
        db.commit()

        return {"document_id": document_id, "chunks": len(chunk_dicts), "status": "processed"}

    except Exception as exc:
        db.rollback()
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = "error"
            db.commit()
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()


@celery_app.task(bind=True, name="run_analysis", max_retries=2)
def run_analysis(self, analysis_id: str):
    """Dispatch LangGraph agent pipeline for a given analysis."""
    from app.models.analysis import Analysis, Report
    from app.models.company import Company
    from app.ai.orchestrator import run_agent_pipeline

    db = SessionLocal()
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            return {"error": "Analysis not found"}

        analysis.status = "running"
        db.commit()

        result = run_agent_pipeline(
            company_id=analysis.company_id,
            analysis_type=analysis.analysis_type,
            db=db,
        )

        analysis.result = result.get("data", {})
        analysis.summary = result.get("summary", "")
        analysis.status = "completed"
        analysis.completed_at = datetime.utcnow()

        company = db.query(Company).filter(Company.id == analysis.company_id).first()
        company_name = company.name if company else "Company"
        report = Report(
            id=str(uuid.uuid4()),
            company_id=analysis.company_id,
            title=f"{company_name} — {analysis.analysis_type.title()} Due Diligence Report",
            report_type=analysis.analysis_type,
            status="ready",
            created_at=datetime.utcnow(),
        )
        db.add(report)
        db.commit()

        return {"analysis_id": analysis_id, "status": "completed"}

    except Exception as exc:
        db.rollback()
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis:
            analysis.status = "error"
            db.commit()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


def _download_from_s3(s3_key: str) -> bytes:
    import boto3
    from app.core.config import settings

    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )
    response = s3.get_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
    return response["Body"].read()
