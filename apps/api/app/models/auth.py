"""Pydantic models for authentication."""

from typing import Literal

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(UserCreate):
    otp_code: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ResetRequest(BaseModel):
    email: EmailStr


class ResetResponse(BaseModel):
    reset_token: str


class UserInfo(BaseModel):
    email: EmailStr


class RegisterResponse(BaseModel):
    otp_secret: str
    status: str = "ok"


class LogoutResponse(BaseModel):
    status: Literal["ok"] = "ok"
