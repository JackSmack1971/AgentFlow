"""Tests for encryption utilities and User model security enhancements."""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from apps.api.app.db.models import User
from apps.api.app.utils.encryption import (
    EncryptionManager,
    encrypt_otp_secret,
    decrypt_otp_secret,
    get_encryption_manager
)


class TestEncryptionManager:
    """Test the EncryptionManager class."""

    def test_generate_key(self):
        """Test key generation."""
        key = EncryptionManager.generate_key()
        assert isinstance(key, str)
        assert len(key) > 0

        # Should be base64 encoded
        import base64
        decoded = base64.urlsafe_b64decode(key)
        assert len(decoded) == 32  # 32 bytes for AES-256

    def test_encrypt_decrypt(self):
        """Test basic encryption/decryption."""
        key = EncryptionManager.generate_key()
        manager = EncryptionManager(key)

        plaintext = "JBSWY3DPEHPK3PXP"
        encrypted = manager.encrypt(plaintext)
        decrypted = manager.decrypt(encrypted)

        assert decrypted == plaintext
        assert encrypted != plaintext

    def test_encrypt_empty_string(self):
        """Test encryption of empty string."""
        key = EncryptionManager.generate_key()
        manager = EncryptionManager(key)

        encrypted = manager.encrypt("")
        decrypted = manager.decrypt(encrypted)

        assert decrypted == ""

    def test_decrypt_invalid_data(self):
        """Test decryption of invalid data."""
        key = EncryptionManager.generate_key()
        manager = EncryptionManager(key)

        with pytest.raises(ValueError):
            manager.decrypt("invalid_encrypted_data")


class TestEncryptionUtilities:
    """Test the encryption utility functions."""

    @patch.dict(os.environ, {"FERNET_KEY": EncryptionManager.generate_key()})
    def test_encrypt_decrypt_otp_secret(self):
        """Test OTP secret encryption/decryption functions."""
        plaintext = "JBSWY3DPEHPK3PXP"
        encrypted = encrypt_otp_secret(plaintext)
        decrypted = decrypt_otp_secret(encrypted)

        assert decrypted == plaintext
        assert encrypted != plaintext

    def test_missing_fernet_key(self):
        """Test behavior when FERNET_KEY is missing."""
        # Clear the global manager instance first
        import apps.api.app.utils.encryption as enc_module
        enc_module._encryption_manager = None

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="FERNET_KEY environment variable is required"):
                get_encryption_manager()


class TestUserSecurity:
    """Test User model security enhancements."""

    @patch.dict(os.environ, {"FERNET_KEY": EncryptionManager.generate_key()})
    def test_otp_secret_encryption(self):
        """Test OTP secret encryption in User model."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password"
        )

        plaintext_secret = "JBSWY3DPEHPK3PXP"
        user.set_otp_secret(plaintext_secret)

        # The stored value should be encrypted
        assert user.otp_secret != plaintext_secret
        assert len(user.otp_secret) > len(plaintext_secret)  # Encrypted data is longer

        # But we should be able to retrieve the original
        retrieved_secret = user.get_otp_secret()
        assert retrieved_secret == plaintext_secret


    @patch.dict(os.environ, {"FERNET_KEY": EncryptionManager.generate_key()})
    def test_invalid_otp_secret_setting(self):
        """Test setting invalid OTP secret."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password"
        )

        with pytest.raises(ValueError, match="OTP secret cannot be empty"):
            user.set_otp_secret("")

    def test_account_lockout_logic(self):
        """Test account lockout functionality."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password"
        )

        # Initially not locked
        assert not user.is_account_locked()

        # Record failed logins
        for i in range(4):
            user.record_failed_login()
            assert not user.is_account_locked()  # Not locked until 5th attempt

        # 5th failed attempt should lock the account
        user.record_failed_login()
        assert user.is_account_locked()
        assert user.failed_login_attempts == 5

        # Successful login should reset
        user.record_successful_login()
        assert not user.is_account_locked()
        assert user.failed_login_attempts == 0

    def test_successful_login_tracking(self):
        """Test successful login tracking."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password"
        )

        initial_attempts = user.failed_login_attempts
        initial_lockout = user.account_locked_until

        user.record_successful_login()

        assert user.last_login is not None
        assert user.failed_login_attempts == 0
        assert user.account_locked_until is None

    def test_soft_delete_functionality(self):
        """Test soft delete functionality."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password"
        )

        # Initially not deleted
        assert not user.is_deleted
        assert user.is_active

        # Soft delete
        user.soft_delete()
        assert user.is_deleted
        assert not user.is_active
        assert user.deleted_at is not None

        # Restore
        user.restore()
        assert not user.is_deleted
        assert user.is_active
        assert user.deleted_at is None

    def test_audit_timestamps(self):
        """Test that audit timestamps are properly set."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password"
        )

        # Check that created_at is set
        assert user.created_at is not None
        assert user.updated_at is not None

        # Check that timestamps are reasonable (within last minute)
        now = datetime.utcnow()
        assert abs((now - user.created_at).total_seconds()) < 60
        assert abs((now - user.updated_at).total_seconds()) < 60


class TestUserSecurityIntegration:
    """Integration tests for User security features."""

    @patch.dict(os.environ, {"FERNET_KEY": EncryptionManager.generate_key()})
    def test_full_user_lifecycle(self):
        """Test complete user lifecycle with security features."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password"
        )

        # Set OTP secret
        otp_secret = "JBSWY3DPEHPK3PXP"
        user.set_otp_secret(otp_secret)

        # Verify encryption
        assert user.get_otp_secret() == otp_secret

        # Test login attempts
        assert not user.is_account_locked()

        # Simulate failed logins
        for i in range(5):
            user.record_failed_login()

        assert user.is_account_locked()

        # Successful login should unlock and reset
        user.record_successful_login()
        assert not user.is_account_locked()
        assert user.failed_login_attempts == 0

        # Test soft delete
        user.soft_delete()
        assert user.is_deleted
        assert not user.is_active