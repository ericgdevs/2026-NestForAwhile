from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.models import User
from app.schemas import LoginRequest, LoginResponse, MeResponse, UserRead

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=LoginResponse)
def login(body: LoginRequest):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/auth/logout", status_code=204)
def logout():
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)):
    return MeResponse(user=UserRead(id=user.id, role=user.role))
