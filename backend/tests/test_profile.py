"""Tests for the editable profile store and its endpoints."""

from fastapi.testclient import TestClient

import app.profile as profile_module
from app.main import app
from app.profile import Profile, ProfileSection

client = TestClient(app)


def test_load_profile_seeds_from_summary(monkeypatch, tmp_path):
    path = tmp_path / "profile.json"
    monkeypatch.setattr(profile_module, "_profile_path", lambda: path)
    monkeypatch.setattr(profile_module.sources, "load_summary_text", lambda: "  seed summary  ")

    loaded = profile_module.load_profile()

    assert loaded.summary == "seed summary"
    assert loaded.name  # taken from settings.person_name
    assert path.exists()  # seeded file written to disk


def test_save_and_reload_roundtrip(monkeypatch, tmp_path):
    path = tmp_path / "profile.json"
    monkeypatch.setattr(profile_module, "_profile_path", lambda: path)

    original = Profile(
        name="Test Person",
        headline="Engineer",
        summary="Bio",
        sections=[ProfileSection(title="Skills", content="Python")],
    )
    profile_module.save_profile(original)
    reloaded = profile_module.load_profile()

    assert reloaded == original


def test_reindex_endpoint(monkeypatch):
    monkeypatch.setattr("app.routers.profile.rag.build_index", lambda: 7)
    response = client.post("/api/profile/reindex")

    assert response.status_code == 200
    assert response.json() == {"chunks": 7}


def test_get_profile_endpoint(monkeypatch, tmp_path):
    path = tmp_path / "profile.json"
    monkeypatch.setattr(profile_module, "_profile_path", lambda: path)
    monkeypatch.setattr(profile_module.sources, "load_summary_text", lambda: "endpoint summary")

    response = client.get("/api/profile")

    assert response.status_code == 200
    assert response.json()["summary"] == "endpoint summary"
