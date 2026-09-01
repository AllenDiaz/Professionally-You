# Professionally-You — Frontend (Next.js)

Phase 5 of the rebuild: a Next.js (App Router, TypeScript, Tailwind v4) frontend
for the FastAPI backend in `../backend`.

## Design

**"A REPL you talk to."** No chat bubbles — turns render as a session log
(`you ›` / `allen ›` labels, hairline dividers), the composer is a terminal
prompt, and each reply ends with a small mono "receipt" line
(`[ok · 1.2s · gemini-2.5-pro]`). Space Mono for structural chrome, Newsreader
serif for reading. Light-mode-primary with a dark variant (toggle top-right);
tokens live in `app/globals.css` (`--paper`, `--ink`, `--rule`, `--phosphor`,
`--signal`).

## Structure

- `app/page.tsx` — the chat page (client component): streams `/api/chat/stream`
  via `lib/api.ts`'s `streamChat`, renders turns with `components/chat/*`.
- `app/admin/*` — token-gated admin dashboard (`components/admin/AdminShell.tsx`
  holds the token in `sessionStorage` and gates access): leads, unknown
  questions, conversation viewer, profile editor (calls `PUT /api/profile` and
  `POST /api/profile/reindex`, both admin-only on the backend).
- `lib/api.ts` — typed client for every backend endpoint, including an SSE
  frame parser for the streaming chat response.

## Run

```bash
cd frontend
cp .env.local.example .env.local   # point at the backend, default localhost:8000
npm install
npm run dev
```

Requires the backend (`../backend`) running and its `ALLOWED_ORIGINS` including
`http://localhost:3000` (the default).

## Build / lint

```bash
npm run build
npm run lint
```
