from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import Role, require_roles
from app.db import get_db
from app.models import Client, Product, User
from app.services.nutrition import scan_local

router = APIRouter()


@router.get("/products/labels")
def product_labels(
    _: User = Depends(require_roles(Role.WAREHOUSE_MANAGER)),
    database: Session = Depends(get_db),
):
    """Name and SKU of every product, for the printable shelf labels."""
    rows = database.execute(select(Product.sku, Product.name).order_by(Product.name))
    return [{"sku": sku, "name": name} for sku, name in rows]


@router.get("/products/scan/{code}")
def scan_product(
    code: str,
    current_user: User = Depends(require_roles(Role.CLIENT)),
    database: Session = Depends(get_db),
):
    client = database.get(Client, current_user.id)
    result = scan_local(database, code, client)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="We couldn't find that product. Try the SKU again.",
        )
    return result
