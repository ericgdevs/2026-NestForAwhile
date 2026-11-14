from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import Role, require_roles
from app.db import get_db
from app.models import Client, User
from app.services.recommendations import build_recommendations

router = APIRouter()


@router.get("/recommendations")
def recommendations(
    current_user: User = Depends(require_roles(Role.CLIENT)),
    database: Session = Depends(get_db),
):
    client = database.get(Client, current_user.id)
    if client is None:
        return []
    return build_recommendations(database, client)
