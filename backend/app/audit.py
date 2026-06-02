"""Append-only audit log of every proxied tool call.

Every call funnels through ``mcp_runtime.invoke`` — the single choke point — so
logging there captures both live MCP traffic and UI "Run test" calls. Stored as
JSON Lines under ``data/audit.log``.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_AUDIT_FILE = Path(__file__).resolve().parent.parent / "data" / "audit.log"


def record(entry: dict[str, Any]) -> None:
    entry = {"ts": datetime.now(timezone.utc).isoformat(), **entry}
    _AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _AUDIT_FILE.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")


def tail(limit: int = 100) -> list[dict[str, Any]]:
    if not _AUDIT_FILE.exists():
        return []
    lines = _AUDIT_FILE.read_text().splitlines()
    out: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    out.reverse()  # newest first
    return out
