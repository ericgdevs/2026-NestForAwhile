from fastapi import APIRouter, Depends, HTTPException

from app.auth import require_roles
from app.models import Role
from app.schemas import CapacityResponse

router = APIRouter(tags=["capacity"])
STAFF_ROLES = (Role.VOLUNTEER, Role.STAFF, Role.MANAGER)


@router.get("/capacity", response_model=CapacityResponse, dependencies=[Depends(require_roles(*STAFF_ROLES))])
def get_capacity():
    raise HTTPException(status_code=501, detail="Not implemented")
