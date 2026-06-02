from app import crypto


def test_roundtrip():
    token = crypto.encrypt("hunter2")
    assert token.startswith("enc:")
    assert "hunter2" not in token
    assert crypto.decrypt(token) == "hunter2"


def test_empty_string():
    assert crypto.encrypt("") == ""
    assert crypto.decrypt("") == ""


def test_legacy_plaintext_passthrough():
    # Values without the enc: prefix are returned unchanged (migration path).
    assert crypto.decrypt("plain") == "plain"


def test_corrupt_token_returns_empty():
    assert crypto.decrypt("enc:not-a-real-token") == ""
