"""Tests for tool dispatch — including the security fix for unknown tools."""

import json
from types import SimpleNamespace

import app.tools as tools


def _tool_call(name, args, call_id="c1"):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=json.dumps(args)),
    )


def test_known_tool_is_dispatched(monkeypatch):
    pushed = []
    monkeypatch.setattr("app.pushover.push", lambda text: pushed.append(text))

    results = tools.handle_tool_calls(
        [_tool_call("record_unknown_question", {"question": "why blue?"})]
    )

    assert results[0]["role"] == "tool"
    assert results[0]["tool_call_id"] == "c1"
    assert json.loads(results[0]["content"]) == {"recorded": "ok"}
    assert pushed and "why blue?" in pushed[0]


def test_record_user_details_dispatch(monkeypatch):
    pushed = []
    monkeypatch.setattr("app.pushover.push", lambda text: pushed.append(text))

    results = tools.handle_tool_calls(
        [_tool_call("record_user_details", {"email": "a@b.com", "name": "Ada"})]
    )

    assert json.loads(results[0]["content"]) == {"recorded": "ok"}
    assert "a@b.com" in pushed[0]


def test_unknown_tool_is_rejected_safely():
    # The old globals()[tool_name] dispatch would try to resolve arbitrary names.
    # The explicit table must reject anything not whitelisted.
    results = tools.handle_tool_calls([_tool_call("os.system", {"question": "x"})])

    payload = json.loads(results[0]["content"])
    assert "error" in payload
    assert "os.system" in payload["error"]
