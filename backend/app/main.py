"""SethuAI — FastAPI app serving three things from one process:

1. ``/api/*``  – the management REST API used by the UI
2. ``/mcp``    – the hosted MCP Streamable HTTP endpoint
3. ``/``       – the built React UI (when ``frontend/dist`` exists)
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.types import Receive, Scope, Send

from . import security
from .api import router as api_router
from .mcp_runtime import server as mcp_server

logger = logging.getLogger("sethuai")

# Stateless + JSON responses keep hosting simple: no per-session state to
# persist, and responses are plain application/json (easy to test with curl
# and accepted by Streamable HTTP clients).
session_manager = StreamableHTTPSessionManager(
    app=mcp_server,
    json_response=True,
    stateless=True,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    status = security.auth_status()
    if not status["admin_protected"]:
        logger.warning("SETHU_ADMIN_TOKEN not set — management API (/api) is OPEN.")
    if not status["mcp_protected"]:
        logger.warning("SETHU_MCP_TOKEN not set — MCP endpoint (/mcp) is OPEN.")
    async with session_manager.run():
        yield


app = FastAPI(title="SethuAI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


async def _mcp_asgi(scope: Scope, receive: Receive, send: Send) -> None:
    # Gate the MCP transport on SETHU_MCP_TOKEN (no-op if unset).
    if scope["type"] == "http":
        headers = {k.decode(): v.decode() for k, v in scope.get("headers", [])}
        if not security.check_mcp_token(
            headers.get("authorization", ""), headers.get("x-api-key", "")
        ):
            await send(
                {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            await send({"type": "http.response.body", "body": b'{"error":"unauthorized"}'})
            return
    await session_manager.handle_request(scope, receive, send)


# The session manager is path-agnostic; mounting it at /mcp routes all
# POST/GET/DELETE for the MCP transport to it.
app.mount("/mcp", _mcp_asgi)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Serve the built frontend. We avoid a greedy catch-all route on purpose: a
# `/{path:path}` GET route would shadow bare `POST /mcp` (returning 405 before
# Starlette's trailing-slash redirect to /mcp/ can run). The UI is a single page
# with state-based views, so serving index.html at "/" plus the assets mount is
# all that's needed.
_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _DIST.exists():
    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    @app.get("/")
    def index():
        return FileResponse(_DIST / "index.html")
