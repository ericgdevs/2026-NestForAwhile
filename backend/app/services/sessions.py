from __future__ import annotations

import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Client, ShoppingSession
from app.services.queue import active_count, enqueue


def start_session(database: Session, client: Client) -> str | None:
    from app.models import CapacitySetting

    capacity = database.scalar(select(CapacitySetting).order_by(CapacitySetting.id))
    max_capacity = capacity.Max_Floor_Capacity if capacity else 10
    if active_count(database) >= max_capacity:
        enqueue(database, client)
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
