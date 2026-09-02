# Professionally You

An AI-powered career chatbot that acts as your professional digital twin. It answers questions about your background, skills, and experience as *you*, backed by Google Gemini (Vertex AI) and grounded in your LinkedIn profile and career summary via retrieval.

## Features

- **Streaming chat UI** (Next.js) with a distinctive "session log" design — no generic chat bubbles. Turns render as a terminal-style log (`you ›` / `allen ›` labels, hairline dividers), and each reply ends with a small mono receipt line (`[ok · 1.2s · gemini-2.5-pro]`).
- **Speaks as you** — a persona system prompt represents you professionally to potential employers or clients, steering interested visitors toward sharing their contact info.
- **RAG retrieval** over your LinkedIn profile — the PDF is chunked, embedded, and only the query-relevant snippets are pulled into each prompt, instead of dumping the whole document every turn. The index is built automatically on first startup.
- **Guardrail + evaluator** (LLM-as-judge): an input guardrail blocks off-topic/abusive messages with a redirect, and an output evaluator checks each reply for on-persona accuracy and retries once with feedback. Both fail open if the judge call errors.
- **Lead & question capture** — tool calls record interested visitors' contact details and questions the twin can't answer, persisted to the database and pushed to your phone.
- **Token-gated admin dashboard** — review captured leads, unknown questions, and full conversation transcripts, and edit your profile / rebuild the RAG index from the browser.
- **Push notifications** via Pushover for real-time alerts (optional).
- **Per-IP rate limiting** on the chat endpoints.
- **Containerized with Podman** for one-command local/self-hosted deployment (web + api + Postgres).

## Architecture

```
Next.js (frontend/, :3000)  ──HTTP/SSE──▶  FastAPI (backend/, :8000)
  chat UI + admin dashboard                   ├─ Vertex AI (ADC, cached token) ── Gemini
                                              ├─ RAG retrieval (embeddings, JSON index)
                                              ├─ guardrail + evaluator (LLM-as-judge)
                                              ├─ tools → Pushover + DB
                                              └─ Postgres / SQLite (conversations, leads, questions)
```

The browser streams `POST /api/chat/stream` (Server-Sent Events) directly from the FastAPI backend, which runs a bounded tool-calling loop against Gemini, retrieves relevant profile context per question, and persists each conversation. The admin dashboard talks to bearer-token-guarded `/api/admin/*` endpoints.

See `CLAUDE.md` for the full architecture breakdown, and `backend/README.md` / `frontend/README.md` for per-service details and the complete endpoint list.

## Tech stack

- **Frontend:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4.
- **Backend:** FastAPI, Python 3.12, SQLAlchemy 2.0, Pydantic v2. Vertex AI via its OpenAI-compatible endpoint for chat and its native embeddings API, with credentials from Application Default Credentials (cached, refreshed only on expiry).
- **Storage:** Postgres in the container stack; SQLite by default when running locally. The RAG index is a plain JSON file (no vector DB).
- **Runtime:** Podman / Docker via `podman-compose.yml`.

## Prerequisites

- [Podman](https://podman.io/) (or Docker) for the recommended setup
- A Google Cloud project with Vertex AI enabled, plus `gcloud auth application-default login` run on your host
- Your LinkedIn profile exported as a PDF, plus a written career summary
- [Pushover](https://pushover.net/) account (optional — notifications are skipped if unset)

## Setup

### 1. Prepare personal context files

Add to the `me/` directory:
- `me/linkedin.pdf` — your exported LinkedIn profile PDF
- `me/summary.txt` — a career summary / talking points about yourself

### 2. Configure environment variables

```bash
cp .env.example .env
```

Fill in `GCP_PROJECT` and `PERSON_NAME`. Optionally set `PUSHOVER_USER` / `PUSHOVER_TOKEN` for push notifications, and `ADMIN_TOKEN` to enable the admin dashboard (without it, the admin API returns 503). See `.env.example` for the full list and `backend/README.md` for backend-specific vars (`DATABASE_URL`, `ENABLE_GUARDRAILS`, `CHAT_RATE_LIMIT`, RAG tuning, etc.).

### 3. Run

```bash
podman-compose up --build
```

This brings up the frontend (`http://localhost:3000`), the API (`http://localhost:8000`), and a Postgres database together. Your host's GCP Application Default Credentials are mounted read-only into the API container, and `me/` is mounted so the backend can build its RAG index on startup.

To run each half locally without containers instead, see `backend/README.md` (`uv sync` + `uvicorn`) and `frontend/README.md` (`npm install` + `npm run dev`).

## Using it

- **Chat:** open `http://localhost:3000` and ask the twin about your background. Replies stream token-by-token.
- **Admin:** go to `http://localhost:3000/admin` and enter your `ADMIN_TOKEN`. From there you can review leads, unanswered questions, and conversation transcripts, edit your profile, and click **rebuild rag index** after changing your profile or LinkedIn PDF.

## Project Structure

```
├── backend/            # FastAPI service — Vertex AI, RAG, guardrails, persistence, admin API
├── frontend/           # Next.js chat UI + admin dashboard
├── podman-compose.yml  # web + api + db (Postgres) stack
├── .env.example        # documented environment variables
├── me/
│   ├── linkedin.pdf    # your LinkedIn export
│   └── summary.txt     # your career summary
├── main.ipynb          # legacy notebook prototype (kept for reference)
├── app.py              # legacy single-file Gradio app (kept for reference)
└── requirements.txt    # pinned deps for the legacy app
```

## Testing

The backend ships a fully offline test suite (Vertex AI and Pushover are mocked):

```bash
cd backend
uv run pytest
```

## Legacy: notebook / Gradio app

The project started as a single Gradio app (`app.py`, `main.ipynb`). It still runs standalone if you need it:

```bash
uv sync
uv run jupyter notebook main.ipynb
```

The Gradio UI launches at `http://localhost:7860`. It can still be deployed to HuggingFace Spaces via `uv run gradio deploy` (Space name `career_conversation`, `cpu-basic` hardware). This is no longer the primary path — new work should go into `backend/` and `frontend/`.
