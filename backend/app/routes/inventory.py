from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import Role, require_roles
from app.db import get_db
from app.models import Product, User
from app.services.inventory import audit_product, lot_rows, replenishment_rows

router = APIRouter()
STAFF = (Role.WAREHOUSE_STAFF, Role.WAREHOUSE_MANAGER)


class AuditSubmit(BaseModel):
    product_id: int
    counted_qty: int = Field(ge=0)


@router.get("/inventory/audit/{code}")
def audit_lookup(
    code: str,
    database: Session = Depends(get_db),
    _: User = Depends(require_roles(*STAFF)),
):
    product = database.scalar(
        select(Product).where((Product.sku == code) | (Product.barcode == code))
    )
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return {
        "product_id": product.id,
        "name": product.name,
        "current_qty": sum(lot.quantity for lot in product.inventory_lots),
    }


@router.post("/inventory/audit")
def submit_audit(
    payload: AuditSubmit,
    current_user: User = Depends(require_roles(*STAFF)),
    database: Session = Depends(get_db),
):
    try:
        return audit_product(database, payload.product_id, payload.counted_qty, current_user.id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/inventory/replenishment")
def replenishment(
    sort: str = Query("priority", pattern="^(priority|location|name)$"),
    database: Session = Depends(get_db),
    _: User = Depends(require_roles(*STAFF)),
):
    return replenishment_rows(database, sort)


@router.get("/inventory/lots")
def lots(
    database: Session = Depends(get_db),
    _: User = Depends(require_roles(*STAFF)),
):
    return lot_rows(database)
