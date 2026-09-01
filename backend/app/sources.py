"""Raw source loaders for the ``me/`` directory.

Shared by the profile store, the RAG indexer, and the prompt builder so none of
them import each other. Results are cached; call ``clear_cache()`` after the
underlying files change (e.g. a new LinkedIn PDF).
"""

from functools import lru_cache

from pypdf import PdfReader

from .config import get_settings


@lru_cache
def load_linkedin_text() -> str:
    """Extract and concatenate the text of every page in ``me/linkedin.pdf``."""
    settings = get_settings()
    path = settings.me_dir / "linkedin.pdf"
    if not path.exists():
        return ""
    reader = PdfReader(str(path))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text


@lru_cache
def load_summary_text() -> str:
    """Read ``me/summary.txt`` (empty string if absent)."""
    settings = get_settings()
    path = settings.me_dir / "summary.txt"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def clear_cache() -> None:
    load_linkedin_text.cache_clear()
    load_summary_text.cache_clear()
