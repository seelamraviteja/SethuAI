"""Simple JSON-file persistence for catalogs.

One file per catalog under ``data/catalogs/<id>.json``. This is intentionally
lightweight for a local-first app; swap for a DB in production. Auth secrets are
encrypted at rest via :mod:`app.crypto` before being written here.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import crypto
from .models import Catalog

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "catalogs"

# Auth fields that must be encrypted before hitting disk.
_SECRET_FIELDS = ("api_key_value", "bearer_token", "password")


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _path(catalog_id: str) -> Path:
    return DATA_DIR / f"{catalog_id}.json"


def save(catalog: Catalog) -> Catalog:
    _ensure_dir()
    data = catalog.model_dump()
    for field in _SECRET_FIELDS:
        data["auth"][field] = crypto.encrypt(data["auth"].get(field, ""))
    _path(catalog.id).write_text(json.dumps(data, indent=2))
    return catalog


def _decrypt(catalog: Catalog) -> Catalog:
    auth = catalog.auth
    auth.api_key_value = crypto.decrypt(auth.api_key_value)
    auth.bearer_token = crypto.decrypt(auth.bearer_token)
    auth.password = crypto.decrypt(auth.password)
    # Recompute the write-only markers from the decrypted truth.
    auth.api_key_set = bool(auth.api_key_value)
    auth.bearer_set = bool(auth.bearer_token)
    auth.password_set = bool(auth.password)
    return catalog


def get(catalog_id: str) -> Catalog | None:
    path = _path(catalog_id)
    if not path.exists():
        return None
    return _decrypt(Catalog.model_validate_json(path.read_text()))


def list_all() -> list[Catalog]:
    _ensure_dir()
    catalogs = []
    for path in sorted(DATA_DIR.glob("*.json")):
        try:
            catalogs.append(_decrypt(Catalog.model_validate_json(path.read_text())))
        except Exception:
            continue
    return catalogs


def list_published() -> list[Catalog]:
    return [c for c in list_all() if c.published]


def delete(catalog_id: str) -> bool:
    path = _path(catalog_id)
    if path.exists():
        path.unlink()
        return True
    return False
