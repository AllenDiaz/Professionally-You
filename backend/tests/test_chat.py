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
    monkeypatch.setattr(chat_module, "build_system_prompt", lambda *args, **kwargs: "SYS")
    monkeypatch.setattr(chat_module.guardrails, "check_input", lambda msg: (True, ""))
    monkeypatch.setattr(chat_module.guardrails, "evaluate_reply", lambda *a, **k: (True, ""))


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


def test_input_guardrail_blocks_before_any_model_call(monkeypatch):
    fake = _FakeClient([])
    monkeypatch.setattr(chat_module, "vertex_client", lambda: fake)
    monkeypatch.setattr(chat_module, "build_system_prompt", lambda *a, **k: "SYS")
    monkeypatch.setattr(chat_module.guardrails, "check_input", lambda msg: (False, "abusive"))

    reply = chat_module.run_chat("bad message")

    assert reply == chat_module.guardrails.GUARDRAIL_REDIRECT_MESSAGE
    assert fake.chat.completions.calls == []


def test_evaluator_rejection_triggers_one_retry(monkeypatch):
    fake = _FakeClient([_text("first draft"), _text("second draft")])
    _patch_common(monkeypatch, fake)

    calls = {"n": 0}

    def _evaluate(name, system_prompt, user_message, draft_reply):
        calls["n"] += 1
        return (calls["n"] > 1, "needs fix")

    monkeypatch.setattr(chat_module.guardrails, "evaluate_reply", _evaluate)

    reply = chat_module.run_chat("question")

    assert reply == "second draft"
    assert len(fake.chat.completions.calls) == 2
    retry_messages = fake.chat.completions.calls[1]["messages"]
    assert any(
        isinstance(m, dict) and "needs fix" in m.get("content", "") for m in retry_messages
    )
