import json

from app.mcp_runtime import _build_request, _shape_response
from app.models import AuthConfig, Catalog, ParamDef, ToolDef


def _catalog(auth: AuthConfig) -> Catalog:
    return Catalog(id="c1", name="API", base_url="https://api.example.com/", slug="api", auth=auth)


def test_build_request_path_query_and_bearer():
    tool = ToolDef(
        id="t1",
        tool_name="getPet",
        method="get",
        path="/pets/{petId}",
        params=[
            ParamDef(name="petId", location="path", required=True),
            ParamDef(name="verbose", location="query"),
            ParamDef(name="X-Trace", location="header"),
        ],
    )
    catalog = _catalog(AuthConfig(type="bearer", bearer_token="tok123"))
    url, query, headers, body, httpx_auth = _build_request(
        catalog, tool, {"petId": 7, "verbose": True, "X-Trace": "abc"}
    )
    assert url == "https://api.example.com/pets/7"
    assert query == {"verbose": True}
    assert headers["X-Trace"] == "abc"
    assert headers["Authorization"] == "Bearer tok123"
    assert body is None
    assert httpx_auth is None


def test_build_request_apikey_in_query_and_basic():
    tool = ToolDef(id="t2", tool_name="op", method="post", path="/x")
    catalog = _catalog(AuthConfig(type="apiKey", api_key_name="key", api_key_in="query", api_key_value="K"))
    _, query, _, body, _ = _build_request(catalog, tool, {"body": {"a": 1}})
    assert query == {"key": "K"}
    assert body == {"a": 1}

    catalog = _catalog(AuthConfig(type="basic", username="u", password="p"))
    *_, httpx_auth = _build_request(catalog, tool, {})
    assert httpx_auth == ("u", "p")


def test_shape_response_passthrough_when_small(monkeypatch):
    monkeypatch.setenv("SETHU_MAX_RESPONSE_CHARS", "1000")
    assert _shape_response("hello", "application/json") == "hello"


def test_shape_response_truncates_json_array(monkeypatch):
    monkeypatch.setenv("SETHU_MAX_RESPONSE_CHARS", "120")
    payload = json.dumps([{"i": n, "pad": "xxxxxxxxxx"} for n in range(50)])
    shaped = _shape_response(payload, "application/json")
    head, _, note = shaped.partition("\n")
    assert "items omitted" in note
    parsed = json.loads(head)  # the kept prefix is still valid JSON
    assert isinstance(parsed, list)
    assert 0 < len(parsed) < 50


def test_shape_response_plain_text_truncation(monkeypatch):
    monkeypatch.setenv("SETHU_MAX_RESPONSE_CHARS", "10")
    shaped = _shape_response("a" * 100, "text/plain")
    assert shaped.startswith("aaaaaaaaaa")
    assert "truncated" in shaped
