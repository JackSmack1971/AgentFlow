"""AuthService password hashing/verification tests."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pyotp
import pytest

from apps.api.app.exceptions import PasswordHashError
from apps.api.app.services.auth import AuthService


@pytest.mark.asyncio
async def test_register_user_uses_async_hash(monkeypatch: pytest.MonkeyPatch) -> None:
    db = SimpleNamespace(add=Mock(), commit=AsyncMock(), rollback=AsyncMock())
    service = AuthService(db)
    hasher = AsyncMock(return_value="hashed")
    monkeypatch.setattr("apps.api.app.services.auth.hash_password_async", hasher)
    secret = await service.register_user("a@b.com", "Password1!")
    hasher.assert_awaited_once_with("Password1!")
    assert secret


@pytest.mark.asyncio
async def test_register_user_hash_error(monkeypatch: pytest.MonkeyPatch) -> None:
    db = SimpleNamespace(add=Mock(), commit=AsyncMock(), rollback=AsyncMock())
    service = AuthService(db)
    hasher = AsyncMock(side_effect=PasswordHashError("boom"))
    monkeypatch.setattr("apps.api.app.services.auth.hash_password_async", hasher)
    with pytest.raises(PasswordHashError):
        await service.register_user("a@b.com", "Password1!")
    hasher.assert_awaited_once()


@pytest.mark.asyncio
async def test_authenticate_user_uses_async_verify(monkeypatch: pytest.MonkeyPatch) -> None:
    service = AuthService(AsyncMock())
    user = SimpleNamespace(hashed_password="hashed", otp_secret="secret")
    service._get_user = AsyncMock(return_value=user)
    verifier = AsyncMock(return_value=True)
    monkeypatch.setattr("apps.api.app.services.auth.verify_password_async", verifier)
    monkeypatch.setattr(pyotp, "TOTP", lambda _: SimpleNamespace(verify=Mock(return_value=True)))
    result = await service.authenticate_user("a@b.com", "Password1!", "0000")
    verifier.assert_awaited_once_with("Password1!", "hashed")
    assert result is True


@pytest.mark.asyncio
async def test_authenticate_user_verify_error(monkeypatch: pytest.MonkeyPatch) -> None:
    service = AuthService(AsyncMock())
    user = SimpleNamespace(hashed_password="hashed", otp_secret="secret")
    service._get_user = AsyncMock(return_value=user)
    verifier = AsyncMock(side_effect=PasswordHashError("boom"))
    monkeypatch.setattr("apps.api.app.services.auth.verify_password_async", verifier)
    monkeypatch.setattr(pyotp, "TOTP", lambda _: SimpleNamespace(verify=Mock(return_value=True)))
    with pytest.raises(PasswordHashError):
        await service.authenticate_user("a@b.com", "Password1!", "0000")
    verifier.assert_awaited_once()

