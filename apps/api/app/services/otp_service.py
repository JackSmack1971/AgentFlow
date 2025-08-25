"""OTP (One-Time Password) service with encryption for secure storage and verification."""

import secrets
import string
from datetime import datetime, timedelta
from typing import Optional

from ..core.cache import get_cache
from ..exceptions import TokenError
from ..utils.encryption import get_encryption_manager


class OTPService:
    """Service for generating, storing, and verifying OTP tokens with encryption."""

    def __init__(self, otp_length: int = 6, ttl_minutes: int = 10):
        """
        Initialize OTP service.

        Args:
            otp_length: Length of generated OTP (default 6 digits)
            ttl_minutes: Time-to-live for OTP in minutes (default 10)
        """
        self.otp_length = otp_length
        self.ttl_minutes = ttl_minutes
        self.cache = get_cache()
        self.encryption_manager = get_encryption_manager()

    def generate_otp(self) -> str:
        """
        Generate a secure random OTP.

        Returns:
            str: Generated OTP string
        """
        characters = string.digits
        return ''.join(secrets.choice(characters) for _ in range(self.otp_length))

    def _get_otp_key(self, identifier: str) -> str:
        """Generate cache key for OTP storage."""
        return f"otp:{identifier}"

    async def store_otp(self, identifier: str, otp: str) -> bool:
        """
        Store encrypted OTP for identifier.

        Args:
            identifier: Unique identifier (e.g., email, phone)
            otp: OTP to store

        Returns:
            bool: True if stored successfully
        """
        try:
            # Encrypt the OTP before storing
            encrypted_otp = self.encryption_manager.encrypt(otp)

            # Store with TTL
            ttl_seconds = self.ttl_minutes * 60
            await self.cache.set(
                self._get_otp_key(identifier),
                encrypted_otp,
                ttl=ttl_seconds
            )
            return True

        except Exception as e:
            print(f"Failed to store OTP for {identifier}: {e}")
            return False

    async def verify_otp(self, identifier: str, otp: str) -> bool:
        """
        Verify OTP for identifier.

        Args:
            identifier: Unique identifier
            otp: OTP to verify

        Returns:
            bool: True if OTP is valid
        """
        try:
            # Get encrypted OTP from cache
            encrypted_otp = await self.cache.get(self._get_otp_key(identifier))
            if not encrypted_otp:
                return False

            # Decrypt and compare
            stored_otp = self.encryption_manager.decrypt(encrypted_otp)
            return secrets.compare_digest(stored_otp, otp)

        except Exception as e:
            print(f"Failed to verify OTP for {identifier}: {e}")
            return False

    async def invalidate_otp(self, identifier: str) -> bool:
        """
        Invalidate OTP for identifier.

        Args:
            identifier: Unique identifier

        Returns:
            bool: True if invalidated successfully
        """
        try:
            await self.cache.client.delete(self._get_otp_key(identifier))
            return True
        except Exception as e:
            print(f"Failed to invalidate OTP for {identifier}: {e}")
            return False

    async def generate_and_store_otp(self, identifier: str) -> str:
        """
        Generate and store a new OTP for identifier.

        Args:
            identifier: Unique identifier

        Returns:
            str: Generated OTP
        """
        otp = self.generate_otp()
        success = await self.store_otp(identifier, otp)

        if not success:
            raise TokenError("Failed to generate and store OTP")

        return otp

    async def is_otp_valid(self, identifier: str) -> bool:
        """
        Check if an OTP exists and is valid for identifier.

        Args:
            identifier: Unique identifier

        Returns:
            bool: True if OTP exists and is valid
        """
        try:
            encrypted_otp = await self.cache.get(self._get_otp_key(identifier))
            return encrypted_otp is not None
        except Exception:
            return False


# Global OTP service instance
_otp_service: Optional[OTPService] = None


def get_otp_service() -> OTPService:
    """Get global OTP service instance."""
    global _otp_service
    if _otp_service is None:
        _otp_service = OTPService()
    return _otp_service


__all__ = ["OTPService", "get_otp_service"]