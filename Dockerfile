# ---- Stage 1: build the React UI ----
FROM node:22-slim AS ui
WORKDIR /ui
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: python runtime serving UI + REST API + MCP ----
FROM python:3.12-slim AS runtime
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app

COPY backend/pyproject.toml ./backend/
WORKDIR /app/backend
RUN uv sync

WORKDIR /app
COPY backend/ ./backend/
# main.py looks for ../frontend/dist relative to backend/app
COPY --from=ui /ui/dist ./frontend/dist

EXPOSE 8077
WORKDIR /app/backend
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8077"]
