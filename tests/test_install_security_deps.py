import asyncio
import subprocess
from subprocess import CalledProcessError, CompletedProcess

import pytest

from scripts.install_security_deps import (
    DependencyInstallationError,
    install_fastapi_guard,
)


@pytest.mark.asyncio
async def test_install_fastapi_guard_respects_env_version(monkeypatch) -> None:
    """Should install the version specified in FASTAPI_GUARD_VERSION."""
    calls: dict[str, list[str]] = {}

    def fake_run(cmd, capture_output=True, text=True, check=True):  # type: ignore[override]
        calls.setdefault("cmds", []).append(cmd)
        return CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setenv("FASTAPI_GUARD_VERSION", "4.0.3")
    monkeypatch.setattr(subprocess, "run", fake_run)

    await install_fastapi_guard()

    assert any("fastapi-guard==4.0.3" in c for c in calls["cmds"])  # version used


@pytest.mark.asyncio
async def test_install_fastapi_guard_logs_error_on_failure(monkeypatch, caplog) -> None:
    """Should log an error and raise when installation fails."""
    async def dummy_sleep(_: float) -> None:
        pass

    def failing_run(*args, **kwargs):  # type: ignore[override]
        raise CalledProcessError(1, "pip", stderr="boom")

    monkeypatch.setenv("FASTAPI_GUARD_VERSION", "4.0.3")
    monkeypatch.setattr(subprocess, "run", failing_run)
    monkeypatch.setattr(asyncio, "sleep", dummy_sleep)

    with caplog.at_level("ERROR"), pytest.raises(DependencyInstallationError) as exc:
        await install_fastapi_guard()

    assert "fastapi-guard==4.0.3" in str(exc.value)
    assert "Attempt" in caplog.text

