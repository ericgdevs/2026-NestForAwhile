from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, select

from app.auth import (COOKIE_NAME, create_access_token, email_digest, get_current_user, verify_password)
from app.config import get_settings
from app.db import get_session
from app.models import ClientProfile, Role, User
from app.schemas import ClientRead, LoginRequest, LoginResult
from app.services import profiles, sessions

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=LoginResult)
def login(body: LoginRequest, response: Response, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email_hash == email_digest(body.email))).first()
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "That email or password didn't work. Please try again.")
    result = sessions.initialize(session, user)
    settings = get_settings()
    response.set_cookie(COOKIE_NAME, create_access_token(user.id, user.role), httponly=True,
                        secure=settings.cookie_secure, samesite="lax", max_age=settings.jwt_expire_minutes * 60)
    return result


@router.post("/auth/logout", status_code=204)
def logout(response: Response, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if user.role == Role.CLIENT:
        sessions.end_session(session, user.id)
    response.delete_cookie(COOKIE_NAME)


@router.get("/me", response_model=ClientRead)
def me(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    client = session.get(ClientProfile, user.id)
    if client is None:
        return ClientRead()
    return ClientRead(name=client.name, Household_Size=client.Household_Size,
                      Client_Enrollment_Status=client.Client_Enrollment_Status,
                      profile=profiles.get_dietary_profile(session, user.id))
