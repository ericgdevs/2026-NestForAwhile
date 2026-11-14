from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.auth import require_roles
from app.db import get_session
from app.models import Role, User
from app.schemas import CapacityResponse
from app.services import capacity, queue

router = APIRouter(tags=["capacity"])
STAFF_ROLES = (Role.VOLUNTEER, Role.STAFF, Role.MANAGER)


class CapacityUpdate(BaseModel):
    Max_Floor_Capacity: int = Field(ge=1)


@router.get("/capacity", response_model=CapacityResponse, dependencies=[Depends(require_roles(*STAFF_ROLES))])
def get_capacity(session: Session = Depends(get_session)):
    queue.refresh_queue(session)
    return capacity.get_capacity(session)


@router.put("/capacity", response_model=CapacityResponse)
def put_capacity(
    body: CapacityUpdate,
    user: User = Depends(require_roles(Role.MANAGER)),
    session: Session = Depends(get_session),
):
    capacity.set_max_capacity(session, body.Max_Floor_Capacity, user.id)
    queue.refresh_queue(session)
    return capacity.get_capacity(session)
