from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from loguru import logger

from ..dependencies import get_auth_service
from ..exceptions import InvalidCredentialsError, OTPError, TokenError
from ..models.auth import (
    LoginRequest,
    LogoutResponse,
    RefreshRequest,
    RegisterResponse,
    ResetRequest,
    ResetResponse,
    TokenResponse,
    UserCreate,
    UserInfo,
)
from ..rate_limiter import limiter
from ..services.auth import (
    AuthService,
    create_access_token,
    create_refresh_token,
    decode_token,
    is_refresh_token_blacklisted,
    revoke_refresh_token,
    store_refresh_token,
    verify_refresh_token,
)

router = APIRouter()


@router.post("/register", status_code=201, response_model=RegisterResponse)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    try:
        secret = await auth_service.register_user(user.email, user.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RegisterResponse(otp_secret=secret)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    credentials: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        await auth_service.authenticate_user(
            credentials.email, credentials.password, credentials.otp_code
        )
        access = await create_access_token(credentials.email)
        refresh = await create_refresh_token(credentials.email)
        await store_refresh_token(refresh, credentials.email)
        return TokenResponse(access_token=access, refresh_token=refresh)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except OTPError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except TokenError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("5/minute")
async def refresh(request: Request, token: RefreshRequest) -> TokenResponse:
    try:
        if await is_refresh_token_blacklisted(token.refresh_token):
            raise TokenError("Invalid refresh token")
        subject = await decode_token(token.refresh_token)
        await verify_refresh_token(token.refresh_token)
        access = await create_access_token(subject)
        new_refresh = await create_refresh_token(subject)
        await store_refresh_token(new_refresh, subject)
        await revoke_refresh_token(token.refresh_token)
        return TokenResponse(access_token=access, refresh_token=new_refresh)
    except TokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/logout", response_model=LogoutResponse)
@limiter.limit("5/minute")
async def logout(request: Request, token: RefreshRequest) -> LogoutResponse:
    try:
        if await is_refresh_token_blacklisted(token.refresh_token):
            raise TokenError("Invalid refresh token")
        await verify_refresh_token(token.refresh_token)
        await revoke_refresh_token(token.refresh_token)
        return LogoutResponse()
    except TokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/reset", response_model=ResetResponse)
@limiter.limit("5/minute")
async def reset(
    request: Request,
    payload: ResetRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> ResetResponse:
    try:
        token = await auth_service.generate_reset_token(payload.email)
        logger.info("password reset requested", email=payload.email)
        return ResetResponse(reset_token=token)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/me", response_model=UserInfo)
@limiter.limit("5/minute")
async def me(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserInfo:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        subject = await decode_token(token)
        info = await auth_service.get_user_info(subject)
        return UserInfo(**info)
    except (TokenError, InvalidCredentialsError) as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
