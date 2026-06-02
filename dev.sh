#!/usr/bin/env bash
# Dev mode: backend on :8077 with reload + Vite dev server on :5173 (HMR).
# Open http://localhost:5173  — it proxies /api and /mcp to the backend.
set -euo pipefail
cd "$(dirname "$0")"

( cd backend && unset VIRTUAL_ENV && uv sync )

( cd backend && unset VIRTUAL_ENV && uv run uvicorn app.main:app --port 8077 --reload ) &
BACK=$!
trap "kill $BACK 2>/dev/null || true" EXIT

( cd frontend && npm install && npm run dev )
