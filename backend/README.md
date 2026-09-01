# Professionally-You — Backend (FastAPI)

Phase 1 of the rebuild: a FastAPI service that ports the original Gradio
`app.py` logic (Vertex AI auth, tool-calling loop, Pushover tools, system-prompt
builder) into a structured, testable backend — and fixes the known bugs.

## What Phase 1 includes

- `app/config.py` — typed settings; accepts **`GCP_LOCATION` or `GOOGLE_LOCATION`**.
- `app/vertex.py` — Vertex AI OpenAI-compat client with **cached ADC token** (refreshes only when expired).
- `app/tools.py` — the two tools with a **safe explicit dispatch table** (no more `globals()`).
- `app/pushover.py` — Pushover helper that no-ops when unconfigured.
- `app/prompt.py` — system-prompt builder (full profile for now; RAG comes in Phase 2).
- `app/chat.py` — **bounded** tool-calling loop (`MAX_TOOL_ITERATIONS`, default 6).
- `app/routers/` — `GET /api/health`, `POST /api/chat`.

## Run

```bash
cd backend
uv sync                       # or: pip install -e . && pip install pytest httpx
uv run uvicorn app.main:app --reload --port 8000
```

Auth uses Application Default Credentials:

```bash
gcloud auth application-default login
```

## Test

```bash
cd backend
uv run pytest            # tests are fully offline (Vertex + Pushover are mocked)
```

## Environment variables

| Var | Purpose | Default |
| --- | --- | --- |
| `GCP_PROJECT` | Google Cloud project id | — |
| `GCP_LOCATION` / `GOOGLE_LOCATION` | Vertex region | `us-central1` |
| `MODEL_NAME` | Gemini model | `google/gemini-2.5-pro` |
| `PERSON_NAME` | Persona name | `Allen Diaz` |
| `PUSHOVER_USER` / `PUSHOVER_TOKEN` | Notifications | unset → skipped |
| `MAX_TOOL_ITERATIONS` | Tool-loop cap | `6` |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | `http://localhost:3000` |
| `ME_DIR` | Profile source dir | repo `me/` |
