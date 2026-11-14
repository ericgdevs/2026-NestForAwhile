from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.auth import require_roles
from app.db import get_session
from app.models import Role
from app.schemas import LotRead
from app.services import inventory

router = APIRouter(tags=["inventory"])
INVENTORY_ROLES = (Role.STAFF, Role.MANAGER)


@router.get("/inventory/lots", response_model=list[LotRead], dependencies=[Depends(require_roles(*INVENTORY_ROLES))])
def list_lots(session: Session = Depends(get_session)):
    return inventory.list_lots(session)
