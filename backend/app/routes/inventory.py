from fastapi import APIRouter, Depends, HTTPException

from app.auth import require_roles
from app.models import Role

router = APIRouter(tags=["inventory"])
INVENTORY_ROLES = (Role.STAFF, Role.MANAGER)


@router.get("/inventory/lots", dependencies=[Depends(require_roles(*INVENTORY_ROLES))])
def list_lots():
    raise HTTPException(status_code=501, detail="Not implemented")
