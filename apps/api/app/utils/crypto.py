"""AES-256 encryption helpers using AESGCM."""

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..exceptions import ConfigurationError

_key_b64 = os.getenv("ENCRYPTION_KEY")
if not _key_b64:
    raise ConfigurationError("ENCRYPTION_KEY not configured")
_KEY = base64.b64decode(_key_b64)


def encrypt(plain: str) -> str:
    nonce = os.urandom(12)
    aes = AESGCM(_KEY)
    cipher = aes.encrypt(nonce, plain.encode(), None)
    return base64.b64encode(nonce + cipher).decode()


def decrypt(token: str) -> str:
    raw = base64.b64decode(token)
    nonce, cipher = raw[:12], raw[12:]
    aes = AESGCM(_KEY)
    plain = aes.decrypt(nonce, cipher, None)
    return plain.decode()
