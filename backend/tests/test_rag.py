"""Tests for chunking and retrieval, using a deterministic fake embedder."""

import numpy as np

import app.rag as rag

# Tiny bag-of-words "embedder" so similarity is predictable in tests.
_VOCAB = ["python", "france", "music", "nyc", "data"]


def _fake_embed(texts):
    vectors = []
    for text in texts:
        lowered = text.lower()
        vectors.append([float(lowered.count(word)) for word in _VOCAB])
    return vectors


def test_chunk_text_overlaps():
    text = " ".join(f"w{i}" for i in range(25))
    chunks = rag.chunk_text(text, chunk_size=10, overlap=2)

    assert len(chunks) > 1
    # Overlap: the tail of chunk 0 reappears at the head of chunk 1.
    assert chunks[0].split()[-2:] == chunks[1].split()[:2]


def test_chunk_text_empty():
    assert rag.chunk_text("", chunk_size=10, overlap=2) == []


def test_retrieve_ranks_by_similarity(monkeypatch):
    chunks = [
        "I write python and build data pipelines",
        "I love france and french cuisine",
        "I play music on weekends",
    ]
    vectors = _fake_embed(chunks)
    monkeypatch.setattr(rag, "_load_index", lambda: (chunks, np.array(vectors, dtype=float)))
    monkeypatch.setattr(rag.embeddings, "embed_texts", _fake_embed)

    top = rag.retrieve("tell me about your python and data work", k=1)
    assert top == [chunks[0]]

    top_music = rag.retrieve("do you enjoy music", k=1)
    assert top_music == [chunks[2]]


def test_retrieve_without_index_returns_empty(monkeypatch):
    monkeypatch.setattr(rag, "_load_index", lambda: ([], None))
    assert rag.retrieve("anything") == []


def test_build_index_persists_chunks(monkeypatch, tmp_path):
    monkeypatch.setattr(rag.sources, "load_linkedin_text", lambda: "alpha beta gamma delta")
    monkeypatch.setattr(rag.sources, "clear_cache", lambda: None)
    monkeypatch.setattr(rag.embeddings, "embed_texts", _fake_embed)
    index_file = tmp_path / "rag_index.json"
    monkeypatch.setattr(rag, "_index_path", lambda: index_file)

    count = rag.build_index()

    assert count == 1  # short text -> single chunk
    assert index_file.exists()


def test_ensure_index_skips_when_disabled(monkeypatch, tmp_path):
    settings = rag.get_settings()
    monkeypatch.setattr(settings, "auto_build_rag_index", False)
    index_file = tmp_path / "rag_index.json"
    monkeypatch.setattr(rag, "_index_path", lambda: index_file)

    def _should_not_be_called():
        raise AssertionError("build_index should not run when auto-build is disabled")

    monkeypatch.setattr(rag, "build_index", _should_not_be_called)

    rag.ensure_index()

    assert not index_file.exists()


def test_ensure_index_skips_when_already_built(monkeypatch, tmp_path):
    settings = rag.get_settings()
    monkeypatch.setattr(settings, "auto_build_rag_index", True)
    index_file = tmp_path / "rag_index.json"
    index_file.write_text("{}")
    monkeypatch.setattr(rag, "_index_path", lambda: index_file)

    def _should_not_be_called():
        raise AssertionError("build_index should not re-run when the index already exists")

    monkeypatch.setattr(rag, "build_index", _should_not_be_called)

    rag.ensure_index()


def test_ensure_index_builds_when_missing_and_enabled(monkeypatch, tmp_path):
    settings = rag.get_settings()
    monkeypatch.setattr(settings, "auto_build_rag_index", True)
    index_file = tmp_path / "rag_index.json"
    monkeypatch.setattr(rag, "_index_path", lambda: index_file)
    calls = []
    monkeypatch.setattr(rag, "build_index", lambda: calls.append(1) or 3)

    rag.ensure_index()

    assert calls == [1]


def test_ensure_index_failure_does_not_raise(monkeypatch, tmp_path):
    settings = rag.get_settings()
    monkeypatch.setattr(settings, "auto_build_rag_index", True)
    index_file = tmp_path / "rag_index.json"
    monkeypatch.setattr(rag, "_index_path", lambda: index_file)

    def _boom():
        raise RuntimeError("vertex unavailable")

    monkeypatch.setattr(rag, "build_index", _boom)

    rag.ensure_index()  # must not raise — startup shouldn't crash on this
