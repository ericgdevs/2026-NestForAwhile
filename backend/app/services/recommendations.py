from datetime import date

from sqlmodel import Session, select

from app.models import ClientProfile, InventoryLot, Product, Recommendation
from app.rules.classify import Status, classify
from app.schemas import RecommendationRead
from app.services import profiles


def _stock_by_product(session: Session) -> dict[int, tuple[int, date | None]]:
    """In-stock, non-expired quantity and earliest expiry per product."""
    today = date.today()
    stock: dict[int, tuple[int, date | None]] = {}
    for lot in session.exec(select(InventoryLot).where(InventoryLot.quantity > 0)):
        if lot.expiration_date is not None and lot.expiration_date < today:
            continue
        qty, earliest = stock.get(lot.product_id, (0, None))
        expiry = min(filter(None, [earliest, lot.expiration_date]), default=None)
        stock[lot.product_id] = (qty + lot.quantity, expiry)
    return stock


def _rationale(status: Status, qty: int, household_size: int, reason: str) -> str:
    if status == Status.CAPPED:
        return f"{reason} Take {qty}."
    return f"Fits your dietary needs. {qty} suggested for a household of {household_size}."


def generate_for_session(session: Session, client_id: int, session_id: int) -> list[Recommendation]:
    client = session.get(ClientProfile, client_id)
    restrictions = profiles.rule_restrictions(profiles.get_dietary_profile(session, client_id))
    stock = _stock_by_product(session)
    never_expiring = date.max
    products = session.exec(select(Product).where(Product.id.in_(stock))).all()
    # Expiring-soonest first reduces waste; name keeps the order deterministic
    products.sort(key=lambda p: (stock[p.id][1] or never_expiring, p.name))
    rows = []
    for product in products:
        result = classify(product, restrictions)
        if result.status == Status.RESTRICTED:
            continue
        available = stock[product.id][0]
        qty = min(client.Household_Size, available) if result.status == Status.APPROVED else 1
        rows.append(Recommendation(session_id=session_id, product_id=product.id, suggested_qty=qty,
                                   rationale=_rationale(result.status, qty, client.Household_Size, result.reason)))
    session.add_all(rows)
    session.commit()
    return rows


def list_for_session(session: Session, client_id: int, session_id: int) -> list[RecommendationRead]:
    restrictions = profiles.rule_restrictions(profiles.get_dietary_profile(session, client_id))
    rows = session.exec(select(Recommendation, Product).join(Product, Product.id == Recommendation.product_id)
                        .where(Recommendation.session_id == session_id).order_by(Recommendation.id)).all()
    return [RecommendationRead(product_id=p.id, name=p.name, suggested_qty=r.suggested_qty, rationale=r.rationale,
                               status=classify(p, restrictions).status.name.capitalize()) for r, p in rows]
