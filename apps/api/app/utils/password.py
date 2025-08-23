"""Password hashing helpers using bcrypt via Passlib."""

from __future__ import annotations

from passlib.context import CryptContext  # type: ignore[import-untyped]

from ..exceptions import PasswordHashError

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password with a random salt.

    Args:
        password: Plain text password.

    Returns:
        A bcrypt hashed password including the salt.

    Raises:
        PasswordHashError: If hashing fails.
    """
    try:
        return _pwd_context.hash(password)
    except Exception as exc:  # pragma: no cover - library failure
        raise PasswordHashError("Hashing failed") from exc


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a stored hash.

    Args:
        password: Plain text password to verify.
        hashed: Previously hashed password.

    Returns:
        True if the password matches, otherwise False.

    Raises:
        PasswordHashError: If verification fails.
    """
    try:
        return _pwd_context.verify(password, hashed)
    except Exception as exc:  # pragma: no cover - library failure
        raise PasswordHashError("Verification failed") from exc
