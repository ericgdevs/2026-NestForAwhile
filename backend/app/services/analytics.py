from datetime import date

from sqlalchemy import func
from sqlmodel import Session, select

from app.models import (Cart, CartItem, Checkout, CheckoutItem, ClientProfile, DietaryTier, InventoryLot,
                        InventoryMovement, Product, Visit)
from app.schemas import Analytics, WasteReduction
from app.services import fifo


def _completed_visits(session: Session):
    return select(Visit).where(Visit.completed_at.is_not(None))


def _scalar(session: Session, query) -> int | float:
    return session.exec(query).one() or 0


def recommendation_adoption_rate(session: Session) -> float:
    """Checked-out units that were recommended, divided by all checked-out units."""
    rows = session.exec(select(CheckoutItem.quantity, CartItem.from_recommendation)
                        .join(Checkout, Checkout.id == CheckoutItem.checkout_id)
                        .join(Cart, Cart.session_id == Checkout.session_id)
                        .join(CartItem, (CartItem.cart_id == Cart.id) & (CartItem.product_id == CheckoutItem.product_id))
                        .where(Checkout.status == "completed")).all()
    total = sum(qty for qty, _ in rows)
    return round(sum(qty for qty, rec in rows if rec) / total, 4) if total else 0.0


def _checkout_movements(session: Session):
    """(units taken, pounds, category, lot expiry, completed date) per checkout movement."""
    rows = session.exec(select(InventoryMovement.change, Product.weight_lb, Product.category,
                               InventoryLot.expiration_date, Checkout.completed_at)
                        .join(InventoryLot, InventoryLot.id == InventoryMovement.lot_id)
                        .join(Product, Product.id == InventoryLot.product_id)
                        .join(Checkout, Checkout.id == InventoryMovement.ref_id)
                        .where(InventoryMovement.reason == "checkout", Checkout.status == "completed")).all()
    return [(-change, (weight or 0) * -change, category, expiry, done) for change, weight, category, expiry, done in rows]


def waste_reduction(session: Session, today: date | None = None) -> WasteReduction:
    today = today or date.today()
    soon_lots = sum(1 for lot in fifo.all_lots_fifo(session) if fifo.is_expiring_soon(lot, today))
    saved = sum(lb for _, lb, _, expiry, done in _checkout_movements(session)
                if expiry is not None and 0 <= (expiry - done.date()).days <= fifo.EXPIRING_SOON_DAYS)
    return WasteReduction(expiring_soon_lots=soon_lots, pounds_saved=round(saved, 2))


def get_analytics(session: Session, today: date | None = None) -> Analytics:
    visits = _completed_visits(session).subquery()
    return Analytics(
        families_served=_scalar(session, select(func.count(func.distinct(visits.c.client_id)))),
        visits_completed=_scalar(session, select(func.count()).select_from(visits)),
        pounds_distributed=round(float(_scalar(session, select(func.sum(visits.c.pounds_distributed)))), 2),
        inventory_usage=sum(units for units, *_ in _checkout_movements(session)),
        recommendation_adoption_rate=recommendation_adoption_rate(session),
        waste_reduction=waste_reduction(session, today),
    )


# Service-level breakdowns (not exposed by the contract). shortcut: no small-cell suppression, add it before exposing publicly.

def inventory_by_category(session: Session, today: date | None = None) -> dict[str, dict[str, int]]:
    """On-hand (usable) and distributed units per product category, categories sorted."""
    today = today or date.today()
    categories = {p.id: p.category for p in session.exec(select(Product))}
    result: dict[str, dict[str, int]] = {c: {"on_hand": 0, "distributed": 0} for c in sorted(set(categories.values()))}
    for lot in session.exec(select(InventoryLot).where(InventoryLot.quantity > 0)):
        if not fifo.is_expired(lot, today):
            result[categories[lot.product_id]]["on_hand"] += lot.quantity
    for units, _, category, _, _ in _checkout_movements(session):
        result[category]["distributed"] += units
    return result


def clients_by_tier(session: Session) -> dict[str, int]:
    """Client counts per dietary tier name, never client rows."""
    rows = session.exec(select(DietaryTier.name, func.count(ClientProfile.user_id))
                        .join(ClientProfile, ClientProfile.Dietary_Tier_ID == DietaryTier.Dietary_Tier_ID, isouter=True)
                        .group_by(DietaryTier.Dietary_Tier_ID, DietaryTier.name).order_by(DietaryTier.Dietary_Tier_ID)).all()
    return {name: count for name, count in rows}


def checkout_history(session: Session) -> list[dict]:
    """Completed checkouts per day: count, units and pounds, oldest day first."""
    days: dict[date, dict] = {}
    for checkout in session.exec(select(Checkout).where(Checkout.status == "completed")):
        day = days.setdefault(checkout.completed_at.date(), {"date": checkout.completed_at.date(), "checkouts": 0,
                                                             "units": 0, "pounds": 0.0})
        day["checkouts"] += 1
        day["pounds"] = round(day["pounds"] + (checkout.total_lb or 0), 2)
    for units, _, _, _, done in _checkout_movements(session):
        days[done.date()]["units"] += units
    return [days[d] for d in sorted(days)]
