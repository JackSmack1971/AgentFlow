from fastapi import APIRouter

router = APIRouter()

@router.post("/login")
async def login(email: str, password: str) -> dict:
    # In lieu of real authentication, echo back a token with "user" role.
    token = f"{email}:user"
    return {"access_token": token, "token_type": "bearer"}
