#!/usr/bin/env bash
# Build the UI and serve everything (UI + REST API + MCP) from one process.
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-8077}"

echo "▸ Building frontend…"
( cd frontend && npm install --silent && npm run build )

echo "▸ Syncing backend deps…"
( cd backend && unset VIRTUAL_ENV && uv sync )

echo "▸ Starting on http://localhost:${PORT}  (MCP at /mcp)"
cd backend
unset VIRTUAL_ENV
exec uv run uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
