from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models import CartItem, CheckoutItem, InventoryLot, InventoryMovement, Visit


def metrics(database: Session) -> dict:
    completed_visits = select(Visit).where(Visit.completed_at.is_not(None)).subquery()
    families = database.scalar(select(func.count(distinct(completed_visits.c.client_id)))) or 0
    visits = database.scalar(select(func.count()).select_from(completed_visits)) or 0
    pounds = (
        database.scalar(
            select(func.coalesce(func.sum(Visit.pounds_distributed), 0)).where(
                Visit.completed_at.is_not(None)
            )
        )
        or 0
    )
    usage = database.scalar(
        select(func.coalesce(func.sum(-InventoryMovement.change), 0)).where(
            InventoryMovement.reason == "checkout", InventoryMovement.change < 0
        )
    ) or 0
    total_cart = database.scalar(select(func.count(CartItem.id))) or 0
    recommended_cart = database.scalar(
        select(func.count(CartItem.id)).where(CartItem.from_recommendation.is_(True))
    ) or 0
    today = date.today()
    soon = today + timedelta(days=7)
    expiring_lots = database.scalar(
        select(func.count(InventoryLot.id)).where(
            InventoryLot.quantity > 0,
            InventoryLot.expiration_date >= today,
            InventoryLot.expiration_date <= soon,
        )
    ) or 0
    near_expiry_usage = database.scalar(
        select(func.coalesce(func.sum(CheckoutItem.quantity), 0))
        .join(InventoryLot, InventoryLot.id == CheckoutItem.lot_id)
        .where(InventoryLot.expiration_date >= today, InventoryLot.expiration_date <= soon)
    ) or 0
    return {
        "families_served": families,
        "visits_completed": visits,
        "pounds_distributed": float(pounds),
        "inventory_usage": int(usage),
        "recommendation_adoption_rate": recommended_cart / total_cart if total_cart else 0,
        "waste_reduction": {
            "expiring_soon_lots": expiring_lots,
            "pounds_saved": float(near_expiry_usage),
        },
    }
