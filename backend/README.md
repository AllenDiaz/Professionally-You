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

## What Phase 2 adds (RAG + editable profile)

- `app/sources.py` — cached loaders for `me/linkedin.pdf` and `me/summary.txt`.
- `app/embeddings.py` — Vertex text embeddings (isolated for testing).
- `app/rag.py` — chunk → embed → persist a JSON index; cosine top-k retrieval. **Replaces dumping the whole PDF into every prompt.**
- `app/profile.py` — editable `data/profile.json`, seeded from `me/` on first load.
- `app/prompt.py` — now builds from the profile summary/sections + query-relevant retrieved chunks.
- Endpoints: `GET/PUT /api/profile`, `POST /api/profile/reindex`.

After changing the profile or LinkedIn PDF, call `POST /api/profile/reindex` to rebuild the RAG index.

## What Phase 3 adds (persistence + admin API)

- `app/models.py` + `app/db.py` — SQLAlchemy models and engine. **SQLite by default**; set `DATABASE_URL` to a Postgres URL in prod.
- `app/crud.py` — data-access helpers.
- `app/tools.py` — the conversation id is threaded explicitly into tool calls (`record_user_details`, `record_unknown_question`), which now **persist** to the DB (leads, unknown questions) in addition to Pushover.
- `POST /api/chat` now persists the conversation + both messages and returns a `conversation_id` (pass it back to continue a conversation).
- `app/routers/admin.py` — bearer-token-guarded (`ADMIN_TOKEN`):
  - `GET /api/admin/leads`
  - `GET /api/admin/unknown-questions`
  - `GET /api/admin/conversations` and `/api/admin/conversations/{id}`

Additional env vars: `DATABASE_URL` (default local SQLite at `backend/data/app.db`), `ADMIN_TOKEN` (required to use the admin API; unset → 503).

## What Phase 4 adds (streaming + guardrails/evaluator + rate limiting)

- `app/stream.py` — streaming counterpart to `chat.py`; accumulates tool-call fragments across chunks, executes them, and resumes streaming. Same bounded tool loop as the non-streaming path.
- `app/guardrails.py` — the "Evaluator" pattern the notebook always suggested but never built:
  - **Input guardrail**: judges each user message before the model runs; blocks abusive/off-topic input with a redirect message.
  - **Output evaluator**: judges the drafted reply for on-persona/accuracy; on rejection, retries **once** with the evaluator's feedback appended.
  - Both **fail open** (never block a reply) if the judge call itself errors, and can be disabled via `ENABLE_GUARDRAILS` / `ENABLE_EVALUATOR`.
- `app/rate_limit.py` — shared `slowapi` limiter, applied per client IP to both chat endpoints via `CHAT_RATE_LIMIT` (default `20/minute`).
- `POST /api/chat/stream` — **new** SSE endpoint. Emits `data: {"delta": "..."}` events, then `data: {"done": true, "conversation_id": ...}`. Persists the conversation the same way as `/api/chat`. **Guardrail runs, evaluator does not** (evaluating the full reply before sending would defeat streaming) — use `/api/chat` when the evaluator matters more than latency.

Additional env vars: `ENABLE_GUARDRAILS` (default `true`), `ENABLE_EVALUATOR` (default `true`), `CHAT_RATE_LIMIT` (default `20/minute`, [slowapi format](https://github.com/laurentS/slowapi)).

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
