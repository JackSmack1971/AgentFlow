"""Encryption utilities for sensitive data using Fernet symmetric encryption."""

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionManager:
    """Manages encryption/decryption of sensitive data using Fernet."""

    def __init__(self, key: Optional[str] = None):
        """Initialize encryption manager with a key.

        Args:
            key: Base64-encoded 32-byte key. If None, uses FERNET_KEY from environment.
        """
        if key is None:
            key = os.getenv("FERNET_KEY")
            if not key:
                raise ValueError("FERNET_KEY environment variable is required")

        self.fernet = Fernet(key)

    @staticmethod
    def generate_key(password: str = None, salt: bytes = None) -> str:
        """Generate a new Fernet key from password or randomly.

        Args:
            password: Optional password to derive key from
            salt: Optional salt for key derivation

        Returns:
            Base64-encoded Fernet key
        """
        if password is None:
            # Generate random key
            return base64.urlsafe_b64encode(os.urandom(32)).decode()

        if salt is None:
            salt = os.urandom(16)

        # Derive key from password using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode())).decode()
        return key

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""

        encrypted = self.fernet.encrypt(plaintext.encode())
        return encrypted.decode()

    def decrypt(self, encrypted_text: str) -> str:
        """Decrypt encrypted string.

        Args:
            encrypted_text: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string

        Raises:
            ValueError: If decryption fails
        """
        if not encrypted_text:
            return ""

        try:
            decrypted = self.fernet.decrypt(encrypted_text.encode())
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {e}")


# Global encryption manager instance
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """Get or create global encryption manager instance."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


def encrypt_otp_secret(otp_secret: str) -> str:
    """Encrypt an OTP secret for storage."""
    return get_encryption_manager().encrypt(otp_secret)


def decrypt_otp_secret(encrypted_secret: str) -> str:
    """Decrypt an OTP secret from storage."""
    return get_encryption_manager().decrypt(encrypted_secret)