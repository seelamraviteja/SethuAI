import json
from pathlib import Path

from app.generator import build_input_schema, generate_catalog, slugify
from app.models import ParamDef, ToolDef

_SAMPLE = Path(__file__).resolve().parent.parent / "sample_petstore.json"


def _sample_spec() -> dict:
    return json.loads(_SAMPLE.read_text())


def test_slugify():
    assert slugify("Swagger Petstore") == "swagger-petstore"
    assert slugify("  Hello, World!  ") == "hello-world"
    assert slugify("@@@") == "api"  # falls back when nothing survives


def test_generate_catalog_from_sample():
    catalog = generate_catalog(_sample_spec())
    assert catalog.name
    assert catalog.slug
    assert catalog.tools, "expected at least one tool from the sample spec"
    # Tool names are stable identifiers and unique.
    names = [t.tool_name for t in catalog.tools]
    assert len(names) == len(set(names))
    for t in catalog.tools:
        assert t.method in ("get", "post", "put", "patch", "delete", "head", "options")


def test_delete_marked_destructive():
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "X"},
        "paths": {"/items/{id}": {"delete": {"operationId": "deleteItem"}}},
    }
    catalog = generate_catalog(spec)
    tool = catalog.tools[0]
    assert tool.destructive is True


def test_duplicate_operation_ids_deduped():
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "X"},
        "paths": {
            "/a": {"get": {"operationId": "list"}},
            "/b": {"get": {"operationId": "list"}},
        },
    }
    names = [t.tool_name for t in generate_catalog(spec).tools]
    assert names == ["list", "list_2"]


def test_build_input_schema_marks_required():
    tool = ToolDef(
        id="t1",
        tool_name="getThing",
        method="get",
        path="/things/{id}",
        params=[
            ParamDef(name="id", location="path", required=True, json_schema={"type": "string"}),
            ParamDef(name="verbose", location="query", required=False, json_schema={"type": "boolean"}),
        ],
        request_body_schema={"type": "object"},
        request_body_required=True,
    )
    schema = build_input_schema(tool)
    assert schema["type"] == "object"
    assert set(schema["properties"]) == {"id", "verbose", "body"}
    assert set(schema["required"]) == {"id", "body"}
