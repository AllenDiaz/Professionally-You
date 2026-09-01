"""Editable profile store.

Replaces the hardcoded name + raw files as the source of persona text. The
profile is persisted as ``data/profile.json`` and, on first load, seeded from
``me/summary.txt`` and the configured person name. Phase 3 can migrate this into
a database table without changing the public functions here.
"""

import json
from pathlib import Path

from pydantic import BaseModel, Field

from . import sources
from .config import get_settings


class ProfileSection(BaseModel):
    title: str
    content: str


class Profile(BaseModel):
    name: str
    headline: str = ""
    summary: str = ""
    sections: list[ProfileSection] = Field(default_factory=list)


def _profile_path() -> Path:
    return get_settings().data_dir / "profile.json"


def load_profile() -> Profile:
    """Load the profile, seeding it from ``me/`` files on first access."""
    path = _profile_path()
    if path.exists():
        return Profile.model_validate(json.loads(path.read_text(encoding="utf-8")))

    settings = get_settings()
    profile = Profile(
        name=settings.person_name,
        summary=sources.load_summary_text().strip(),
    )
    save_profile(profile)
    return profile


def save_profile(profile: Profile) -> Profile:
    path = _profile_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(profile.model_dump_json(indent=2), encoding="utf-8")
    return profile
