"""Test that the system prompt is built from the profile + retrieved snippets."""

import app.prompt as prompt_module
from app.profile import Profile, ProfileSection


def test_prompt_uses_profile_and_retrieval(monkeypatch):
    fake_profile = Profile(
        name="Ada Lovelace",
        summary="Pioneering programmer.",
        sections=[ProfileSection(title="Skills", content="Analytical engines")],
    )
    monkeypatch.setattr(prompt_module, "load_profile", lambda: fake_profile)
    monkeypatch.setattr(prompt_module.rag, "retrieve", lambda msg: ["RETRIEVED CHUNK"])

    prompt = prompt_module.build_system_prompt("tell me about your skills")

    assert "Ada Lovelace" in prompt
    assert "Pioneering programmer." in prompt
    assert "## Skills:" in prompt
    assert "RETRIEVED CHUNK" in prompt


def test_prompt_without_message_skips_retrieval(monkeypatch):
    fake_profile = Profile(name="Ada", summary="Bio")
    monkeypatch.setattr(prompt_module, "load_profile", lambda: fake_profile)

    def _boom(_msg):
        raise AssertionError("retrieval should not run without a user message")

    monkeypatch.setattr(prompt_module.rag, "retrieve", _boom)

    prompt = prompt_module.build_system_prompt()
    assert "Retrieved" not in prompt and "retrieved" not in prompt
