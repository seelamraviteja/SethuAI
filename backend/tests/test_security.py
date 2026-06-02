import pytest
from fastapi import HTTPException

from app import security


def test_open_mode_allows(monkeypatch):
    monkeypatch.delenv("SETHU_ADMIN_TOKEN", raising=False)
    # No token configured -> no exception regardless of headers.
    security.require_admin(authorization="", x_admin_token="")


def test_correct_token_accepted(monkeypatch):
    monkeypatch.setenv("SETHU_ADMIN_TOKEN", "s3cret")
    security.require_admin(authorization="Bearer s3cret", x_admin_token="")
    security.require_admin(authorization="", x_admin_token="s3cret")


def test_wrong_token_rejected(monkeypatch):
    monkeypatch.setenv("SETHU_ADMIN_TOKEN", "s3cret")
    with pytest.raises(HTTPException) as exc:
        security.require_admin(authorization="Bearer nope", x_admin_token="")
    assert exc.value.status_code == 401


def test_mcp_token_check(monkeypatch):
    monkeypatch.delenv("SETHU_MCP_TOKEN", raising=False)
    assert security.check_mcp_token("", "") is True  # open mode

    monkeypatch.setenv("SETHU_MCP_TOKEN", "mcp")
    assert security.check_mcp_token("Bearer mcp", "") is True
    assert security.check_mcp_token("", "mcp") is True
    assert security.check_mcp_token("Bearer wrong", "") is False
