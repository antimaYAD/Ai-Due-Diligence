from typing import Any

from openai import OpenAI

from app.core.config import settings
from app.core.database import SessionLocal

_client = OpenAI(api_key=settings.OPENAI_API_KEY)


def retrieve_chunks(
    query: str,
    company_id: str | None = None,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Retrieve document chunks via ORM (works with SQLite and PostgreSQL)."""
    from app.models.document import DocumentChunk, Document

    db = SessionLocal()
    try:
        q = (
            db.query(DocumentChunk, Document.file_name, Document.company_id)
            .join(Document, DocumentChunk.document_id == Document.id)
        )
        if company_id:
            q = q.filter(Document.company_id == company_id)
        rows = q.order_by(DocumentChunk.created_at.desc()).limit(top_k).all()

        return [
            {
                "id": str(chunk.id),
                "content": chunk.content,
                "page_number": chunk.page_number,
                "document_name": file_name,
                "company_id": str(cid),
            }
            for chunk, file_name, cid in rows
        ]
    finally:
        db.close()


def rag_query(
    question: str,
    company_id: str | None = None,
    top_k: int = 10,
) -> dict[str, Any]:
    """Full RAG flow: retrieve → augment → generate answer with citations."""
    chunks = retrieve_chunks(query=question, company_id=company_id, top_k=top_k)

    if not chunks:
        return {
            "answer": "No relevant documents found. Please upload company filings first.",
            "sources": [],
        }

    context = "\n\n---\n\n".join(
        f"[{c['document_name']} | Page {c['page_number']}]\n{c['content']}"
        for c in chunks
    )

    system_prompt = (
        "You are an AI Due Diligence Copilot. Answer the user's question based ONLY on the "
        "provided document excerpts. Be precise, cite sources by document name and page number. "
        "If the answer is not in the documents, say so clearly."
    )

    prompt = (
        f"{system_prompt}\n\n"
        f"Question: {question}\n\n"
        f"Document Excerpts:\n{context}"
    )
    response = _client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )
    answer = response.choices[0].message.content or ""

    sources = [
        {
            "document_name": c["document_name"],
            "page_number": c["page_number"],
        }
        for c in chunks[:5]
    ]

    return {"answer": answer, "sources": sources}
