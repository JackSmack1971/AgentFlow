"""Property-based tests for encryption helpers."""

import base64
import os

from hypothesis import given
from hypothesis import strategies as st

# Use deterministic key for reproducible tests
os.environ["ENCRYPTION_KEY"] = base64.b64encode(b"0" * 32).decode()

from apps.api.app.utils import crypto


@given(st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=100))
def test_encrypt_decrypt_roundtrip(value: str) -> None:
    """Should return original text after encrypt/decrypt cycle."""
    # Act
    token = crypto.encrypt(value)
    result = crypto.decrypt(token)

    # Assert
    assert result == value
