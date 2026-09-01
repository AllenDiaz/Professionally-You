"""Tests for the streaming chat loop, using a fake streaming Vertex client."""

import json
from types import SimpleNamespace

import app.stream as stream_module


class _Delta:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class _Choice:
    def __init__(self, delta, finish_reason=None):
        self.delta = delta
        self.finish_reason = finish_reason


class _Chunk:
    def __init__(self, choice):
        self.choices = [choice]


class _ToolCallDelta:
    def __init__(self, index, id=None, name=None, arguments=None):
        self.index = index
        self.id = id
        self.function = SimpleNamespace(name=name, arguments=arguments)


class _FakeStreamingCompletions:
    def __init__(self, streams, final_response=None):
        self._streams = list(streams)
        self.calls = []
        self._final_response = final_response

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs.get("stream"):
            return self._streams.pop(0)
        return self._final_response


class _FakeClient:
    def __init__(self, streams, final_response=None):
        self.chat = SimpleNamespace(
            completions=_FakeStreamingCompletions(streams, final_response)
        )


def _text_stream(text):
    chunks = [_Chunk(_Choice(_Delta(content=ch))) for ch in text]
    chunks.append(_Chunk(_Choice(_Delta(), finish_reason="stop")))
    return chunks


def _tool_call_stream(name, arguments, call_id="call_1"):
    return [
        _Chunk(_Choice(_Delta(tool_calls=[_ToolCallDelta(0, id=call_id, name=name, arguments="")]))),
        _Chunk(
            _Choice(
                _Delta(tool_calls=[_ToolCallDelta(0, arguments=arguments)]),
                finish_reason="tool_calls",
            )
        ),
    ]


def _patch(monkeypatch, fake):
    monkeypatch.setattr(stream_module, "vertex_client", lambda: fake)
    monkeypatch.setattr(stream_module, "build_system_prompt", lambda *a, **k: "SYS")
    monkeypatch.setattr(stream_module.guardrails, "check_input", lambda msg: (True, ""))


def test_streams_plain_text(monkeypatch):
    fake = _FakeClient([_text_stream("Hi!")])
    _patch(monkeypatch, fake)

    chunks = list(stream_module.stream_chat("hello"))

    assert "".join(chunks) == "Hi!"


def test_input_guardrail_blocks_before_streaming(monkeypatch):
    fake = _FakeClient([])
    _patch(monkeypatch, fake)
    monkeypatch.setattr(stream_module.guardrails, "check_input", lambda msg: (False, "no"))

    chunks = list(stream_module.stream_chat("bad"))

    assert chunks == [stream_module.guardrails.GUARDRAIL_REDIRECT_MESSAGE]
    assert fake.chat.completions.calls == []


def test_streams_after_tool_call(monkeypatch):
    fake = _FakeClient(
        [
            _tool_call_stream("record_unknown_question", json.dumps({"question": "q?"})),
            _text_stream("Recorded!"),
        ]
    )
    _patch(monkeypatch, fake)
    monkeypatch.setattr("app.pushover.push", lambda text: None)

    chunks = list(stream_module.stream_chat("obscure question"))

    assert "".join(chunks) == "Recorded!"
    assert len(fake.chat.completions.calls) == 2
    followup_messages = fake.chat.completions.calls[1]["messages"]
    assert any(m.get("role") == "tool" for m in followup_messages)


def test_stream_tool_loop_is_bounded(monkeypatch):
    settings = stream_module.get_settings()
    cap = settings.max_tool_iterations
    streams = [
        _tool_call_stream("record_unknown_question", json.dumps({"question": "q"}))
        for _ in range(cap)
    ]
    final_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="forced answer"))]
    )
    fake = _FakeClient(streams, final_response=final_response)
    _patch(monkeypatch, fake)
    monkeypatch.setattr("app.pushover.push", lambda text: None)

    chunks = list(stream_module.stream_chat("loop forever"))

    assert "".join(chunks) == "forced answer"
    assert len(fake.chat.completions.calls) == cap + 1
