from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from .exceptions import TokenError
from .services import auth as auth_service

security = HTTPBearer()


class User(BaseModel):
    sub: str
    roles: List[str] = []


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    try:
        sub = await auth_service.decode_token(credentials.credentials)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return User(sub=sub, roles=[])


def require_roles(required: List[str]):
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if not set(required).intersection(user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
            )
        return user

    return role_checker
