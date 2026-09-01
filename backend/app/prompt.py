"""System-prompt construction.

Phase 2: the prompt is now built from the editable profile (summary + sections)
plus **query-aware RAG retrieval** — only the top-k LinkedIn chunks relevant to
the current user message are included, instead of the entire PDF every turn.
"""

from . import rag
from .config import get_settings
from .profile import load_profile


def build_system_prompt(user_message: str | None = None) -> str:
    settings = get_settings()
    profile = load_profile()
    name = profile.name or settings.person_name

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

    prompt += f"\n\n## Summary:\n{profile.summary}\n"
    for section in profile.sections:
        prompt += f"\n## {section.title}:\n{section.content}\n"

    # Query-aware retrieval — replaces dumping the whole LinkedIn PDF every turn.
    if user_message:
        snippets = rag.retrieve(user_message)
        if snippets:
            joined = "\n\n---\n\n".join(snippets)
            prompt += f"\n\n## Relevant background (retrieved):\n{joined}\n"

    prompt += (
        f"\n\nWith this context, please chat with the user, "
        f"always staying in character as {name}."
    )
    return prompt
