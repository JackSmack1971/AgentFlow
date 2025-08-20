"""Pydantic models for authentication."""

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(UserCreate):
    pass


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
