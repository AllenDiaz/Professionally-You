"""Retrieval-augmented generation over the LinkedIn profile.

Replaces the original approach of dumping the entire LinkedIn PDF into the system
prompt on every turn. Instead the profile text is chunked, embedded once, and
persisted to a small on-disk index; at chat time only the top-k chunks relevant
to the user's message are retrieved.

The store is a plain JSON file with cosine similarity over numpy — no external
vector database required for Phase 2. (Phase 3 can move this into Postgres/pgvector.)
"""

import json
import logging
from pathlib import Path

import numpy as np

from . import embeddings, sources
from .config import get_settings

logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping word windows."""
    words = text.split()
    if not words:
        return []
    step = max(1, chunk_size - overlap)
    chunks: list[str] = []
    for start in range(0, len(words), step):
        window = words[start : start + chunk_size]
        chunk = " ".join(window).strip()
        if chunk:
            chunks.append(chunk)
        if start + chunk_size >= len(words):
            break
    return chunks


def _index_path() -> Path:
    return get_settings().data_dir / "rag_index.json"


def _save_index(chunks: list[str], vectors: list[list[float]]) -> None:
    path = _index_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"chunks": chunks, "vectors": vectors}), encoding="utf-8")


def _load_index() -> tuple[list[str], np.ndarray | None]:
    path = _index_path()
    if not path.exists():
        return [], None
    data = json.loads(path.read_text(encoding="utf-8"))
    chunks = data.get("chunks", [])
    vectors = data.get("vectors", [])
    matrix = np.array(vectors, dtype=float) if vectors else None
    return chunks, matrix


def build_index() -> int:
    """(Re)build the RAG index from the LinkedIn source. Returns the chunk count."""
    settings = get_settings()
    sources.clear_cache()
    text = sources.load_linkedin_text()
    chunks = chunk_text(text, settings.rag_chunk_size, settings.rag_chunk_overlap)
    if not chunks:
        _save_index([], [])
        return 0
    vectors = embeddings.embed_texts(chunks)
    _save_index(chunks, vectors)
    return len(chunks)


def ensure_index() -> None:
    """Build the RAG index on first boot if it doesn't exist yet.

    Without this, a freshly deployed container has zero LinkedIn grounding
    until someone remembers to call POST /api/profile/reindex — the model
    just fills the gap with a plausible-sounding but fabricated career.
    """
    settings = get_settings()
    if not settings.auto_build_rag_index:
        return
    if _index_path().exists():
        return
    try:
        count = build_index()
        logger.info("Built initial RAG index: %d chunk(s)", count)
    except Exception:
        logger.exception(
            "Initial RAG index build failed; chat will run without LinkedIn grounding "
            "until POST /api/profile/reindex succeeds"
        )


def retrieve(query: str, k: int | None = None) -> list[str]:
    """Return the k most relevant profile chunks for ``query`` (empty if no index)."""
    settings = get_settings()
    k = k or settings.rag_top_k
    chunks, matrix = _load_index()
    if not chunks or matrix is None or matrix.size == 0:
        return []

    query_vec = np.array(embeddings.embed_texts([query])[0], dtype=float)
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
    matrix_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10)
    scores = matrix_norm @ query_norm
    top = np.argsort(scores)[::-1][:k]
    return [chunks[i] for i in top]
