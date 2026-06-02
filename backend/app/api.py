"""Management REST API used by the UI (mounted under /api)."""
from __future__ import annotations

import json
import uuid
from typing import Any

import httpx
import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from . import audit, mcp_runtime, net, security, storage
from .generator import generate_catalog, slugify
from .models import Catalog

# Every management route requires the admin token (no-op if SETHU_ADMIN_TOKEN unset).
router = APIRouter(dependencies=[Depends(security.require_admin)])

_SECRET_FIELDS = ("api_key_value", "bearer_token", "password")


def _mask(catalog: Catalog) -> Catalog:
    """Return a copy safe to send to the UI: secrets blanked, markers kept."""
    clone = catalog.model_copy(deep=True)
    clone.auth.api_key_set = bool(clone.auth.api_key_value)
    clone.auth.bearer_set = bool(clone.auth.bearer_token)
    clone.auth.password_set = bool(clone.auth.password)
    clone.auth.api_key_value = ""
    clone.auth.bearer_token = ""
    clone.auth.password = ""
    return clone


def _merge_secrets(incoming: Catalog, existing: Catalog | None) -> None:
    """Secrets are write-only: a blank incoming field keeps the stored value."""
    if existing is None:
        return
    for field in _SECRET_FIELDS:
        if not getattr(incoming.auth, field):
            setattr(incoming.auth, field, getattr(existing.auth, field))


def _load_spec(content: str) -> dict:
    content = content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Empty spec.")
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise HTTPException(
            status_code=400, detail=f"Could not parse spec as JSON or YAML: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Spec did not parse to an object.")
    return data


class ParseRequest(BaseModel):
    content: str = ""
    url: str = ""


@router.post("/parse", response_model=Catalog)
async def parse_spec(req: ParseRequest) -> Catalog:
    """Parse a spec into a *draft* catalog (not persisted). Accepts raw content or a URL."""
    content = req.content
    if req.url:
        try:
            net.validate_url(req.url)
        except net.BlockedHostError as exc:
            raise HTTPException(
                status_code=400, detail=f"Refused to fetch spec URL: {exc}"
            ) from exc
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                resp = await client.get(req.url)
                resp.raise_for_status()
                content = resp.text
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=400, detail=f"Could not fetch spec URL: {exc}"
            ) from exc
    spec = _load_spec(content)
    catalog = generate_catalog(spec)
    if not catalog.tools:
        raise HTTPException(status_code=400, detail="No operations found in the spec.")
    return catalog


@router.get("/catalogs", response_model=list[Catalog])
def list_catalogs() -> list[Catalog]:
    return [_mask(c) for c in storage.list_all()]


@router.get("/catalogs/{catalog_id}", response_model=Catalog)
def get_catalog(catalog_id: str) -> Catalog:
    catalog = storage.get(catalog_id)
    if catalog is None:
        raise HTTPException(status_code=404, detail="Catalog not found.")
    return _mask(catalog)


def _ensure_unique_slug(catalog: Catalog) -> None:
    base = slugify(catalog.slug or catalog.name)
    slug = base
    counter = 2
    existing = {c.slug for c in storage.list_all() if c.id != catalog.id}
    while slug in existing:
        slug = f"{base}-{counter}"
        counter += 1
    catalog.slug = slug


@router.post("/catalogs", response_model=Catalog)
def create_catalog(catalog: Catalog) -> Catalog:
    if not catalog.id:
        catalog.id = uuid.uuid4().hex[:8]
    _ensure_unique_slug(catalog)
    return _mask(storage.save(catalog))


@router.put("/catalogs/{catalog_id}", response_model=Catalog)
def update_catalog(catalog_id: str, catalog: Catalog) -> Catalog:
    existing = storage.get(catalog_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Catalog not found.")
    catalog.id = catalog_id
    _merge_secrets(catalog, existing)
    _ensure_unique_slug(catalog)
    return _mask(storage.save(catalog))


@router.delete("/catalogs/{catalog_id}")
def delete_catalog(catalog_id: str) -> dict[str, bool]:
    if not storage.delete(catalog_id):
        raise HTTPException(status_code=404, detail="Catalog not found.")
    return {"deleted": True}


@router.post("/catalogs/{catalog_id}/publish", response_model=Catalog)
def publish_catalog(catalog_id: str) -> Catalog:
    catalog = storage.get(catalog_id)
    if catalog is None:
        raise HTTPException(status_code=404, detail="Catalog not found.")
    catalog.published = True
    return _mask(storage.save(catalog))


@router.post("/catalogs/{catalog_id}/unpublish", response_model=Catalog)
def unpublish_catalog(catalog_id: str) -> Catalog:
    catalog = storage.get(catalog_id)
    if catalog is None:
        raise HTTPException(status_code=404, detail="Catalog not found.")
    catalog.published = False
    return _mask(storage.save(catalog))


class TestToolRequest(BaseModel):
    arguments: dict[str, Any] = {}


@router.post("/catalogs/{catalog_id}/test/{tool_id}")
async def test_tool(catalog_id: str, tool_id: str, req: TestToolRequest) -> dict[str, str]:
    """Invoke a single tool against the live backend (for the UI's Test button)."""
    catalog = storage.get(catalog_id)
    if catalog is None:
        raise HTTPException(status_code=404, detail="Catalog not found.")
    tool = next((t for t in catalog.tools if t.id == tool_id), None)
    if tool is None:
        raise HTTPException(status_code=404, detail="Tool not found.")
    result = await mcp_runtime.invoke(catalog, tool, req.arguments, source="test")
    return {"result": result}


@router.get("/mcp-info")
def mcp_info() -> dict[str, Any]:
    """Summary of what the hosted MCP endpoint currently exposes."""
    published = storage.list_published()
    tools = []
    for catalog in published:
        for tool in catalog.tools:
            if tool.enabled:
                tools.append(
                    {
                        "name": f"{catalog.slug}__{tool.tool_name}",
                        "catalog": catalog.name,
                        "method": tool.method.upper(),
                        "path": tool.path,
                        "destructive": tool.destructive,
                    }
                )
    return {
        "endpoint": "/mcp",
        "published_catalogs": len(published),
        "tool_count": len(tools),
        "tools": tools,
        **security.auth_status(),
    }


@router.get("/audit")
def get_audit(limit: int = 100) -> dict[str, Any]:
    """Recent proxied tool calls (newest first)."""
    return {"entries": audit.tail(limit)}
