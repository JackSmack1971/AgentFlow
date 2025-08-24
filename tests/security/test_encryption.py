"""Security tests for encryption utilities.

Tests cover:
- OTP secret encryption/decryption
- Key generation and management
- Encryption key rotation
- Data integrity and confidentiality
- Encryption performance and security boundaries
"""

import base64
import os
import pytest
from cryptography.fernet import Fernet, InvalidToken

from apps.api.app.utils.encryption import (
    EncryptionManager,
    encrypt_otp_secret,
    decrypt_otp_secret,
    get_encryption_manager
)


class TestEncryptionManager:
    """Test the EncryptionManager class."""

    def test_encryption_manager_initialization_with_key(self):
        """Test initialization with a provided key."""
        key = "test_key_32_chars_12345678901234567890"
        manager = EncryptionManager(key)

        assert manager.fernet is not None
        assert isinstance(manager.fernet, Fernet)

    def test_encryption_manager_initialization_from_env(self):
        """Test initialization using environment variable."""
        test_key = "env_test_key_32_chars_1234567890"
        os.environ["FERNET_KEY"] = test_key

        try:
            manager = EncryptionManager()
            assert manager.fernet is not None
        finally:
            del os.environ["FERNET_KEY"]

    def test_encryption_manager_missing_key_error(self):
        """Test error when no key is provided."""
        if "FERNET_KEY" in os.environ:
            del os.environ["FERNET_KEY"]

        with pytest.raises(ValueError, match="FERNET_KEY environment variable is required"):
            EncryptionManager()

    def test_key_generation_random(self):
        """Test random key generation."""
        key = EncryptionManager.generate_key()

        assert key is not None
        assert len(key) > 32  # Base64 encoded 32-byte key

        # Should be valid base64
        decoded = base64.urlsafe_b64decode(key)
        assert len(decoded) == 32  # 32 bytes

    def test_key_generation_from_password(self):
        """Test key generation from password."""
        password = "test_password_123"
        salt = b"salt_1234567890123456"  # 16 bytes

        key1 = EncryptionManager.generate_key(password, salt)
        key2 = EncryptionManager.generate_key(password, salt)

        # Same password and salt should produce same key
        assert key1 == key2

        # Different salt should produce different key
        key3 = EncryptionManager.generate_key(password, b"different_salt_123456")
        assert key1 != key3

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encrypt/decrypt preserves data."""
        key = "test_key_32_chars_12345678901234567890"
        manager = EncryptionManager(key)

        test_data = "This is sensitive data to encrypt"

        # Encrypt
        encrypted = manager.encrypt(test_data)
        assert encrypted != test_data
        assert isinstance(encrypted, str)

        # Decrypt
        decrypted = manager.decrypt(encrypted)
        assert decrypted == test_data

    def test_encrypt_empty_string(self):
        """Test encryption of empty string."""
        key = "test_key_32_chars_12345678901234567890"
        manager = EncryptionManager(key)

        encrypted = manager.encrypt("")
        assert encrypted == ""

        decrypted = manager.decrypt(encrypted)
        assert decrypted == ""

    def test_decrypt_invalid_data(self):
        """Test decryption of invalid data."""
        key = "test_key_32_chars_12345678901234567890"
        manager = EncryptionManager(key)

        with pytest.raises(ValueError):
            manager.decrypt("invalid_encrypted_data")

    def test_different_keys_produce_different_results(self):
        """Test that different keys produce different encrypted results."""
        key1 = "test_key_32_chars_12345678901234567890"
        key2 = "different_key_32_chars_123456789012345"

        manager1 = EncryptionManager(key1)
        manager2 = EncryptionManager(key2)

        test_data = "Test data for encryption"

        encrypted1 = manager1.encrypt(test_data)
        encrypted2 = manager2.encrypt(test_data)

        assert encrypted1 != encrypted2

        # Each manager should only be able to decrypt its own data
        assert manager1.decrypt(encrypted1) == test_data
        assert manager2.decrypt(encrypted2) == test_data

        with pytest.raises(ValueError):
            manager1.decrypt(encrypted2)

        with pytest.raises(ValueError):
            manager2.decrypt(encrypted1)


class TestOTPEncryption:
    """Test OTP secret encryption functions."""

    def test_otp_secret_encrypt_decrypt(self):
        """Test OTP secret encryption/decryption functions."""
        test_secret = "JBSWY3DPEHPK3PXP"  # Example TOTP secret

        # Set test key
        os.environ["FERNET_KEY"] = "test_key_32_chars_12345678901234567890"

        try:
            # Encrypt
            encrypted = encrypt_otp_secret(test_secret)
            assert encrypted != test_secret
            assert isinstance(encrypted, str)

            # Decrypt
            decrypted = decrypt_otp_secret(encrypted)
            assert decrypted == test_secret

        finally:
            del os.environ["FERNET_KEY"]

    def test_otp_secret_empty_string(self):
        """Test OTP secret encryption with empty string."""
        os.environ["FERNET_KEY"] = "test_key_32_chars_12345678901234567890"

        try:
            encrypted = encrypt_otp_secret("")
            assert encrypted == ""

            decrypted = decrypt_otp_secret("")
            assert decrypted == ""

        finally:
            del os.environ["FERNET_KEY"]


class TestGlobalEncryptionManager:
    """Test the global encryption manager instance."""

    def test_get_encryption_manager_singleton(self):
        """Test that get_encryption_manager returns singleton instance."""
        os.environ["FERNET_KEY"] = "test_key_32_chars_12345678901234567890"

        try:
            manager1 = get_encryption_manager()
            manager2 = get_encryption_manager()

            assert manager1 is manager2  # Same instance

        finally:
            del os.environ["FERNET_KEY"]

    def test_encryption_manager_thread_safety(self):
        """Test that encryption manager is thread-safe."""
        import threading
        import time

        os.environ["FERNET_KEY"] = "test_key_32_chars_12345678901234567890"

        try:
            results = []

            def worker():
                manager = get_encryption_manager()
                test_data = f"Thread {threading.current_thread().ident}"
                encrypted = manager.encrypt(test_data)
                decrypted = manager.decrypt(encrypted)
                results.append((test_data, decrypted))

            # Create multiple threads
            threads = []
            for _ in range(5):
                thread = threading.Thread(target=worker)
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # Verify all operations succeeded
            assert len(results) == 5
            for original, decrypted in results:
                assert original == decrypted

        finally:
            del os.environ["FERNET_KEY"]


class TestEncryptionSecurity:
    """Test encryption security properties."""

    def test_encryption_entropy(self):
        """Test that encryption produces high entropy output."""
        key = "test_key_32_chars_12345678901234567890"
        manager = EncryptionManager(key)

        test_data = "The same input data"
        encrypted_results = set()

        # Encrypt the same data multiple times
        for _ in range(100):
            encrypted = manager.encrypt(test_data)
            encrypted_results.add(encrypted)

        # Each encryption should produce different ciphertext (due to IV)
        assert len(encrypted_results) == 100

    def test_key_compromise_resistance(self):
        """Test behavior when key is compromised."""
        key1 = "test_key_32_chars_12345678901234567890"
        key2 = "compromised_key_32_chars_1234567890"

        manager1 = EncryptionManager(key1)
        manager2 = EncryptionManager(key2)

        test_data = "Sensitive information"

        # Encrypt with original key
        encrypted = manager1.encrypt(test_data)

        # Should not be decryptable with different key
        with pytest.raises(ValueError):
            manager2.decrypt(encrypted)

    def test_encryption_timing_attack_resistance(self):
        """Test that encryption/decryption timing is consistent."""
        import time

        key = "test_key_32_chars_12345678901234567890"
        manager = EncryptionManager(key)

        test_data = "A" * 1000  # Same length data

        # Time multiple encryptions
        encrypt_times = []
        for _ in range(100):
            start = time.perf_counter()
            manager.encrypt(test_data)
            end = time.perf_counter()
            encrypt_times.append(end - start)

        # Timing should be relatively consistent
        avg_time = sum(encrypt_times) / len(encrypt_times)
        max_deviation = max(abs(t - avg_time) for t in encrypt_times)

        # Max deviation should be reasonable (< 50% of average)
        assert max_deviation < avg_time * 0.5

    def test_large_data_encryption(self):
        """Test encryption of large data."""
        key = "test_key_32_chars_12345678901234567890"
        manager = EncryptionManager(key)

        # Test with 1MB of data
        large_data = "A" * (1024 * 1024)

        # Should handle large data without issues
        encrypted = manager.encrypt(large_data)
        assert len(encrypted) > len(large_data)  # Encrypted data is larger

        decrypted = manager.decrypt(encrypted)
        assert decrypted == large_data


class TestEncryptionErrorHandling:
    """Test encryption error handling."""

    def test_decrypt_corrupted_data(self):
        """Test decryption of corrupted encrypted data."""
        key = "test_key_32_chars_12345678901234567890"
        manager = EncryptionManager(key)

        # Encrypt some data
        original = "Test data"
        encrypted = manager.encrypt(original)

        # Corrupt the encrypted data
        corrupted = encrypted[:-5] + "corrupt"

        with pytest.raises(ValueError):
            manager.decrypt(corrupted)

    def test_decrypt_wrong_key(self):
        """Test decryption with wrong key."""
        key1 = "test_key_32_chars_12345678901234567890"
        key2 = "different_key_32_chars_123456789012345"

        manager1 = EncryptionManager(key1)
        manager2 = EncryptionManager(key2)

        original = "Test data"
        encrypted = manager1.encrypt(original)

        with pytest.raises(ValueError):
            manager2.decrypt(encrypted)

    def test_encrypt_none_data(self):
        """Test encryption of None data."""
        key = "test_key_32_chars_12345678901234567890"
        manager = EncryptionManager(key)

        with pytest.raises(AttributeError):
            manager.encrypt(None)

    def test_decrypt_none_data(self):
        """Test decryption of None data."""
        key = "test_key_32_chars_12345678901234567890"
        manager = EncryptionManager(key)

        with pytest.raises(AttributeError):
            manager.decrypt(None)


class TestEncryptionIntegration:
    """Test encryption integration with other components."""

    def test_encryption_with_user_model(self, db_session, test_user):
        """Test encryption integration with User model."""
        user = test_user["user"]
        original_secret = "JBSWY3DPEHPK3PXP"

        # Set OTP secret (should be encrypted)
        user.set_otp_secret(original_secret)

        # Verify it's encrypted in the database
        assert user.otp_secret != original_secret

        # Verify we can decrypt it back
        decrypted_secret = user.get_otp_secret()
        assert decrypted_secret == original_secret

        # Verify database persistence
        db_session.refresh(user)
        assert user.get_otp_secret() == original_secret

    def test_encryption_key_rotation_simulation(self):
        """Test simulation of encryption key rotation."""
        old_key = "old_key_32_chars_12345678901234567890"
        new_key = "new_key_32_chars_12345678901234567890"

        old_manager = EncryptionManager(old_key)
        new_manager = EncryptionManager(new_key)

        test_data = "Data to re-encrypt"

        # Encrypt with old key
        old_encrypted = old_manager.encrypt(test_data)

        # Decrypt with old key
        decrypted = old_manager.decrypt(old_encrypted)
        assert decrypted == test_data

        # Re-encrypt with new key
        new_encrypted = new_manager.encrypt(decrypted)

        # Should not be decryptable with old key
        with pytest.raises(ValueError):
            old_manager.decrypt(new_encrypted)

        # Should be decryptable with new key
        new_decrypted = new_manager.decrypt(new_encrypted)
        assert new_decrypted == test_data

    def test_encryption_in_concurrent_environment(self):
        """Test encryption behavior in concurrent environment."""
        import asyncio

        key = "test_key_32_chars_12345678901234567890"
        manager = EncryptionManager(key)

        async def encrypt_task(data):
            encrypted = manager.encrypt(data)
            decrypted = manager.decrypt(encrypted)
            return data == decrypted

        async def run_concurrent_tasks():
            tasks = []
            for i in range(10):
                task = encrypt_task(f"Data {i}")
                tasks.append(task)

            results = await asyncio.gather(*tasks)
            return all(results)

        # Run concurrent encryption/decryption tasks
        success = asyncio.run(run_concurrent_tasks())
        assert success is True


class TestEncryptionCompliance:
    """Test encryption compliance with security standards."""

    def test_fernet_key_length(self):
        """Test that Fernet keys meet length requirements."""
        # Generate multiple keys and verify length
        for _ in range(10):
            key = EncryptionManager.generate_key()
            decoded = base64.urlsafe_b64decode(key)
            assert len(decoded) == 32  # Fernet requires 32-byte keys

    def test_encryption_algorithm_correctness(self):
        """Test that we're using the correct encryption algorithm."""
        key = "test_key_32_chars_12345678901234567890"
        manager = EncryptionManager(key)

        # Verify we're using Fernet (AES-128-CBC with HMAC-SHA256)
        assert hasattr(manager.fernet, 'encrypt')
        assert hasattr(manager.fernet, 'decrypt')

        # Test with known test vectors if available
        test_data = "Known test data"
        encrypted = manager.encrypt(test_data)

        # Should be base64 encoded
        assert all(c in base64.urlsafe_b64encode(b'').decode() for c in encrypted)

    def test_no_plaintext_storage(self):
        """Test that sensitive data is never stored in plaintext."""
        key = "test_key_32_chars_12345678901234567890"
        manager = EncryptionManager(key)

        sensitive_data = "SuperSecretPassword123"

        # Encrypt
        encrypted = manager.encrypt(sensitive_data)

        # Encrypted data should not contain the original data
        assert sensitive_data not in encrypted

        # Encrypted data should be different from original
        assert encrypted != sensitive_data

        # Should be able to decrypt back to original
        decrypted = manager.decrypt(encrypted)
        assert decrypted == sensitive_data