from google import genai

from app.core.config import settings

_client = genai.Client(api_key=settings.GEMINI_API_KEY)


def generate_embedding(text: str) -> list[float]:
    result = _client.models.embed_content(
        model=settings.EMBEDDING_MODEL,
        contents=text,
    )
    return result.embeddings[0].values


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    return [generate_embedding(t) for t in texts]
