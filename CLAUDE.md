# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git Workflow

**Professional, granular GitHub sequence from add to push — without a Claude co-author.**

When committing work in this repo:
- Make **granular commits**: group related files into small, logically-scoped commits rather than one large commit. Each commit does one thing.
- Use **conventional commit messages** (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `build:`, `chore:`).
- Run the full sequence: `git add` → `git commit` (one per logical change) → `git push`.
- **Commit and push directly to `main`** (no feature branch).
- **Do NOT add a `Co-Authored-By: Claude` trailer** (or any Claude/Anthropic co-author line) to commits.

## Project Overview

**Professionally-You** is an AI-powered career chatbot — a "digital twin" that answers questions about a person's professional background. It was originally a single Gradio/notebook app (`main.ipynb`, `app.py` — kept as a historical reference, no longer the entrypoint); it has since been rebuilt as a **FastAPI backend + Next.js frontend**, containerized with **Podman**.

## Architecture

```
Next.js (frontend/, port 3000)  ──HTTP/SSE──▶  FastAPI (backend/, port 8000)
  chat UI + admin dashboard                       ├─ Vertex AI (ADC, cached token) ── Gemini
                                                   ├─ RAG retrieval (embeddings, JSON index)
                                                   ├─ guardrail + evaluator (LLM-as-judge)
                                                   ├─ tools → Pushover
                                                   └─ Postgres/SQLite (conversations, leads, unknown Qs)
```

- **`backend/`** — see `backend/README.md`. FastAPI app (`app/main.py`), Vertex AI auth with cached ADC token (`app/vertex.py`), a bounded tool-calling loop (`app/chat.py`, `app/stream.py` for SSE), RAG-based system prompt (`app/rag.py`, `app/prompt.py`) instead of dumping the whole LinkedIn PDF every turn, an editable profile store (`app/profile.py`), SQLAlchemy persistence (`app/models.py`, `app/db.py`), an admin API guarded by a bearer token (`app/auth.py`, `app/routers/admin.py`), input guardrail + output evaluator (`app/guardrails.py`), and per-IP rate limiting (`app/rate_limit.py`).
- **`frontend/`** — see `frontend/README.md`. Next.js (App Router, TypeScript, Tailwind v4) chat UI that streams `/api/chat/stream`, plus a token-gated admin dashboard under `/admin`.
- **`podman-compose.yml`** — runs `web` + `api` + `db` (Postgres) together. `backend/Containerfile` and `frontend/Containerfile` build each image; run `podman-compose up --build` from the repo root.
- **`me/`** — source-of-record LinkedIn PDF + summary, read by the backend's RAG ingest.

## Running the Application

**New stack (recommended):**
```bash
podman-compose up --build
```
Or run each half locally — see `backend/README.md` and `frontend/README.md` for `uv sync` / `npm install` + dev-server instructions.

**Legacy notebook (still present, not the primary path):**
```bash
uv sync
uv run jupyter notebook main.ipynb
```
The Gradio UI launches locally once all cells are executed.

## Environment Variables

See `.env.example` at the repo root for the full, correctly-named list (backend reads `GCP_LOCATION`, accepting the legacy `GOOGLE_LOCATION` name too). Backend-specific vars (`DATABASE_URL`, `ADMIN_TOKEN`, `ENABLE_GUARDRAILS`, etc.) are documented in `backend/README.md`; the frontend's `NEXT_PUBLIC_API_BASE_URL` is documented in `frontend/README.md`.

## Deployment

The new stack is provider-agnostic via containers (`podman-compose.yml`); see `backend/Containerfile` / `frontend/Containerfile`. The legacy notebook's HuggingFace Spaces deployment path (`uv run gradio deploy`, Space `career_conversation`) still works if you need it, but is no longer the primary deployment target.
