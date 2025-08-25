"""RSA key management utilities."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Tuple

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

logger = logging.getLogger(__name__)


class RSAKeyError(Exception):
    """Raised when RSA key generation fails."""


async def generate_rsa_key_pair(private_path: str, public_path: str) -> Tuple[str, str]:
    """Generate RSA key pair and persist to the provided paths."""
    try:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_bytes = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_bytes = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        for path, data in ((private_path, private_bytes), (public_path, public_bytes)):
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(p.write_bytes, data)
        os.environ["JWT_PRIVATE_KEY_PATH"] = private_path
        os.environ["JWT_PUBLIC_KEY_PATH"] = public_path
        return private_path, public_path
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("RSA key generation failed", exc_info=True)
        raise RSAKeyError(str(exc)) from exc
