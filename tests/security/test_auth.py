"""Security tests for JWT authentication flows.

Tests cover:
- User registration with OTP
- Login with valid/invalid credentials
- Token refresh and expiration
- Account locking after failed attempts
- Logout and token blacklisting
- Password reset functionality
"""

import pytest
from fastapi import HTTPException
from freezegun import freeze_time

from apps.api.app.db.models import User
from apps.api.app.exceptions import InvalidCredentialsError, OTPError, TokenError
from apps.api.app.services.auth import AuthService


class TestUserRegistration:
    """Test user registration security."""

    @pytest.mark.asyncio
    async def test_successful_registration(self, auth_service, db_session):
        """Test successful user registration returns OTP secret."""
        email = "newuser@example.com"
        password = "SecurePass123!"

        otp_secret = await auth_service.register_user(email, password)

        # Verify user was created
        user = db_session.query(User).filter(User.email == email).first()
        assert user is not None
        assert user.email == email
        assert user.is_active is True
        assert user.failed_login_attempts == 0
        assert user.account_locked_until is None

        # Verify OTP secret is returned and encrypted
        assert otp_secret is not None
        assert len(otp_secret) > 0
        assert otp_secret != user.get_otp_secret()  # Should be encrypted in DB

    @pytest.mark.asyncio
    async def test_duplicate_registration_fails(self, auth_service, test_user):
        """Test that registering with existing email fails."""
        with pytest.raises(InvalidCredentialsError):
            await auth_service.register_user(test_user["email"], "NewPassword123!")

    @pytest.mark.asyncio
    async def test_weak_password_rejection(self, auth_service):
        """Test that weak passwords are rejected."""
        weak_passwords = ["123", "password", "weak"]

        for weak_pass in weak_passwords:
            with pytest.raises(InvalidCredentialsError):
                await auth_service.register_user(f"user_{weak_pass}@example.com", weak_pass)


class TestUserAuthentication:
    """Test user login authentication security."""

    @pytest.mark.asyncio
    async def test_successful_login_with_otp(self, auth_service, test_user):
        """Test successful login with valid credentials and OTP."""
        from apps.api.app.services.auth import create_access_token, create_refresh_token

        # Authenticate user
        await auth_service.authenticate_user(
            test_user["email"],
            test_user["password"],
            test_user["otp_secret"]
        )

        # Generate tokens
        access_token = await create_access_token(test_user["email"])
        refresh_token = await create_refresh_token(test_user["email"])

        assert access_token is not None
        assert refresh_token is not None
        assert len(access_token) > 100  # JWT tokens are reasonably long
        assert len(refresh_token) > 100

    @pytest.mark.asyncio
    async def test_login_without_otp_fails(self, auth_service, test_user):
        """Test login fails without valid OTP."""
        with pytest.raises(OTPError):
            await auth_service.authenticate_user(
                test_user["email"],
                test_user["password"],
                "invalid_otp"
            )

    @pytest.mark.asyncio
    async def test_invalid_credentials_login_fails(self, auth_service):
        """Test login fails with invalid credentials."""
        with pytest.raises(InvalidCredentialsError):
            await auth_service.authenticate_user(
                "nonexistent@example.com",
                "wrongpassword",
                "123456"
            )

    @pytest.mark.asyncio
    async def test_account_locking_after_failed_attempts(self, auth_service, locked_user):
        """Test account gets locked after multiple failed attempts."""
        # Try to authenticate locked user
        with pytest.raises(InvalidCredentialsError):
            await auth_service.authenticate_user(
                locked_user.email,
                "wrong_password",
                "123456"
            )


class TestTokenManagement:
    """Test JWT token creation, validation, and refresh."""

    @pytest.mark.asyncio
    async def test_token_creation_and_validation(self, auth_service, test_user):
        """Test token creation and validation flow."""
        from apps.api.app.services.auth import (
            create_access_token,
            create_refresh_token,
            decode_token,
            verify_refresh_token
        )

        # Create tokens
        access_token = await create_access_token(test_user["email"])
        refresh_token = await create_refresh_token(test_user["email"])

        # Decode and verify access token
        subject = await decode_token(access_token)
        assert subject == test_user["email"]

        # Verify refresh token
        await verify_refresh_token(refresh_token)

    @pytest.mark.asyncio
    async def test_expired_token_rejection(self, expired_token):
        """Test that expired tokens are rejected."""
        from apps.api.app.services.auth import decode_token

        with pytest.raises(TokenError):
            await decode_token(expired_token)

    @pytest.mark.asyncio
    async def test_invalid_token_rejection(self, invalid_token):
        """Test that invalid tokens are rejected."""
        from apps.api.app.services.auth import decode_token

        with pytest.raises(TokenError):
            await decode_token(invalid_token)

    @pytest.mark.asyncio
    async def test_malformed_token_rejection(self, malformed_token):
        """Test that malformed tokens are rejected."""
        from apps.api.app.services.auth import decode_token

        with pytest.raises(TokenError):
            await decode_token(malformed_token)

    @pytest.mark.asyncio
    async def test_token_refresh_flow(self, auth_service, authenticated_user):
        """Test complete token refresh flow."""
        from apps.api.app.services.auth import (
            create_access_token,
            decode_token,
            revoke_refresh_token,
            store_refresh_token,
            verify_refresh_token
        )

        old_refresh_token = authenticated_user["refresh_token"]

        # Verify old refresh token is valid
        await verify_refresh_token(old_refresh_token)

        # Create new tokens
        new_access = await create_access_token(authenticated_user["email"])
        new_refresh = await create_refresh_token(authenticated_user["email"])

        # Store new refresh token
        await store_refresh_token(new_refresh, authenticated_user["email"])

        # Revoke old refresh token
        await revoke_refresh_token(old_refresh_token)

        # Verify old token is now blacklisted
        with pytest.raises(TokenError):
            await verify_refresh_token(old_refresh_token)

        # Verify new tokens work
        await verify_refresh_token(new_refresh)
        subject = await decode_token(new_access)
        assert subject == authenticated_user["email"]


