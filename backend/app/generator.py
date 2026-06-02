"""Turn an OpenAPI / Swagger spec into a draft Catalog of MCP tools.

Supports OpenAPI 3.x and Swagger 2.0. Local ``$ref``s are dereferenced so each
tool's input schema is self-contained (cycles are broken with an empty schema).
"""
from __future__ import annotations

import re
import uuid
from typing import Any

from .models import Catalog, ParamDef, ToolDef

_HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")


def slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return text or "api"


def _sanitize_tool_name(text: str) -> str:
    """MCP tool names should be stable identifiers: [a-zA-Z0-9_]."""
    name = re.sub(r"[^a-zA-Z0-9_]+", "_", text.strip()).strip("_")
    return name or "operation"


def _resolve_pointer(root: dict, ref: str) -> Any:
    if not ref.startswith("#/"):
        return None
    node: Any = root
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None
    return node


def _make_deref(root: dict):
    def deref(node: Any, seen: tuple = ()) -> Any:
        if isinstance(node, dict):
            ref = node.get("$ref")
            if isinstance(ref, str):
                if ref in seen:
                    return {}
                target = _resolve_pointer(root, ref)
                if target is None:
                    return {}
                return deref(target, seen + (ref,))
            return {k: deref(v, seen) for k, v in node.items() if k != "$ref"}
        if isinstance(node, list):
            return [deref(item, seen) for item in node]
        return node

    return deref


def _swagger2_param_schema(param: dict) -> dict[str, Any]:
    """Build a JSON Schema for a Swagger 2.0 non-body parameter."""
    schema: dict[str, Any] = {}
    for key in ("type", "format", "enum", "items", "default", "minimum", "maximum"):
        if key in param:
            schema[key] = param[key]
    if not schema:
        schema["type"] = "string"
    return schema


def _base_url(spec: dict) -> str:
    servers = spec.get("servers")
    if isinstance(servers, list) and servers:
        url = servers[0].get("url", "")
        if url:
            return url
    if "host" in spec:  # Swagger 2.0
        scheme = (spec.get("schemes") or ["https"])[0]
        return f"{scheme}://{spec['host']}{spec.get('basePath', '')}"
    return ""


def generate_catalog(spec: dict) -> Catalog:
    deref = _make_deref(spec)
    info = spec.get("info", {}) or {}
    name = info.get("title") or "Untitled API"

    catalog = Catalog(
        id=uuid.uuid4().hex[:8],
        name=name,
        description=info.get("description", "") or "",
        base_url=_base_url(spec),
        slug=slugify(name),
    )

    used_names: set[str] = set()
    paths = spec.get("paths", {}) or {}

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        shared_params = path_item.get("parameters", []) or []
        for method in _HTTP_METHODS:
            op = path_item.get(method)
            if not isinstance(op, dict):
                continue

            params: list[ParamDef] = []
            body_schema: dict[str, Any] | None = None
            body_required = False

            raw_params = list(shared_params) + list(op.get("parameters", []) or [])
            for raw in raw_params:
                raw = deref(raw)
                if not isinstance(raw, dict):
                    continue
                location = raw.get("in", "query")
                if location == "body":  # Swagger 2.0 body parameter
                    body_schema = deref(raw.get("schema", {})) or {}
                    body_required = bool(raw.get("required", False))
                    continue
                schema = deref(raw.get("schema")) if "schema" in raw else _swagger2_param_schema(raw)
                params.append(
                    ParamDef(
                        name=raw.get("name", "param"),
                        location=location,
                        required=bool(raw.get("required", False)),
                        json_schema=schema or {},
                        description=raw.get("description", "") or "",
                    )
                )

            # OpenAPI 3.x request body
            request_body = op.get("requestBody")
            if isinstance(request_body, dict):
                request_body = deref(request_body)
                content = request_body.get("content", {}) or {}
                json_content = content.get("application/json") or next(
                    (v for v in content.values() if isinstance(v, dict)), None
                )
                if isinstance(json_content, dict) and "schema" in json_content:
                    body_schema = deref(json_content["schema"]) or {}
                    body_required = bool(request_body.get("required", False))

            op_id = op.get("operationId") or f"{method}_{path}"
            tool_name = _sanitize_tool_name(op_id)
            base_tool_name = tool_name
            counter = 2
            while tool_name in used_names:
                tool_name = f"{base_tool_name}_{counter}"
                counter += 1
            used_names.add(tool_name)

            description = (op.get("summary") or op.get("description") or "").strip()

            catalog.tools.append(
                ToolDef(
                    id=uuid.uuid4().hex[:8],
                    tool_name=tool_name,
                    description=description,
                    enabled=True,
                    destructive=method == "delete",
                    method=method,
                    path=path,
                    params=params,
                    request_body_schema=body_schema,
                    request_body_required=body_required,
                )
            )

    return catalog


def build_input_schema(tool: ToolDef) -> dict[str, Any]:
    """Compose the MCP tool ``inputSchema`` from params + request body."""
    properties: dict[str, Any] = {}
    required: list[str] = []

    for param in tool.params:
        schema = dict(param.json_schema or {})
        if param.description:
            schema.setdefault("description", param.description)
        properties[param.name] = schema or {"type": "string"}
        if param.required:
            required.append(param.name)

    if tool.request_body_schema is not None:
        body = dict(tool.request_body_schema)
        body.setdefault("description", "Request body (JSON).")
        properties["body"] = body
        if tool.request_body_required:
            required.append("body")

    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema
