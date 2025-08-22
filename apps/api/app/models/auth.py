"""Pydantic models for authentication."""

from typing import Literal

from pydantic import EmailStr

from .base import StrictModel


class UserCreate(StrictModel):
    email: EmailStr
    password: str


class LoginRequest(UserCreate):
    otp_code: str


class RefreshRequest(StrictModel):
    refresh_token: str


class TokenResponse(StrictModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ResetRequest(StrictModel):
    email: EmailStr


class ResetResponse(StrictModel):
    reset_token: str


class UserInfo(StrictModel):
    email: EmailStr


class RegisterResponse(StrictModel):
    otp_secret: str
    status: str = "ok"


class LogoutResponse(StrictModel):
    status: Literal["ok"] = "ok"
