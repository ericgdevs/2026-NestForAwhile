from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.auth import require_roles
from app.db import get_session
from app.models import Role, User
from app.schemas import DietaryProfileRead, DietaryProfileWrite
from app.services import profiles

router = APIRouter(tags=["profile"])


@router.put("/me/profile", response_model=DietaryProfileRead)
def save_profile(data: DietaryProfileWrite, user: User = Depends(require_roles(Role.CLIENT)),
                 session: Session = Depends(get_session)):
    try:
        return profiles.save_dietary_profile(session, user.id, data)
    except LookupError:
        raise HTTPException(404, "No client profile found for this account.")
