"""Tests for the native Vertex embeddings REST call."""

from types import SimpleNamespace

import app.embeddings as embeddings


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_embed_texts_empty_input_skips_request(monkeypatch):
    def _should_not_be_called(*a, **k):
        raise AssertionError("requests.post should not be called for empty input")

    monkeypatch.setattr(embeddings.requests, "post", _should_not_be_called)

    assert embeddings.embed_texts([]) == []


def test_embed_texts_calls_native_predict_endpoint(monkeypatch):
    monkeypatch.setattr(embeddings, "get_access_token", lambda: "fake-token")
    captured = {}

    def _fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return _FakeResponse(
            {
                "predictions": [
                    {"embeddings": {"values": [0.1, 0.2]}},
                    {"embeddings": {"values": [0.3, 0.4]}},
                ]
            }
        )

    monkeypatch.setattr(embeddings.requests, "post", _fake_post)

    result = embeddings.embed_texts(["hello", "world"])

    assert result == [[0.1, 0.2], [0.3, 0.4]]
    assert captured["headers"] == {"Authorization": "Bearer fake-token"}
    assert captured["json"] == {"instances": [{"content": "hello"}, {"content": "world"}]}
    assert ":predict" in captured["url"]
    assert "/publishers/google/models/" in captured["url"]
    # Native endpoint must NOT use the OpenAI-compat "google/" publisher prefix
    # inside the model id itself.
    assert "google/google/" not in captured["url"]
