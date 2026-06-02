# Contributing to SethuAI

Thanks for your interest in improving SethuAI! This guide covers local setup,
the checks CI runs, and how to propose changes.

## Local setup

Requirements: [`uv`](https://docs.astral.sh/uv/) (Python 3.12) and Node 18+.

```bash
git clone git@github.com:seelamraviteja/SethuAI.git && cd SethuAI
./dev.sh        # backend on :8077 (reload) + Vite dev server on :5173
```

Open `http://localhost:5173` — it proxies `/api` and `/mcp` to the backend.

## Running the checks

These are exactly what CI runs, so run them before opening a PR.

**Backend** (from `backend/`):

```bash
uv sync --dev
uv run ruff check .     # lint
uv run pytest -q        # tests
```

**Frontend** (from `frontend/`):

```bash
npm ci
npm run build           # typecheck (tsc) + production build
```

## Tests

Backend tests live in `backend/tests/`. Please add or update tests for any
behavior change — the pure modules (`generator.py`, `net.py`, `mcp_runtime`
helpers, `storage.py`, `crypto.py`) are all unit-testable without a network.

## Pull requests

1. Branch off `main`.
2. Keep changes focused; match the surrounding code style.
3. Make sure lint, tests, and the frontend build all pass.
4. Describe the change and the motivation in the PR body.

## Reporting bugs / requesting features

Open an issue using the templates under `.github/ISSUE_TEMPLATE/`. For security
issues, please avoid filing a public issue — see `SECURITY.md`.
