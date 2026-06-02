"""Central, env-driven configuration.

Every knob is read from the environment at call time (not import time) so tests
can monkeypatch ``os.environ`` and the running process can be reconfigured
without a restart. Defaults are chosen to be safe for a local-first app.
"""
from __future__ import annotations

import os

# --- HTTP proxy ------------------------------------------------------------

DEFAULT_HTTP_TIMEOUT = 30.0
DEFAULT_MAX_RESPONSE_CHARS = 50_000
DEFAULT_AUDIT_MAX_BYTES = 5_000_000  # ~5 MB before the log rotates


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def http_timeout() -> float:
    """Default per-request timeout (seconds) for proxied calls."""
    return _float_env("SETHU_HTTP_TIMEOUT", DEFAULT_HTTP_TIMEOUT)


def max_response_chars() -> int:
    """Cap on the characters returned to the model from a proxied response."""
    return _int_env("SETHU_MAX_RESPONSE_CHARS", DEFAULT_MAX_RESPONSE_CHARS)


def audit_max_bytes() -> int:
    """Size at which ``audit.log`` is rotated to ``audit.log.1``."""
    return _int_env("SETHU_AUDIT_MAX_BYTES", DEFAULT_AUDIT_MAX_BYTES)


# --- SSRF protection -------------------------------------------------------


def _bool(raw: str | None) -> bool:
    return (raw or "").strip().lower() not in ("", "0", "false", "no", "off")


def block_private_hosts() -> bool:
    """Whether to reject proxied requests that resolve to private/internal IPs.

    Explicit opt-in/out via ``SETHU_BLOCK_PRIVATE_HOSTS`` always wins. Otherwise
    the guard turns **on** automatically whenever the MCP endpoint is
    token-protected — i.e. a production posture — and stays **off** in open dev
    mode so local backends (``localhost``, ``127.0.0.1``) remain testable.
    """
    explicit = os.environ.get("SETHU_BLOCK_PRIVATE_HOSTS")
    if explicit is not None:
        return _bool(explicit)
    return bool(os.environ.get("SETHU_MCP_TOKEN"))
