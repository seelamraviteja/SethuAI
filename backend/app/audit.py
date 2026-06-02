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

from . import config

_AUDIT_FILE = Path(__file__).resolve().parent.parent / "data" / "audit.log"
# One rotated generation is kept so recent history survives a rotation.
_BACKUP_FILE = _AUDIT_FILE.parent / (_AUDIT_FILE.name + ".1")


def _rotate_if_needed() -> None:
    if not _AUDIT_FILE.exists():
        return
    if _AUDIT_FILE.stat().st_size < config.audit_max_bytes():
        return
    _BACKUP_FILE.unlink(missing_ok=True)
    _AUDIT_FILE.rename(_BACKUP_FILE)


def record(entry: dict[str, Any]) -> None:
    entry = {"ts": datetime.now(timezone.utc).isoformat(), **entry}
    _AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    _rotate_if_needed()
    with _AUDIT_FILE.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")


def tail(limit: int = 100) -> list[dict[str, Any]]:
    # Read the rotated backup first so the newest `limit` entries are returned
    # even just after a rotation left the live file nearly empty.
    lines: list[str] = []
    for path in (_BACKUP_FILE, _AUDIT_FILE):
        if path.exists():
            lines.extend(path.read_text().splitlines())
    out: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    out.reverse()  # newest first
    return out
