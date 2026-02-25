from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..config import settings
from ..auth import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginIn(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(payload: LoginIn):
    # Admin
    if payload.username == settings.ADMIN_USER and payload.password == settings.ADMIN_PASSWORD:
        token = create_access_token(payload.username, role="admin")
        return {"access_token": token, "token_type": "bearer", "role": "admin"}

    # Reviewer (optional)
    if getattr(settings, "REVIEWER_USER", "") and getattr(settings, "REVIEWER_PASSWORD", ""):
        if payload.username == settings.REVIEWER_USER and payload.password == settings.REVIEWER_PASSWORD:
            token = create_access_token(payload.username, role="reviewer")
            return {"access_token": token, "token_type": "bearer", "role": "reviewer"}

    raise HTTPException(status_code=401, detail="Invalid credentials")