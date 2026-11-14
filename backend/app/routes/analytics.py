from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.auth import require_roles
from app.db import get_session
from app.models import Role
from app.schemas import Analytics
from app.services import analytics

router = APIRouter(tags=["analytics"])


@router.get("/analytics", response_model=Analytics,
            dependencies=[Depends(require_roles(Role.MANAGER, Role.DIRECTOR))])
def get_analytics(session: Session = Depends(get_session)):
    return analytics.get_analytics(session)
