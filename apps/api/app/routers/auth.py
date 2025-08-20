from fastapi import APIRouter
router = APIRouter()

@router.post("/login")
async def login(email: str, password: str):
    # TODO: implement proper auth + JWT issuance
    return {"access_token": "demo-token", "token_type": "bearer"}
