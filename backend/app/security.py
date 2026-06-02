"""Token-based access control.

Two independent, opt-in tokens (set via env):

* ``SETHU_ADMIN_TOKEN`` — gates the management API (``/api/*``).
* ``SETHU_MCP_TOKEN``   — gates the hosted MCP endpoint (``/mcp``).

If a token env var is unset, that surface runs **open** (dev mode). Startup logs
a warning so an open deployment is never silent.
"""
from __future__ import annotations

import os

from fastapi import Header, HTTPException


def _extract(authorization: str, header_token: str) -> str:
    if authorization.startswith("Bearer "):
        return authorization[len("Bearer ") :].strip()
    return header_token.strip()


def require_admin(
    authorization: str = Header(default=""),
    x_admin_token: str = Header(default=""),
) -> None:
    expected = os.environ.get("SETHU_ADMIN_TOKEN")
    if not expected:
        return  # open mode
    if _extract(authorization, x_admin_token) != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing admin token.")


def check_mcp_token(authorization: str, x_api_key: str = "") -> bool:
    expected = os.environ.get("SETHU_MCP_TOKEN")
    if not expected:
        return True  # open mode
    return _extract(authorization, x_api_key) == expected


def auth_status() -> dict[str, bool]:
    return {
        "admin_protected": bool(os.environ.get("SETHU_ADMIN_TOKEN")),
        "mcp_protected": bool(os.environ.get("SETHU_MCP_TOKEN")),
    }
