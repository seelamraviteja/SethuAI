"""SSRF protection for outbound proxied requests.

The MCP runtime forwards tool calls to whatever ``base_url`` a catalog declares,
and the management API fetches spec URLs the user pastes in. Both are
attacker-influenced, so before we make a request we resolve the host and refuse
addresses that point back at internal infrastructure (loopback, private ranges,
link-local cloud-metadata endpoints, etc.).

The check is opt-in via :func:`app.config.block_private_hosts` — off in open dev
mode (so local backends stay testable), on automatically once the deployment is
token-protected.
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit

from . import config


class BlockedHostError(Exception):
    """Raised when a URL resolves to a disallowed (internal) address."""


def _ip_is_internal(ip: ipaddress._BaseAddress) -> bool:
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def _resolve(host: str) -> list[ipaddress._BaseAddress]:
    # A literal IP needs no DNS; otherwise resolve every A/AAAA record so a
    # hostname can't smuggle one internal address past us behind a public one.
    try:
        return [ipaddress.ip_address(host)]
    except ValueError:
        pass
    infos = socket.getaddrinfo(host, None)
    return [ipaddress.ip_address(info[4][0]) for info in infos]


def validate_url(url: str) -> None:
    """Raise :class:`BlockedHostError` if ``url`` is unsafe to request.

    No-op when the guard is disabled. Always rejects non-HTTP schemes and
    unparseable hosts, since those are never legitimate proxy targets.
    """
    if not config.block_private_hosts():
        return

    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise BlockedHostError(f"Unsupported URL scheme: {parts.scheme or '(none)'!r}")

    host = parts.hostname
    if not host:
        raise BlockedHostError("URL has no host.")

    try:
        addresses = _resolve(host)
    except socket.gaierror as exc:
        raise BlockedHostError(f"Could not resolve host {host!r}: {exc}") from exc

    for ip in addresses:
        if _ip_is_internal(ip):
            raise BlockedHostError(
                f"Refusing request to internal address {ip} (host {host!r}). "
                "Set SETHU_BLOCK_PRIVATE_HOSTS=0 to allow private targets."
            )
