from datetime import date

from sqlmodel import Session, select

from app.models import Checkout, DonationSource, GrantFundingStream, InventoryLot, InventoryMovement, Product, Visit
from app.schemas import AttributionRow, DistributionRow, ReportData, VisitMetrics

UNATTRIBUTED = "Unattributed"


def _in_period(moment, start: date, end: date) -> bool:
    return start <= moment.date() <= end


def _distributed(session: Session, start: date, end: date) -> list[dict]:
    """One row per checkout movement in the period; no client or session fields leave this query."""
    rows = session.exec(select(InventoryMovement.change, Product.weight_lb, Product.category, InventoryLot.donor_id,
                               InventoryLot.grant_id, Checkout.completed_at)
                        .join(InventoryLot, InventoryLot.id == InventoryMovement.lot_id)
                        .join(Product, Product.id == InventoryLot.product_id)
                        .join(Checkout, Checkout.id == InventoryMovement.ref_id)
                        .where(InventoryMovement.reason == "checkout", Checkout.status == "completed")).all()
    return [{"units": -change, "pounds": (weight or 0) * -change, "category": category, "donor_id": donor,
             "grant_id": grant} for change, weight, category, donor, grant, done in rows if _in_period(done, start, end)]


def source_attribution(session: Session, kind: str, start: date, end: date) -> list[AttributionRow]:
    """Attribution comes from the donor/grant linked to each lot; sources in id order, unattributed last."""
    model, key = (DonationSource, "donor_id") if kind == "donor" else (GrantFundingStream, "grant_id")
    moved = _distributed(session, start, end)
    stock = session.exec(select(InventoryLot)).all()
    sources = [(source.id, source.attribution_label) for source in session.exec(select(model).order_by(model.id))]
    sources.append((None, UNATTRIBUTED))
    rows = []
    for source_id, label in sources:
        taken = [m for m in moved if m[key] == source_id]
        on_hand = sum(lot.quantity for lot in stock if getattr(lot, key) == source_id)
        if source_id is None and not taken and not on_hand:
            continue
        rows.append(AttributionRow(label=label, units_distributed=sum(m["units"] for m in taken),
                                   pounds_distributed=round(sum(m["pounds"] for m in taken), 2), on_hand_units=on_hand))
    return rows


def distribution_totals(session: Session, start: date, end: date) -> list[DistributionRow]:
    totals: dict[str, list[float]] = {}
    for m in _distributed(session, start, end):
        units, pounds = totals.setdefault(m["category"], [0, 0.0])[:2]
        totals[m["category"]] = [units + m["units"], pounds + m["pounds"]]
    return [DistributionRow(category=c, units=int(u), pounds=round(lb, 2)) for c, (u, lb) in sorted(totals.items())]


def visit_metrics(session: Session, start: date, end: date) -> VisitMetrics:
    visits = [v for v in session.exec(select(Visit).where(Visit.completed_at.is_not(None)))
              if _in_period(v.completed_at, start, end)]
    return VisitMetrics(visits_completed=len(visits), families_served=len({v.client_id for v in visits}),
                        pounds_distributed=round(sum(v.pounds_distributed or 0 for v in visits), 2))


def build_report(session: Session, kind: str, start: date, end: date) -> ReportData:
    """Deterministic, anonymized report object; the same data and period always give the same result."""
    if kind not in ("donor", "grant"):
        raise ValueError("Report type must be 'donor' or 'grant'")
    if start > end:
        raise ValueError("period_start must not be after period_end")
    return ReportData(type=kind, period_start=start, period_end=end,
                      donor_metrics=source_attribution(session, "donor", start, end),
                      grant_attribution=source_attribution(session, "grant", start, end),
                      distribution_totals=distribution_totals(session, start, end),
                      visit_metrics=visit_metrics(session, start, end))
