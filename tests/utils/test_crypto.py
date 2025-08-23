"""Tests for encryption helpers."""

import base64
import importlib
import os

import pytest
from hypothesis import given
from hypothesis import strategies as st

from apps.api.app.exceptions import ConfigurationError


@given(st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=100))
def test_encrypt_decrypt_roundtrip(value: str) -> None:
    """Should return original text after encrypt/decrypt cycle."""
    os.environ["ENCRYPTION_KEY"] = base64.b64encode(b"0" * 32).decode()
    import apps.api.app.utils.crypto as crypto

    importlib.reload(crypto)

    token = crypto.encrypt(value)
    result = crypto.decrypt(token)

    assert result == value


def test_missing_key_raises_configuration_error() -> None:
    """Should raise ConfigurationError when ENCRYPTION_KEY is absent."""
    os.environ.pop("ENCRYPTION_KEY", None)
    import apps.api.app.utils.crypto as crypto

    with pytest.raises(ConfigurationError):
        importlib.reload(crypto)
