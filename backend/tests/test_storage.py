from app import storage
from app.models import AuthConfig, Catalog


def _fresh_storage(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    storage._cache.clear()


def test_save_get_roundtrip_and_secret_encryption(monkeypatch, tmp_path):
    _fresh_storage(monkeypatch, tmp_path)
    cat = Catalog(id="abc", name="API", auth=AuthConfig(type="bearer", bearer_token="topsecret"))
    storage.save(cat)

    # On-disk file must not contain the plaintext secret.
    raw = (tmp_path / "abc.json").read_text()
    assert "topsecret" not in raw

    loaded = storage.get("abc")
    assert loaded is not None
    assert loaded.auth.bearer_token == "topsecret"
    assert loaded.auth.bearer_set is True


def test_cache_hit_returns_same_instance(monkeypatch, tmp_path):
    _fresh_storage(monkeypatch, tmp_path)
    storage.save(Catalog(id="abc", name="API"))
    first = storage.get("abc")
    second = storage.get("abc")
    assert first is second  # served from cache, not re-decrypted


def test_save_invalidates_cache(monkeypatch, tmp_path):
    _fresh_storage(monkeypatch, tmp_path)
    storage.save(Catalog(id="abc", name="Old"))
    storage.get("abc")
    storage.save(Catalog(id="abc", name="New"))
    assert storage.get("abc").name == "New"


def test_delete_removes_file_and_cache(monkeypatch, tmp_path):
    _fresh_storage(monkeypatch, tmp_path)
    storage.save(Catalog(id="abc", name="API"))
    storage.get("abc")
    assert storage.delete("abc") is True
    assert storage.get("abc") is None
    assert storage.delete("abc") is False
