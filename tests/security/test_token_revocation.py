"""Security tests for token revocation system.

Tests cover:
- Revoking specific access tokens
- Revoking refresh tokens
- Revoking all user sessions
- Token revocation checking
- Automatic cleanup of expired tokens
- Token status updates
"""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from apps.api.app.exceptions import TokenError


class TestTokenRevocationService:
    """Test token revocation service functionality."""

    @pytest.fixture
    def revocation_service(self, redis_client):
        """Create TokenRevocationService instance for testing."""
        from apps.api.app.services.secure_jwt import TokenRevocationService

        return TokenRevocationService(redis_client, max_tokens_per_user=10)

    @pytest.mark.asyncio
    async def test_revoke_access_token_success(self, revocation_service, redis_client):
        """Test successful revocation of access token."""
        jti = "test_jti_123"
        subject = "test@example.com"

        # Revoke token
        result = await revocation_service.revoke_access_token(jti, subject, 300)

        # Verify success
        assert result is True

        # Verify token is marked as revoked
        revoked_key = f"revoked:access:{jti}"
        revoked_data = await redis_client.get(revoked_key)

        assert revoked_data is not None
        revoked_info = json.loads(revoked_data.decode())

        assert revoked_info["subject"] == subject
        assert revoked_info["reason"] == "explicit_revocation"
        assert "revoked_at" in revoked_info

    @pytest.mark.asyncio
    async def test_revoke_access_token_updates_metadata(self, revocation_service, redis_client):
        """Test that revoking access token updates metadata."""
        jti = "test_jti_456"
        subject = "test@example.com"

        # First, create token metadata
        metadata_key = f"token:metadata:{jti}"
        metadata = {
            "jti": jti,
            "subject": subject,
            "status": "active",
            "created_at": datetime.utcnow().isoformat()
        }
        await redis_client.setex(metadata_key, 3600, json.dumps(metadata))

        # Revoke token
        await revocation_service.revoke_access_token(jti, subject)

        # Verify metadata was updated
        updated_metadata = await redis_client.get(metadata_key)
        assert updated_metadata is not None

        updated_info = json.loads(updated_metadata.decode())
        assert updated_info["status"] == "revoked"
        assert "updated_at" in updated_info

    @pytest.mark.asyncio
    async def test_revoke_refresh_token_success(self, revocation_service, redis_client):
        """Test successful revocation of refresh token."""
        jti = "refresh_jti_123"
        subject = "test@example.com"

        # Revoke refresh token
        result = await revocation_service.revoke_refresh_token(jti, subject, 3600)

        # Verify success
        assert result is True

        # Verify token is marked as revoked
        revoked_key = f"revoked:refresh:{jti}"
        revoked_data = await redis_client.get(revoked_key)

        assert revoked_data is not None
        revoked_info = json.loads(revoked_data.decode())

        assert revoked_info["subject"] == subject
        assert revoked_info["token_type"] == "refresh"
        assert "revoked_at" in revoked_info

    @pytest.mark.asyncio
    async def test_revoke_user_sessions_multiple_tokens(self, revocation_service, redis_client):
        """Test revoking all sessions for a user with multiple tokens."""
        subject = "test@example.com"
        jti1 = "jti_1"
        jti2 = "jti_2"

        # Create metadata for multiple tokens
        for jti in [jti1, jti2]:
            metadata_key = f"token:metadata:{jti}"
            metadata = {
                "jti": jti,
                "subject": subject,
                "status": "active",
                "created_at": datetime.utcnow().isoformat()
            }
            await redis_client.setex(metadata_key, 3600, json.dumps(metadata))

        # Revoke all user sessions
        revoked_count = await revocation_service.revoke_user_sessions(subject)

        # Verify both tokens were revoked
        assert revoked_count == 2

        # Verify both tokens are marked as revoked
        for jti in [jti1, jti2]:
            revoked_key = f"revoked:access:{jti}"
            assert await redis_client.exists(revoked_key)

        # Verify user session revocation record
        user_key = f"user:sessions_revoked:{subject}"
        user_data = await redis_client.get(user_key)

        assert user_data is not None
        user_info = json.loads(user_data.decode())
        assert user_info["session_count"] == 2

    @pytest.mark.asyncio
    async def test_revoke_user_sessions_no_tokens(self, revocation_service, redis_client):
        """Test revoking sessions for user with no active tokens."""
        subject = "user_no_tokens@example.com"

        # Revoke sessions
        revoked_count = await revocation_service.revoke_user_sessions(subject)

        # Should return 0
        assert revoked_count == 0

        # Verify user session revocation record still created
        user_key = f"user:sessions_revoked:{subject}"
        user_data = await redis_client.get(user_key)

        assert user_data is not None
        user_info = json.loads(user_data.decode())
        assert user_info["session_count"] == 0

    @pytest.mark.asyncio
    async def test_is_token_revoked_access_token(self, revocation_service, redis_client):
        """Test checking if access token is revoked."""
        jti = "check_jti_123"

        # Initially should not be revoked
        assert await revocation_service.is_token_revoked(jti, "access") is False

        # Revoke token
        await redis_client.setex(f"revoked:access:{jti}", 300, "revoked")

        # Should now be revoked
        assert await revocation_service.is_token_revoked(jti, "access") is True

    @pytest.mark.asyncio
    async def test_is_token_revoked_refresh_token(self, revocation_service, redis_client):
        """Test checking if refresh token is revoked."""
        jti = "check_refresh_jti_123"

        # Initially should not be revoked
        assert await revocation_service.is_token_revoked(jti, "refresh") is False

        # Revoke refresh token
        await redis_client.setex(f"revoked:refresh:{jti}", 300, "revoked")

        # Should now be revoked
        assert await revocation_service.is_token_revoked(jti, "refresh") is True

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens(self, revocation_service, redis_client):
        """Test cleanup of expired tokens."""
        subject = "cleanup_test@example.com"
        expired_jti = "expired_jti_123"
        active_jti = "active_jti_456"

        # Create expired token metadata
        expired_metadata = {
            "jti": expired_jti,
            "subject": subject,
            "exp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
            "status": "active"
        }
        expired_key = f"token:metadata:{expired_jti}"
        await redis_client.setex(expired_key, 3600, json.dumps(expired_metadata))

        # Create active token metadata
        active_metadata = {
            "jti": active_jti,
            "subject": subject,
            "exp": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "status": "active"
        }
        active_key = f"token:metadata:{active_jti}"
        await redis_client.setex(active_key, 3600, json.dumps(active_metadata))

        # Clean up expired tokens
        cleaned_count = await revocation_service.cleanup_expired_tokens(subject)

        # Should have cleaned up 1 expired token
        assert cleaned_count == 1

        # Verify expired token is gone
        assert await redis_client.exists(expired_key) is False

        # Verify active token still exists
        assert await redis_client.exists(active_key) is True

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_no_expired(self, revocation_service, redis_client):
        """Test cleanup when no tokens are expired."""
        subject = "no_expired@example.com"
        active_jti = "active_jti_789"

        # Create active token metadata
        active_metadata = {
            "jti": active_jti,
            "subject": subject,
            "exp": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "status": "active"
        }
        active_key = f"token:metadata:{active_jti}"
        await redis_client.setex(active_key, 3600, json.dumps(active_metadata))

        # Clean up expired tokens
        cleaned_count = await revocation_service.cleanup_expired_tokens(subject)

        # Should have cleaned up 0 tokens
        assert cleaned_count == 0

        # Verify active token still exists
        assert await redis_client.exists(active_key) is True

    @pytest.mark.asyncio
    async def test_revoke_access_token_failure_handling(self, revocation_service, redis_client):
        """Test handling of failures during access token revocation."""
        jti = "failure_jti_123"
        subject = "test@example.com"

        # Mock Redis to raise exception
        with patch.object(redis_client, 'setex', side_effect=Exception("Redis error")):
            result = await revocation_service.revoke_access_token(jti, subject)

            # Should return False on failure
            assert result is False

    @pytest.mark.asyncio
    async def test_revoke_refresh_token_failure_handling(self, revocation_service, redis_client):
        """Test handling of failures during refresh token revocation."""
        jti = "failure_refresh_jti_123"
        subject = "test@example.com"

        # Mock Redis to raise exception
        with patch.object(redis_client, 'setex', side_effect=Exception("Redis error")):
            result = await revocation_service.revoke_refresh_token(jti, subject)

            # Should return False on failure
            assert result is False

    @pytest.mark.asyncio
    async def test_is_token_revoked_failure_handling(self, revocation_service, redis_client):
        """Test handling of failures during token revocation checking."""
        jti = "failure_check_jti_123"

        # Mock Redis to raise exception
        with patch.object(redis_client, 'exists', side_effect=Exception("Redis error")):
            result = await revocation_service.is_token_revoked(jti)

            # Should return False (fail open) on failure
            assert result is False

    @pytest.mark.asyncio
    async def test_revoke_user_sessions_failure_handling(self, revocation_service, redis_client):
        """Test handling of failures during user session revocation."""
        subject = "failure_sessions@example.com"

        # Mock Redis keys to raise exception
        with patch.object(redis_client, 'keys', side_effect=Exception("Redis error")):
            result = await revocation_service.revoke_user_sessions(subject)

            # Should return 0 on failure
            assert result == 0

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_failure_handling(self, revocation_service, redis_client):
        """Test handling of failures during token cleanup."""
        subject = "failure_cleanup@example.com"

        # Mock Redis keys to raise exception
        with patch.object(redis_client, 'keys', side_effect=Exception("Redis error")):
            result = await revocation_service.cleanup_expired_tokens(subject)

            # Should return 0 on failure
            assert result == 0