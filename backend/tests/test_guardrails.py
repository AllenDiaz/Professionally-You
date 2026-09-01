"""Tests for the input guardrail and output evaluator, using a fake Vertex client."""

import json

import app.guardrails as guardrails


class _FakeClient:
    def __init__(self, content):
        self._content = content
        self.calls = []

    @property
    def chat(self):
        from types import SimpleNamespace

        return SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        from types import SimpleNamespace

        self.calls.append(kwargs)
        message = SimpleNamespace(content=self._content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_check_input_handles_markdown_fenced_json(monkeypatch):
    fenced = "```json\n" + json.dumps({"allowed": False, "reason": "off-topic"}) + "\n```"
    monkeypatch.setattr(guardrails, "vertex_client", lambda: _FakeClient(fenced))

    allowed, reason = guardrails.check_input("...")

    assert allowed is False
    assert reason == "off-topic"


def test_parse_json_object_extracts_from_surrounding_prose():
    text = 'Sure, here you go: {"allowed": true, "reason": "fine"} — hope that helps!'

    assert guardrails._parse_json_object(text) == {"allowed": True, "reason": "fine"}


def test_parse_json_object_empty_text_returns_empty_dict():
    assert guardrails._parse_json_object(None) == {}
    assert guardrails._parse_json_object("") == {}


def test_check_input_allows(monkeypatch):
    monkeypatch.setattr(
        guardrails, "vertex_client", lambda: _FakeClient(json.dumps({"allowed": True, "reason": ""}))
    )
    allowed, reason = guardrails.check_input("tell me about your career")
    assert allowed is True


def test_check_input_blocks(monkeypatch):
    monkeypatch.setattr(
        guardrails,
        "vertex_client",
        lambda: _FakeClient(json.dumps({"allowed": False, "reason": "abusive"})),
    )
    allowed, reason = guardrails.check_input("...")
    assert allowed is False
    assert reason == "abusive"


def test_check_input_fails_open_on_error(monkeypatch):
    def _boom():
        raise RuntimeError("network down")

    monkeypatch.setattr(guardrails, "vertex_client", _boom)
    allowed, reason = guardrails.check_input("hello")
    assert allowed is True


def test_check_input_disabled_via_settings(monkeypatch):
    settings = guardrails.get_settings()
    monkeypatch.setattr(settings, "enable_guardrails", False)

    def _should_not_be_called():
        raise AssertionError("vertex_client should not be called when disabled")

    monkeypatch.setattr(guardrails, "vertex_client", _should_not_be_called)

    allowed, reason = guardrails.check_input("anything")
    assert allowed is True


def test_evaluate_reply_accepts(monkeypatch):
    monkeypatch.setattr(
        guardrails,
        "vertex_client",
        lambda: _FakeClient(json.dumps({"acceptable": True, "feedback": ""})),
    )
    acceptable, feedback = guardrails.evaluate_reply("Name", "sys", "msg", "draft")
    assert acceptable is True


def test_evaluate_reply_rejects(monkeypatch):
    monkeypatch.setattr(
        guardrails,
        "vertex_client",
        lambda: _FakeClient(json.dumps({"acceptable": False, "feedback": "off persona"})),
    )
    acceptable, feedback = guardrails.evaluate_reply("Name", "sys", "msg", "draft")
    assert acceptable is False
    assert feedback == "off persona"


def test_evaluate_reply_disabled_via_settings(monkeypatch):
    settings = guardrails.get_settings()
    monkeypatch.setattr(settings, "enable_evaluator", False)

    def _should_not_be_called():
        raise AssertionError("vertex_client should not be called when disabled")

    monkeypatch.setattr(guardrails, "vertex_client", _should_not_be_called)

    acceptable, feedback = guardrails.evaluate_reply("Name", "sys", "msg", "draft")
    assert acceptable is True
