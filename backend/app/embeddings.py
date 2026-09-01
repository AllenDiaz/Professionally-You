"""Text embeddings via Vertex AI's native embeddings API.

Vertex's OpenAI-compatible endpoint (used for chat in ``vertex.py``) rejects
embedding models outright ("OpenMaaS model ... not supported"), regardless of
model name or ``encoding_format`` — that compat layer only covers generative
models. This calls Vertex's native ``:predict`` REST endpoint instead, reusing
the same ADC token as the chat client. Isolated behind a single function so
the RAG layer never talks to Vertex directly, and tests can substitute a
deterministic fake embedder.
"""

import requests

from .config import get_settings
from .vertex import get_access_token


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return one embedding vector per input string."""
    if not texts:
        return []
    settings = get_settings()
    url = (
        f"https://{settings.gcp_location}-aiplatform.googleapis.com/v1"
        f"/projects/{settings.gcp_project}/locations/{settings.gcp_location}"
        f"/publishers/google/models/{settings.embedding_model}:predict"
    )
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {get_access_token()}"},
        json={"instances": [{"content": text} for text in texts]},
        timeout=30,
    )
    response.raise_for_status()
    predictions = response.json()["predictions"]
    return [p["embeddings"]["values"] for p in predictions]
