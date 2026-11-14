from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import Role, require_roles
from app.db import get_db
from app.models import User
from app.services.analytics import metrics

router = APIRouter()


@router.get("/analytics")
def analytics(
    database: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.WAREHOUSE_MANAGER, Role.DIRECTOR)),
):
    return metrics(database)
