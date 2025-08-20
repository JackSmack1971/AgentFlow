from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

security = HTTPBearer()

class User(BaseModel):
    sub: str
    roles: List[str] = []

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    token = credentials.credentials
    if not token or token == "invalid":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id, roles_str = token.split(":", 1)
        roles = [r for r in roles_str.split(",") if r]
    except ValueError:
        user_id, roles = token, []
    return User(sub=user_id, roles=roles)

def require_roles(required: List[str]):
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if not set(required).intersection(user.roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        return user
    return role_checker
