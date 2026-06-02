import pytest

from app import net


def test_disabled_allows_everything(monkeypatch):
    monkeypatch.setenv("SETHU_BLOCK_PRIVATE_HOSTS", "0")
    net.validate_url("http://127.0.0.1:8080/x")  # no raise


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/x",
        "http://localhost/x",
        "http://169.254.169.254/latest/meta-data",  # cloud metadata
        "http://10.0.0.5/x",
        "http://192.168.1.1/x",
    ],
)
def test_blocks_internal_targets(monkeypatch, url):
    monkeypatch.setenv("SETHU_BLOCK_PRIVATE_HOSTS", "1")
    with pytest.raises(net.BlockedHostError):
        net.validate_url(url)


def test_allows_public_literal_ip(monkeypatch):
    monkeypatch.setenv("SETHU_BLOCK_PRIVATE_HOSTS", "1")
    net.validate_url("http://8.8.8.8/x")  # public, literal — no DNS, no raise


def test_rejects_non_http_scheme(monkeypatch):
    monkeypatch.setenv("SETHU_BLOCK_PRIVATE_HOSTS", "1")
    with pytest.raises(net.BlockedHostError):
        net.validate_url("file:///etc/passwd")


def test_default_follows_mcp_token(monkeypatch):
    monkeypatch.delenv("SETHU_BLOCK_PRIVATE_HOSTS", raising=False)
    monkeypatch.delenv("SETHU_MCP_TOKEN", raising=False)
    net.validate_url("http://127.0.0.1/x")  # open mode: allowed

    monkeypatch.setenv("SETHU_MCP_TOKEN", "secret")
    with pytest.raises(net.BlockedHostError):
        net.validate_url("http://127.0.0.1/x")  # protected mode: enforced
