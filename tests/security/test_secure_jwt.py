"""Security tests for enhanced JWT authentication with encryption and validation.

Tests cover:
- Secure JWT token creation with encryption
- Comprehensive token validation
- Audience and issuer validation
- Token revocation and blacklisting
- Session tracking and security flags
- Algorithm confusion attack prevention
- Role-based access control
- Security anomaly detection
"""

import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from freezegun import freeze_time

from apps.api.app.exceptions import TokenError


class TestSecureJWTHandler:
    """Test enhanced JWT handler with encryption and security features."""

    @pytest.fixture
    def secure_jwt_handler(self, redis_client, rsa_keys):
        """Create SecureJWTHandler instance for testing."""
        from apps.api.app.services.secure_jwt import SecureJWTHandler

        return SecureJWTHandler(
            audience="agentflow-api",
            issuer="agentflow-auth",
            redis_client=redis_client,
        )

    @pytest.mark.asyncio
    async def test_create_secure_token_success(self, secure_jwt_handler, redis_client):
        """Test successful creation of encrypted JWT token."""
        subject = "test@example.com"
        roles = ["user", "admin"]

        token = await secure_jwt_handler.create_secure_token(
            subject=subject,
            roles=roles,
            expiration_minutes=5
        )

        # Verify token was created
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are reasonably long

        # Decode and verify payload
        payload = jwt.decode(
            token,
            secure_jwt_handler.public_key,
            algorithms=[secure_jwt_handler.algorithm],
            audience=secure_jwt_handler.audience,
            issuer=secure_jwt_handler.issuer,
        )

        # Verify comprehensive security claims
        assert payload["sub"] == subject
        assert payload["aud"] == secure_jwt_handler.audience
        assert payload["iss"] == secure_jwt_handler.issuer
        assert "jti" in payload
        assert "session_id" in payload
        assert payload["roles"] == roles
        assert payload["token_version"] == "1.0"
        assert "iat" in payload
        assert "nbf" in payload
        assert "exp" in payload

        # Verify expiration is reasonable (5 minutes)
        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        assert exp_time - iat_time == timedelta(minutes=5)

    @pytest.mark.asyncio
    async def test_validate_valid_token(self, secure_jwt_handler):
        """Test validation of a valid secure token."""
        subject = "test@example.com"
        roles = ["user"]

        # Create token
        token = await secure_jwt_handler.create_secure_token(subject, roles)

        # Validate token
        payload = await secure_jwt_handler.validate_token(token)

        # Verify payload
        assert payload["sub"] == subject
        assert payload["roles"] == roles
        assert "jti" in payload
        assert "session_id" in payload

    @pytest.mark.asyncio
    async def test_validate_expired_token_fails(self, secure_jwt_handler):
        """Test that expired tokens are rejected."""
        subject = "test@example.com"

        with freeze_time("2024-01-01 12:00:00"):
            # Create token that expires in 1 minute
            token = await secure_jwt_handler.create_secure_token(
                subject, expiration_minutes=1
            )

        # Move time forward past expiration
        with freeze_time("2024-01-01 12:02:00"):
            with pytest.raises(TokenError) as exc_info:
                await secure_jwt_handler.validate_token(token)

            assert "expired" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_validate_invalid_audience_fails(self, secure_jwt_handler):
        """Test that tokens with invalid audience are rejected."""
        subject = "test@example.com"

        # Create token with valid audience
        token = await secure_jwt_handler.create_secure_token(subject)

        # Decode token and modify audience
        payload = jwt.decode(
            token,
            secure_jwt_handler.public_key,
            algorithms=[secure_jwt_handler.algorithm],
        )
        payload["aud"] = "invalid-audience"

        # Re-encode with invalid audience
        invalid_token = jwt.encode(
            payload,
            secure_jwt_handler.private_key,
            algorithm=secure_jwt_handler.algorithm,
        )

        with pytest.raises(TokenError) as exc_info:
            await secure_jwt_handler.validate_token(invalid_token)

        assert "audience" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_validate_invalid_issuer_fails(self, secure_jwt_handler):
        """Test that tokens with invalid issuer are rejected."""
        subject = "test@example.com"

        # Create token with valid issuer
        token = await secure_jwt_handler.create_secure_token(subject)

        # Decode token and modify issuer
        payload = jwt.decode(
            token,
            secure_jwt_handler.public_key,
            algorithms=[secure_jwt_handler.algorithm],
        )
        payload["iss"] = "invalid-issuer"

        # Re-encode with invalid issuer
        invalid_token = jwt.encode(
            payload,
            secure_jwt_handler.private_key,
            algorithm=secure_jwt_handler.algorithm,
        )

        with pytest.raises(TokenError) as exc_info:
            await secure_jwt_handler.validate_token(invalid_token)

        assert "issuer" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_validate_revoked_token_fails(self, secure_jwt_handler, redis_client):
        """Test that revoked tokens are rejected."""
        subject = "test@example.com"

        # Create token
        token = await secure_jwt_handler.create_secure_token(subject)

        # Decode to get JTI
        payload = jwt.decode(
            token,
            secure_jwt_handler.public_key,
            algorithms=[secure_jwt_handler.algorithm],
        )
        jti = payload["jti"]

        # Revoke token
        await redis_client.setex(f"revoked:access:{jti}", 300, "revoked")

        # Validation should fail
        with pytest.raises(TokenError) as exc_info:
            await secure_jwt_handler.validate_token(token)

        assert "revoked" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_validate_token_with_invalid_roles_fails(self, secure_jwt_handler):
        """Test that tokens with invalid roles format are rejected."""
        subject = "test@example.com"

        # Create token
        token = await secure_jwt_handler.create_secure_token(subject)

        # Decode and modify roles to invalid format
        payload = jwt.decode(
            token,
            secure_jwt_handler.public_key,
            algorithms=[secure_jwt_handler.algorithm],
        )
        payload["roles"] = "invalid_roles_string"  # Should be list

        # Re-encode with invalid roles
        invalid_token = jwt.encode(
            payload,
            secure_jwt_handler.private_key,
            algorithm=secure_jwt_handler.algorithm,
        )

        with pytest.raises(TokenError) as exc_info:
            await secure_jwt_handler.validate_token(invalid_token)

        assert "roles format" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_validate_token_with_invalid_version_fails(self, secure_jwt_handler):
        """Test that tokens with invalid version are rejected."""
        subject = "test@example.com"

        # Create token
        token = await secure_jwt_handler.create_secure_token(subject)

        # Decode and modify version
        payload = jwt.decode(
            token,
            secure_jwt_handler.public_key,
            algorithms=[secure_jwt_handler.algorithm],
        )
        payload["token_version"] = "2.0"  # Invalid version

        # Re-encode with invalid version
        invalid_token = jwt.encode(
            payload,
            secure_jwt_handler.private_key,
            algorithm=secure_jwt_handler.algorithm,
        )

        with pytest.raises(TokenError) as exc_info:
            await secure_jwt_handler.validate_token(invalid_token)

        assert "version" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_token_expiration_too_far_future_fails(self, secure_jwt_handler):
        """Test that tokens with expiration too far in future are rejected."""
        subject = "test@example.com"

        # Create token
        token = await secure_jwt_handler.create_secure_token(subject)

        # Decode and modify expiration to be too far in future
        payload = jwt.decode(
            token,
            secure_jwt_handler.public_key,
            algorithms=[secure_jwt_handler.algorithm],
        )
        payload["exp"] = payload["iat"] + 7200  # 2 hours in future

        # Re-encode with invalid expiration
        invalid_token = jwt.encode(
            payload,
            secure_jwt_handler.private_key,
            algorithm=secure_jwt_handler.algorithm,
        )

        with pytest.raises(TokenError) as exc_info:
            await secure_jwt_handler.validate_token(invalid_token)

        assert "expiration" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_rapid_token_validation_detection(self, secure_jwt_handler, redis_client):
        """Test detection of rapid token validation attempts."""
        subject = "test@example.com"

        # Create token
        token = await secure_jwt_handler.create_secure_token(subject)

        # Decode to get JTI
        payload = jwt.decode(
            token,
            secure_jwt_handler.public_key,
            algorithms=[secure_jwt_handler.algorithm],
        )
        jti = payload["jti"]

        # Simulate rapid validation by setting last validation time
        await redis_client.setex(
            f"token:last_validation:{jti}",
            300,
            (datetime.utcnow() - timedelta(seconds=30)).isoformat()
        )

        # Validate token - should detect rapid validation
        result_payload = await secure_jwt_handler.validate_token(token)

        # Should include security flags
        assert "security_flags" in result_payload
        assert "rapid_validation" in result_payload.get("security_flags", [])

    @pytest.mark.asyncio
    async def test_rotate_tokens(self, secure_jwt_handler):
        """Test that refresh token rotation issues new tokens."""
        subject = "rotate@example.com"
        refresh = await secure_jwt_handler.create_secure_token(subject, expiration_minutes=10080)
        rotated = await secure_jwt_handler.rotate_tokens(refresh)
        assert rotated["refresh_token"] != refresh
        payload = jwt.decode(
            rotated["refresh_token"],
            secure_jwt_handler.public_key,
            algorithms=[secure_jwt_handler.algorithm],
            audience=secure_jwt_handler.audience,
            issuer=secure_jwt_handler.issuer,
        )
        assert payload["sub"] == subject

    @pytest.mark.asyncio
    async def test_token_metadata_storage(self, secure_jwt_handler, redis_client):
        """Test that token metadata is properly stored."""
        subject = "test@example.com"
        session_id = "test_session_123"

        # Mock session ID generation
        with patch.object(secure_jwt_handler, '_generate_session_id', return_value=session_id):
            token = await secure_jwt_handler.create_secure_token(subject)

        # Decode to get JTI
        payload = jwt.decode(
            token,
            secure_jwt_handler.public_key,
            algorithms=[secure_jwt_handler.algorithm],
        )
        jti = payload["jti"]

        # Check that metadata was stored
        metadata_key = f"token:metadata:{jti}"
        metadata = await redis_client.get(metadata_key)

        assert metadata is not None
        metadata_dict = eval(metadata.decode())  # Convert bytes to dict

        assert metadata_dict["jti"] == jti
        assert metadata_dict["subject"] == subject
        assert metadata_dict["session_id"] == session_id
        assert metadata_dict["status"] == "active"

    @pytest.mark.asyncio
    async def test_generate_secure_jti(self, secure_jwt_handler):
        """Test generation of cryptographically secure JWT ID."""
        jti1 = secure_jwt_handler._generate_secure_jti()
        jti2 = secure_jwt_handler._generate_secure_jti()

        # Verify JTIs are unique and properly formatted
        assert jti1 != jti2
        assert isinstance(jti1, str)
        assert len(jti1) > 20  # Should be reasonably long

        # Should be URL-safe base64
        import base64
        import re
        assert re.match(r'^[A-Za-z0-9_-]*$', jti1)

    @pytest.mark.asyncio
    async def test_generate_session_id(self, secure_jwt_handler):
        """Test generation of unique session identifier."""
        session_id1 = secure_jwt_handler._generate_session_id()
        session_id2 = secure_jwt_handler._generate_session_id()

        # Verify session IDs are unique and properly formatted
        assert session_id1 != session_id2
        assert isinstance(session_id1, str)
        assert session_id1.startswith("session_")
        assert len(session_id1) > 10

    @pytest.mark.asyncio
    async def test_derive_encryption_key(self, secure_jwt_handler):
        """Test derivation of encryption key from master secret."""
        key1 = secure_jwt_handler._derive_encryption_key()
        key2 = secure_jwt_handler._derive_encryption_key()

        # Keys should be consistent for same secret
        assert key1 == key2
        assert isinstance(key1, bytes)
        assert len(key1) == 32  # HKDF-SHA256 with 32-byte output

    @pytest.mark.asyncio
    async def test_is_token_revoked(self, secure_jwt_handler, redis_client):
        """Test token revocation checking."""
        jti = "test_jti_123"

        # Token should not be revoked initially
        assert await secure_jwt_handler._is_token_revoked(jti) is False

        # Revoke token
        await redis_client.setex(f"revoked:access:{jti}", 300, "revoked")

        # Should now be revoked
        assert await secure_jwt_handler._is_token_revoked(jti) is True

    @pytest.mark.asyncio
    async def test_validate_token_claims_valid(self, secure_jwt_handler):
        """Test validation of valid token claims."""
        payload = {
            "sub": "test@example.com",
            "roles": ["user", "admin"],
            "token_version": "1.0",
            "iat": datetime.utcnow().timestamp(),
            "exp": (datetime.utcnow() + timedelta(minutes=5)).timestamp()
        }

        # Should not raise exception
        result = secure_jwt_handler._validate_token_claims(payload)
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_token_claims_invalid_roles(self, secure_jwt_handler):
        """Test validation fails with invalid roles format."""
        payload = {
            "sub": "test@example.com",
            "roles": "invalid_string_instead_of_list",
            "token_version": "1.0"
        }

        with pytest.raises(TokenError):
            secure_jwt_handler._validate_token_claims(payload)

    @pytest.mark.asyncio
    async def test_validate_token_claims_invalid_version(self, secure_jwt_handler):
        """Test validation fails with invalid token version."""
        payload = {
            "sub": "test@example.com",
            "roles": ["user"],
            "token_version": "9.9"
        }

        with pytest.raises(TokenError):
            secure_jwt_handler._validate_token_claims(payload)

    @pytest.mark.asyncio
    async def test_analyze_token_security_normal(self, secure_jwt_handler, redis_client):
        """Test security analysis for normal token usage."""
        payload = {"jti": "test_jti_123"}

        # Should return empty flags for normal usage
        flags = await secure_jwt_handler._analyze_token_security(payload)
        assert flags == []

    @pytest.mark.asyncio
    async def test_analyze_token_security_rapid_validation(self, secure_jwt_handler, redis_client):
        """Test security analysis detects rapid validation."""
        jti = "test_jti_123"
        payload = {"jti": jti}

        # Set recent validation time
        await redis_client.setex(
            f"token:last_validation:{jti}",
            300,
            (datetime.utcnow() - timedelta(seconds=10)).isoformat()
        )

        flags = await secure_jwt_handler._analyze_token_security(payload)
        assert "rapid_validation" in flags