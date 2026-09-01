"""Tests for the bounded chat loop, using a fake Vertex client (no network)."""

import json
from types import SimpleNamespace

import app.chat as chat_module


class _FakeCompletions:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._responses.pop(0)


class _FakeClient:
    def __init__(self, responses):
        self.chat = SimpleNamespace(completions=_FakeCompletions(responses))


def _text(text):
    message = SimpleNamespace(role="assistant", content=text, tool_calls=None)
    return SimpleNamespace(
        choices=[SimpleNamespace(finish_reason="stop", message=message)]
    )


def _tool(name, args, call_id="call_1"):
    tool_call = SimpleNamespace(
        id=call_id, function=SimpleNamespace(name=name, arguments=json.dumps(args))
    )
    message = SimpleNamespace(role="assistant", content=None, tool_calls=[tool_call])
    return SimpleNamespace(
        choices=[SimpleNamespace(finish_reason="tool_calls", message=message)]
    )


def _patch_common(monkeypatch, fake):
    monkeypatch.setattr(chat_module, "vertex_client", lambda: fake)
    monkeypatch.setattr(chat_module, "build_system_prompt", lambda: "SYS")


def test_returns_plain_text(monkeypatch):
    fake = _FakeClient([_text("Hello!")])
    _patch_common(monkeypatch, fake)

    reply = chat_module.run_chat("hi")

    assert reply == "Hello!"
    # System prompt is injected as the first message.
    assert fake.chat.completions.calls[0]["messages"][0] == {
        "role": "system",
        "content": "SYS",
    }


def test_handles_a_tool_call_then_answers(monkeypatch):
    fake = _FakeClient(
        [
            _tool("record_unknown_question", {"question": "q?"}),
            _text("Recorded, thanks!"),
        ]
    )
    _patch_common(monkeypatch, fake)
    monkeypatch.setattr("app.pushover.push", lambda text: None)

    reply = chat_module.run_chat("some obscure question")

    assert reply == "Recorded, thanks!"
    assert len(fake.chat.completions.calls) == 2


def test_tool_loop_is_bounded(monkeypatch):
    settings = chat_module.get_settings()
    cap = settings.max_tool_iterations
    # Always return tool calls for every bounded iteration, then a final text
    # answer for the forced no-tools call.
    responses = [_tool("record_unknown_question", {"question": "q"}) for _ in range(cap)]
    responses.append(_text("Final forced answer"))
    fake = _FakeClient(responses)
    _patch_common(monkeypatch, fake)
    monkeypatch.setattr("app.pushover.push", lambda text: None)

    reply = chat_module.run_chat("loop forever")

    assert reply == "Final forced answer"
    # cap tool rounds + 1 final no-tools call.
    assert len(fake.chat.completions.calls) == cap + 1
    # The final call must not offer tools.
    assert "tools" not in fake.chat.completions.calls[-1]
