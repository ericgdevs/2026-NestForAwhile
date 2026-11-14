from typing import Literal

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.auth import require_roles
from app.db import get_session
from app.models import Role
from app.schemas import LotRead, ReplenishmentItem
from app.services import inventory, replenishment

router = APIRouter(tags=["inventory"])
INVENTORY_ROLES = (Role.STAFF, Role.MANAGER)


@router.get("/inventory/lots", response_model=list[LotRead], dependencies=[Depends(require_roles(*INVENTORY_ROLES))])
def list_lots(session: Session = Depends(get_session)):
    return inventory.list_lots(session)


@router.get("/inventory/replenishment", response_model=list[ReplenishmentItem],
            dependencies=[Depends(require_roles(*INVENTORY_ROLES))])
def get_replenishment(sort: Literal["priority", "location", "name"] = "priority", session: Session = Depends(get_session)):
    return replenishment.list_replenishment(session, sort)
