from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.auth import require_roles
from app.db import get_session
from app.models import Role, User
from app.schemas import RecommendationRead
from app.services import recommendations, sessions

router = APIRouter(tags=["recommendations"])


@router.get("/recommendations", response_model=list[RecommendationRead])
def get_recommendations(user: User = Depends(require_roles(Role.CLIENT)), session: Session = Depends(get_session)):
    shopping = sessions.active_session(session, user.id)
    if shopping is None:
        raise HTTPException(404, "Start a shopping session to see recommendations.")
    return recommendations.list_for_session(session, user.id, shopping.id)
