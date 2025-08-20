from fastapi import APIRouter, HTTPException

from ..exceptions import InvalidCredentialsError, TokenError
from ..models.auth import LoginRequest, RefreshRequest, TokenResponse, UserCreate
from ..services import auth as auth_service

router = APIRouter()


@router.post("/register", status_code=201)
async def register(user: UserCreate) -> dict:
    try:
        await auth_service.register_user(user.email, user.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "ok"}


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest) -> TokenResponse:
    try:
        await auth_service.authenticate_user(credentials.email, credentials.password)
        access = await auth_service.create_access_token(credentials.email)
        refresh = await auth_service.create_refresh_token(credentials.email)
        await auth_service.store_refresh_token(refresh, credentials.email)
        return TokenResponse(access_token=access, refresh_token=refresh)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except TokenError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(token: RefreshRequest) -> TokenResponse:
    try:
        if await auth_service.is_refresh_token_blacklisted(token.refresh_token):
            raise TokenError("Invalid refresh token")
        subject = await auth_service.decode_token(token.refresh_token)
        await auth_service.verify_refresh_token(token.refresh_token)
        access = await auth_service.create_access_token(subject)
        new_refresh = await auth_service.create_refresh_token(subject)
        await auth_service.store_refresh_token(new_refresh, subject)
        await auth_service.revoke_refresh_token(token.refresh_token)
        return TokenResponse(access_token=access, refresh_token=new_refresh)
    except TokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@router.post("/logout")
async def logout(token: RefreshRequest) -> dict:
    try:
        if await auth_service.is_refresh_token_blacklisted(token.refresh_token):
            raise TokenError("Invalid refresh token")
        await auth_service.verify_refresh_token(token.refresh_token)
        await auth_service.revoke_refresh_token(token.refresh_token)
        return {"status": "ok"}
    except TokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
