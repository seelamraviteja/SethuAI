"""The hosted MCP server.

A single low-level MCP ``Server`` whose tool list is computed *live* from all
published catalogs on every request. Tool names are prefixed with the catalog
slug (``<slug>__<tool>``) so one Streamable HTTP endpoint can serve many APIs.
Each tool call is translated into an HTTP request against the catalog's backend.
"""
from __future__ import annotations

import json
from typing import Any

import httpx
import mcp.types as types
from mcp.server.lowlevel import Server

from . import audit, config, net, storage
from .generator import build_input_schema
from .models import Catalog, ToolDef

server: Server = Server("sethuai")


def _prefixed(slug: str, tool_name: str) -> str:
    return f"{slug}__{tool_name}"


def _find_tool(prefixed_name: str) -> tuple[Catalog, ToolDef] | tuple[None, None]:
    slug, _, tool_name = prefixed_name.partition("__")
    for catalog in storage.list_published():
        if catalog.slug != slug:
            continue
        for tool in catalog.tools:
            if tool.tool_name == tool_name and tool.enabled:
                return catalog, tool
    return None, None


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    tools: list[types.Tool] = []
    for catalog in storage.list_published():
        for tool in catalog.tools:
            if not tool.enabled:
                continue
            description = tool.description or f"{tool.method.upper()} {tool.path}"
            if tool.destructive:
                description = f"[DESTRUCTIVE] {description}"
            tools.append(
                types.Tool(
                    name=_prefixed(catalog.slug, tool.tool_name),
                    description=description,
                    inputSchema=build_input_schema(tool),
                )
            )
    return tools


def _build_request(catalog: Catalog, tool: ToolDef, arguments: dict[str, Any]):
    path = tool.path
    query: dict[str, Any] = {}
    headers: dict[str, str] = {}

    for param in tool.params:
        if param.name not in arguments:
            continue
        value = arguments[param.name]
        if param.location == "path":
            path = path.replace("{" + param.name + "}", str(value))
        elif param.location == "header":
            headers[param.name] = str(value)
        else:  # query (cookie params are uncommon; treat as query)
            query[param.name] = value

    body = arguments.get("body")

    auth = catalog.auth
    httpx_auth = None
    if auth.type == "apiKey" and auth.api_key_name:
        if auth.api_key_in == "query":
            query[auth.api_key_name] = auth.api_key_value
        else:
            headers[auth.api_key_name] = auth.api_key_value
    elif auth.type == "bearer" and auth.bearer_token:
        headers["Authorization"] = f"Bearer {auth.bearer_token}"
    elif auth.type == "basic":
        httpx_auth = (auth.username, auth.password)

    url = catalog.base_url.rstrip("/") + "/" + path.lstrip("/")
    return url, query, headers, body, httpx_auth


async def invoke(
    catalog: Catalog, tool: ToolDef, arguments: dict[str, Any], source: str = "mcp"
) -> str:
    """Proxy a single tool call to the backend API and return a text result.

    Every call — whether from a live MCP client or the UI's test button — passes
    through here, so this is where we write the audit log.
    """
    base = {
        "source": source,
        "catalog": catalog.name,
        "slug": catalog.slug,
        "tool": tool.tool_name,
        "method": tool.method.upper(),
        "path": tool.path,
        "destructive": tool.destructive,
    }

    if not catalog.base_url:
        audit.record({**base, "ok": False, "status": None, "error": "no base_url"})
        return "Error: catalog has no base_url configured."

    url, query, headers, body, httpx_auth = _build_request(catalog, tool, arguments)

    try:
        net.validate_url(url)
    except net.BlockedHostError as exc:
        audit.record({**base, "ok": False, "status": None, "error": f"blocked: {exc}"})
        return f"Blocked: {exc}"

    timeout = tool.timeout_seconds or config.http_timeout()
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.request(
                tool.method.upper(),
                url,
                params=query or None,
                headers=headers or None,
                json=body if body is not None else None,
                auth=httpx_auth,
            )
    except httpx.RequestError as exc:
        audit.record({**base, "ok": False, "status": None, "error": str(exc)})
        return f"Request failed: {exc.__class__.__name__}: {exc}"

    audit.record({**base, "ok": response.is_success, "status": response.status_code})

    body_text = _shape_response(response.text, response.headers.get("content-type", ""))
    return f"HTTP {response.status_code} {response.reason_phrase}\n\n{body_text}"


def _shape_response(text: str, content_type: str) -> str:
    """Cap an oversized response, staying valid JSON when we can.

    For a JSON array we keep as many leading items as fit under the budget and
    append a machine-readable note about how many were dropped — far more useful
    to a model than a mid-token character cut. Everything else falls back to a
    plain truncation marker.
    """
    limit = config.max_response_chars()
    if len(text) <= limit:
        return text

    if "json" in content_type.lower():
        try:
            data = json.loads(text)
        except ValueError:
            data = None
        if isinstance(data, list) and data:
            kept = list(data)
            while len(kept) > 1:
                shaped = json.dumps(kept)
                if len(shaped) <= limit:
                    omitted = len(data) - len(kept)
                    if not omitted:  # re-serialized compact JSON already fits
                        return shaped
                    note = f"\n…[truncated: {omitted} of {len(data)} items omitted]"
                    return shaped + note
                # Drop ~10% of the remaining items each pass to converge fast.
                kept = kept[: max(1, len(kept) - max(1, len(kept) // 10))]
            # A single item still over budget falls through to char truncation.

    return text[:limit] + "\n…[response truncated]"


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    catalog, tool = _find_tool(name)
    if catalog is None or tool is None:
        return [types.TextContent(type="text", text=f"Unknown or disabled tool: {name}")]
    result = await invoke(catalog, tool, arguments or {})
    return [types.TextContent(type="text", text=result)]
