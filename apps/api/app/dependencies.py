from typing import Awaitable, Callable, List  # isort:skip  # noqa: UP035

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_session
from .exceptions import TokenError
from .services.auth import AuthService, decode_token

security = HTTPBearer()


class User(BaseModel):
    sub: str
    roles: List[str] = Field(default_factory=list)  # noqa: UP006


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    try:
        sub = await decode_token(credentials.credentials)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return User(sub=sub)


async def get_auth_service(
    session: AsyncSession = Depends(get_session),
) -> AuthService:
    """Provide AuthService with database session."""
    return AuthService(session)


def require_roles(
    required: List[str],  # noqa: UP006
) -> Callable[[User], Awaitable[User]]:
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if not set(required).intersection(user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
            )
        return user

    return role_checker
