"""Symmetric encryption for secrets at rest.

Auth credentials (API keys, bearer tokens, passwords) are encrypted before they
touch disk. The key comes from ``SETHU_SECRET_KEY`` (any string — it's hashed to
a 32-byte Fernet key). For local dev, if that env var is unset we generate a key
once and persist it to ``data/.sethu_key`` so restarts can still decrypt.
"""
from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_KEYFILE = _DATA_DIR / ".sethu_key"


def _load_key() -> bytes:
    env = os.environ.get("SETHU_SECRET_KEY")
    if env:
        digest = hashlib.sha256(env.encode()).digest()
        return base64.urlsafe_b64encode(digest)
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    if _KEYFILE.exists():
        return _KEYFILE.read_bytes()
    key = Fernet.generate_key()
    _KEYFILE.write_bytes(key)
    return key


_fernet = Fernet(_load_key())

# Marker prefix so we can tell encrypted values from legacy plaintext.
_PREFIX = "enc:"


def encrypt(value: str) -> str:
    if not value:
        return ""
    return _PREFIX + _fernet.encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    if not value:
        return ""
    if not value.startswith(_PREFIX):
        return value  # legacy plaintext — return as-is
    try:
        return _fernet.decrypt(value[len(_PREFIX) :].encode()).decode()
    except InvalidToken:
        return ""
