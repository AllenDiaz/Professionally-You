"""Text embeddings via the Vertex AI OpenAI-compatible endpoint.

Isolated behind a single function so the RAG layer never talks to Vertex
directly — and so tests can substitute a deterministic fake embedder.
"""

from .config import get_settings
from .vertex import vertex_client


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return one embedding vector per input string."""
    if not texts:
        return []
    settings = get_settings()
    client = vertex_client()
    response = client.embeddings.create(model=settings.embedding_model, input=texts)
    return [item.embedding for item in response.data]
