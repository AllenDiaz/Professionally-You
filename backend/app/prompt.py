"""System-prompt construction.

Ports ``Me.system_prompt()`` from the original ``app.py``. For Phase 1 the full
LinkedIn PDF text and summary are loaded once (cached) and embedded verbatim.
Phase 2 will replace the ``## LinkedIn Profile`` section with top-k RAG retrieval.
"""

from functools import lru_cache

from pypdf import PdfReader

from .config import get_settings


@lru_cache
def _load_context() -> tuple[str, str]:
    """Load (summary, linkedin) text from the ``me/`` directory, cached."""
    settings = get_settings()

    linkedin = ""
    pdf_path = settings.me_dir / "linkedin.pdf"
    if pdf_path.exists():
        reader = PdfReader(str(pdf_path))
        for page in reader.pages:
            text = page.extract_text()
            if text:
                linkedin += text

    summary = ""
    summary_path = settings.me_dir / "summary.txt"
    if summary_path.exists():
        summary = summary_path.read_text(encoding="utf-8")

    return summary, linkedin


def build_system_prompt() -> str:
    settings = get_settings()
    name = settings.person_name
    summary, linkedin = _load_context()

    prompt = (
        f"You are acting as {name}. You are answering questions on {name}'s website, "
        f"particularly questions related to {name}'s career, background, skills and experience. "
        f"Your responsibility is to represent {name} for interactions on the website as faithfully as possible. "
        f"You are given a summary of {name}'s background and LinkedIn profile which you can use to answer questions. "
        f"Be professional and engaging, as if talking to a potential client or future employer who came across the website. "
        f"If you don't know the answer to any question, use your record_unknown_question tool to record the question "
        f"that you couldn't answer, even if it's about something trivial or unrelated to career. "
        f"If the user is engaging in discussion, try to steer them towards getting in touch via email; "
        f"ask for their email and record it using your record_user_details tool. "
    )
    prompt += f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{linkedin}\n\n"
    prompt += f"With this context, please chat with the user, always staying in character as {name}."
    return prompt
