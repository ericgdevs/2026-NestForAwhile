from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import Role, require_roles
from app.db import get_db
from app.models import Client, User, utc_now

router = APIRouter()
manager_only = require_roles(Role.WAREHOUSE_MANAGER)


@router.get("/clients/pending")
def pending_clients(_: User = Depends(manager_only), database: Session = Depends(get_db)):
    """The only place a client's real name is returned: staff verify who they approve."""
    clients = database.scalars(
        select(Client)
        .where(Client.Client_Enrollment_Status == "Pending")
        .order_by(Client.created_at)
    )
    return [
        {
            "client_id": client.user_id,
            "name": client.name,
            "Household_Size": client.Household_Size,
            "created_at": client.created_at.isoformat(),
        }
        for client in clients
    ]


@router.post("/clients/{client_id}/approve")
def approve_client(
    client_id: int,
    manager: User = Depends(manager_only),
    database: Session = Depends(get_db),
):
    client = database.get(Client, client_id)
    if client is None or client.Client_Enrollment_Status != "Pending":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No pending client")
    client.Client_Enrollment_Status = "Active"
    client.approved_by = manager.id
    client.approved_at = utc_now()
    database.commit()
    return {"client_id": client.user_id, "Client_Enrollment_Status": "Active"}
