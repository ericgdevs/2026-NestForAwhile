from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import Role, require_roles
from app.db import get_db
from app.models import CapacitySetting, QueueEntry, ShoppingSession, User

router = APIRouter()


@router.get("/capacity")
def capacity(
    database: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.VOLUNTEER, Role.WAREHOUSE_STAFF, Role.WAREHOUSE_MANAGER)),
):
    setting = database.scalar(select(CapacitySetting).order_by(CapacitySetting.id))
    active = database.scalar(
        select(func.count(ShoppingSession.id)).where(ShoppingSession.status == "active")
    ) or 0
    waiting = database.scalar(
        select(func.count(QueueEntry.id)).where(QueueEntry.status == "waiting")
    ) or 0
    return {
        "Active_Floor_Shoppers": active,
        "Max_Floor_Capacity": setting.Max_Floor_Capacity if setting else 10,
        "Queue_Waiting": waiting,
    }
