from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import Role, require_roles
from app.db import get_db
from app.models import CapacitySetting, QueueEntry, User
from app.services.queue import active_count, promote_waiting

router = APIRouter()


class CapacityUpdate(BaseModel):
    Max_Floor_Capacity: int = Field(ge=1)


@router.get("/capacity")
def capacity(
    database: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.VOLUNTEER, Role.WAREHOUSE_STAFF, Role.WAREHOUSE_MANAGER)),
):
    setting = database.scalar(select(CapacitySetting).order_by(CapacitySetting.id))
    active = active_count(database)
    waiting = database.scalar(
        select(func.count(QueueEntry.id)).where(QueueEntry.status == "waiting")
    ) or 0
    return {
        "Active_Floor_Shoppers": active,
        "Max_Floor_Capacity": setting.Max_Floor_Capacity if setting else 10,
        "Queue_Waiting": waiting,
    }


@router.put("/capacity")
def update_capacity(
    payload: CapacityUpdate,
    current_user: User = Depends(require_roles(Role.WAREHOUSE_MANAGER)),
    database: Session = Depends(get_db),
):
    setting = database.scalar(select(CapacitySetting).order_by(CapacitySetting.id))
    if setting is None:
        setting = CapacitySetting(id=1)
        database.add(setting)
    setting.Max_Floor_Capacity = payload.Max_Floor_Capacity
    setting.updated_by = current_user.id
    promote_waiting(database)
    database.commit()
    return capacity(database, current_user)