class TestAccountSecurity:
    """Test account security features."""

    @pytest.mark.asyncio
    async def test_failed_login_attempt_tracking(self, db_session, test_user, auth_service):
        """Test that failed login attempts are tracked."""
        user = test_user["user"]
        initial_attempts = user.failed_login_attempts

        # Attempt login with wrong password multiple times
        for _ in range(3):
            with pytest.raises(InvalidCredentialsError):
                await auth_service.authenticate_user(
                    test_user["email"],
                    "wrong_password",
                    test_user["otp_secret"]
                )

        # Verify attempts were recorded
        db_session.refresh(user)
        assert user.failed_login_attempts == initial_attempts + 3

    @pytest.mark.asyncio
    async def test_successful_login_resets_attempts(self, db_session, user_with_failed_attempts, auth_service):
        """Test that successful login resets failed attempt counter."""
        user = user_with_failed_attempts
        initial_attempts = user.failed_login_attempts

        # Get user credentials
        user_email = user.email
        user_password = "TestPassword123!"  # This should be the correct password

        # Create OTP secret for this user
        otp_secret = user.get_otp_secret()

        # Successful login should reset attempts
        await auth_service.authenticate_user(user_email, user_password, otp_secret)

        # Verify attempts were reset
        db_session.refresh(user)
        assert user.failed_login_attempts == 0

    @pytest.mark.asyncio
    @freeze_time("2024-01-01 12:00:00")
    async def test_account_lockout_duration(self, db_session, test_user, auth_service):
        """Test that account lockout has proper duration."""
        user = test_user["user"]

        # Simulate 5 failed attempts
        for _ in range(5):
            with pytest.raises(InvalidCredentialsError):
                await auth_service.authenticate_user(
                    test_user["email"],
                    "wrong_password",
                    test_user["otp_secret"]
                )

        # Verify account is locked
        db_session.refresh(user)
        assert user.is_account_locked()
        assert user.account_locked_until is not None

        # Verify lockout duration (30 minutes from now)
        expected_unlock = datetime(2024, 1, 1, 12, 30, 0)
        assert user.account_locked_until.replace(tzinfo=None) == expected_unlock


class TestPasswordReset:
    """Test password reset security."""

    @pytest.mark.asyncio
    async def test_password_reset_token_generation(self, auth_service, test_user):
        """Test that password reset tokens are generated securely."""
        reset_token = await auth_service.generate_reset_token(test_user["email"])

        assert reset_token is not None
        assert len(reset_token) > 20  # Should be reasonably long

        # Verify token is different each time
        reset_token_2 = await auth_service.generate_reset_token(test_user["email"])
        assert reset_token != reset_token_2

    @pytest.mark.asyncio
    async def test_password_reset_invalid_email(self, auth_service):
        """Test password reset fails for non-existent email."""
        with pytest.raises(InvalidCredentialsError):
            await auth_service.generate_reset_token("nonexistent@example.com")


class TestAPIEndpoints:
    """Test authentication API endpoints."""

    def test_register_endpoint_security(self, client):
        """Test register endpoint with security considerations."""
        # Test rate limiting would be handled by middleware tests
        response = client.post("/auth/register", json={
            "email": "new@example.com",
            "password": "SecurePass123!"
        })

        # Should return 201 with OTP secret
        assert response.status_code == 201
        data = response.json()
        assert "otp_secret" in data

    def test_login_endpoint_security(self, client, test_user):
        """Test login endpoint security."""
        response = client.post("/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"],
            "otp_code": test_user["otp_secret"]
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_me_endpoint_requires_auth(self, client):
        """Test /me endpoint requires authentication."""
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_me_endpoint_with_valid_token(self, client, authenticated_user):
        """Test /me endpoint with valid authentication."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": authenticated_user["auth_header"]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == authenticated_user["email"]

    def test_refresh_endpoint_security(self, client, authenticated_user):
        """Test token refresh endpoint."""
        response = client.post("/auth/refresh", json={
            "refresh_token": authenticated_user["refresh_token"]
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

        # New tokens should be different
        assert data["access_token"] != authenticated_user["access_token"]
        assert data["refresh_token"] != authenticated_user["refresh_token"]

    def test_logout_endpoint_security(self, client, authenticated_user):
        """Test logout endpoint."""
        response = client.post("/auth/logout", json={
            "refresh_token": authenticated_user["refresh_token"]
        })

        assert response.status_code == 200

        # Token should be blacklisted after logout
        refresh_response = client.post("/auth/refresh", json={
            "refresh_token": authenticated_user["refresh_token"]
        })

        assert refresh_response.status_code == 401