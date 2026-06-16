import io
from typing import Generator

from pypdf import PdfReader


def extract_text_from_pdf(file_bytes: bytes) -> list[dict]:
    """Extract text per page from a PDF byte stream."""
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append({"page_number": i + 1, "text": text.strip()})
    return pages


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks by word boundary."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def process_document_pages(pages: list[dict]) -> Generator[dict, None, None]:
    """Yield chunk dicts with page_number and chunk_index from extracted pages."""
    for page in pages:
        page_number = page["page_number"]
        text = page["text"]
        if not text:
            continue
        chunks = chunk_text(text)
        for idx, chunk in enumerate(chunks):
            yield {
                "content": chunk,
                "page_number": page_number,
                "chunk_index": idx,
            }
