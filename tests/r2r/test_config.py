import pytest

from packages.r2r.config import R2RConfig, load_config


def test_load_config_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("R2R_BASE_URL", "https://example.com")
    monkeypatch.setenv("R2R_API_KEY", "token")
    cfg = load_config(path="nonexistent.toml")
    assert cfg == R2RConfig(base_url="https://example.com", api_key="token")
