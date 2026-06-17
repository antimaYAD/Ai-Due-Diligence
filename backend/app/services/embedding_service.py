from openai import OpenAI

from app.core.config import settings

_client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_embedding(text: str) -> list[float]:
    result = _client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=text,
    )
    return result.data[0].embedding


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    result = _client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in result.data]
