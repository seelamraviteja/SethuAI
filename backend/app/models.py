"""Pydantic data models for the MCP Adapter.

A *Catalog* is the central artifact: it is produced by the generator from an
OpenAPI spec, refined by a human in the UI, and then interpreted at runtime by
the MCP server. We deliberately store the catalog as data (not generated code)
so a single runtime can serve many APIs and pick up edits live.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ParamDef(BaseModel):
    """A single OpenAPI operation parameter (path / query / header / cookie)."""

    name: str
    location: str = "query"  # one of: path | query | header | cookie
    required: bool = False
    json_schema: dict[str, Any] = Field(default_factory=dict)
    description: str = ""


class AuthConfig(BaseModel):
    """Service-account auth applied to every proxied request for a catalog."""

    type: str = "none"  # none | apiKey | bearer | basic

    # apiKey
    api_key_name: str = ""  # header or query param name
    api_key_in: str = "header"  # header | query
    api_key_value: str = ""

    # bearer
    bearer_token: str = ""

    # basic
    username: str = ""
    password: str = ""

    # Response-only markers: tell the UI a secret exists without revealing it.
    # Secrets are write-only from the UI — never sent back in API responses.
    api_key_set: bool = False
    bearer_set: bool = False
    password_set: bool = False


class ToolDef(BaseModel):
    """One OpenAPI operation, exposed as one MCP tool."""

    id: str
    tool_name: str
    description: str = ""
    enabled: bool = True
    destructive: bool = False
    method: str
    path: str
    params: list[ParamDef] = Field(default_factory=list)
    request_body_schema: Optional[dict[str, Any]] = None
    request_body_required: bool = False


class Catalog(BaseModel):
    """A generated + human-reviewed set of tools for a single API."""

    id: str = ""
    name: str = "Untitled API"
    description: str = ""
    base_url: str = ""
    slug: str = ""  # used as the MCP tool-name prefix; must be unique
    auth: AuthConfig = Field(default_factory=AuthConfig)
    tools: list[ToolDef] = Field(default_factory=list)
    published: bool = False
