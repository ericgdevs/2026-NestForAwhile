from __future__ import annotations

import secrets

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CapacitySetting, Client, QueueEntry, ShoppingSession


def start_session(database: Session, client: Client) -> str | None:
    capacity = database.scalar(select(CapacitySetting).order_by(CapacitySetting.id))
    max_capacity = capacity.Max_Floor_Capacity if capacity else 10
    active_count = database.scalar(
        select(func.count(ShoppingSession.id)).where(ShoppingSession.status == "active")
    ) or 0
    if active_count >= max_capacity:
        database.add(QueueEntry(client_id=client.user_id, status="waiting"))
        database.commit()
        return None

    token = secrets.token_urlsafe(32)
    database.add(
        ShoppingSession(
            Shopping_Session_Token=token,
            client_id=client.user_id,
            status="active",
        )
    )
    database.commit()
    return token
