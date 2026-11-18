"""Anonymous visit dataset for reports: filters, preview rows, totals and summaries.

Rows never carry a name, email or database ID. A participant is a keyed-hash code (same family,
same code), shown next to household size, which is enough to count families without naming them.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Checkout, CheckoutItem, Client, Donor, Grant, InventoryLot, Product, Visit

PREVIEW_ROWS = 100  # the preview shows the newest rows; totals always cover every match
EXPORT_ROWS = 50_000  # shortcut: one in-memory file, stream or paginate if exports outgrow this
TOP_CATEGORIES = 5


@dataclass(frozen=True)
class ReportFilters:
    date_from: date | None = None
    date_to: date | None = None
    attributed: str | None = None  # "donor" or "grant": only items from lots with that attribution
    donor_id: int | None = None
    grant_id: int | None = None
    category: str | None = None
    household_min: int | None = None
    household_max: int | None = None


def participant_code(client_id: int) -> str:
    digest = hmac.new(settings.jwt_secret.encode(), str(client_id).encode(), hashlib.sha256)
    return f"P-{digest.hexdigest()[:8].upper()}"


def _conditions(f: ReportFilters) -> list[Any]:
    checks: list[Any] = [Visit.completed_at.is_not(None)]
    if f.date_from:
        checks.append(Visit.completed_at >= datetime.combine(f.date_from, time.min))
    if f.date_to:
        checks.append(
            Visit.completed_at < datetime.combine(f.date_to + timedelta(days=1), time.min)
        )
    if f.attributed == "donor":
        checks.append(InventoryLot.donor_id.is_not(None))
    if f.attributed == "grant":
        checks.append(InventoryLot.grant_id.is_not(None))
    if f.donor_id is not None:
        checks.append(InventoryLot.donor_id == f.donor_id)
    if f.grant_id is not None:
        checks.append(InventoryLot.grant_id == f.grant_id)
    if f.category:
        checks.append(Product.category == f.category)
    if f.household_min is not None:
        checks.append(Client.Household_Size >= f.household_min)
    if f.household_max is not None:
        checks.append(Client.Household_Size <= f.household_max)
    return checks


def _from_items(query, f: ReportFilters):
    """Completed visits -> their completed checkout items -> lot, product, household."""
    return (
        query.select_from(Visit)
        .join(
            Checkout, (Checkout.session_id == Visit.session_id) & (Checkout.status == "completed")
        )
        .join(CheckoutItem, CheckoutItem.checkout_id == Checkout.id)
        .join(InventoryLot, InventoryLot.id == CheckoutItem.lot_id)
        .join(Product, Product.id == CheckoutItem.product_id)
        .join(Client, Client.user_id == Visit.client_id)
        .where(*_conditions(f))
    )


_ITEMS = func.sum(CheckoutItem.quantity)
_POUNDS = func.sum(CheckoutItem.quantity * func.coalesce(Product.weight_lb, 0))


def _visit_rows(database: Session, f: ReportFilters, limit: int) -> list[dict[str, Any]]:
    query = _from_items(
        select(
            Visit.id, Visit.client_id, Visit.completed_at, Client.Household_Size, _ITEMS, _POUNDS
        ),
        f,
    )
    rows = database.execute(
        query.group_by(Visit.id, Visit.client_id, Visit.completed_at, Client.Household_Size)
        .order_by(Visit.completed_at.desc(), Visit.id.desc())
        .limit(limit)
    ).all()
    labels = _labels_by_visit(database, f, [row.id for row in rows])
    return [
        {
            "participant_id": participant_code(row.client_id),
            "visit_date": row.completed_at.date().isoformat(),
            "household_size": row.Household_Size,
            "items": int(row[4]),
            "pounds": round(float(row[5] or 0), 1),
            "donors": labels.get(row.id, {}).get("donors", []),
            "grants": labels.get(row.id, {}).get("grants", []),
        }
        for row in rows
    ]


def _labels_by_visit(database: Session, f: ReportFilters, visit_ids: list[int]):
    if not visit_ids:
        return {}
    query = _from_items(
        select(distinct(Visit.id), Donor.attribution_label, Grant.attribution_label), f
    )
    pairs = database.execute(
        query.outerjoin(Donor, Donor.id == InventoryLot.donor_id)
        .outerjoin(Grant, Grant.id == InventoryLot.grant_id)
        .where(Visit.id.in_(visit_ids))
    ).all()
    labels: dict[int, dict[str, list[str]]] = {}
    for visit_id, donor, grant in pairs:
        entry = labels.setdefault(visit_id, {"donors": [], "grants": []})
        if donor and donor not in entry["donors"]:
            entry["donors"].append(donor)
        if grant and grant not in entry["grants"]:
            entry["grants"].append(grant)
    return labels


def totals(database: Session, f: ReportFilters) -> dict[str, Any]:
    visits, families, items, pounds = database.execute(
        _from_items(
            select(
                func.count(distinct(Visit.id)),
                func.count(distinct(Visit.client_id)),
                _ITEMS,
                _POUNDS,
            ),
            f,
        )
    ).one()
    return {
        "visits": visits,
        "households": families,
        "items": int(items or 0),
        "pounds": round(float(pounds or 0), 1),
    }


def preview(database: Session, f: ReportFilters) -> dict[str, Any]:
    return {"totals": totals(database, f), "rows": _visit_rows(database, f, PREVIEW_ROWS)}


def export_rows(database: Session, f: ReportFilters) -> list[dict[str, Any]]:
    return _visit_rows(database, f, EXPORT_ROWS)


def options(database: Session) -> dict[str, Any]:
    return {
        "donors": [
            {"id": id_, "label": label}
            for id_, label in database.execute(select(Donor.id, Donor.attribution_label))
        ],
        "grants": [
            {"id": id_, "label": label}
            for id_, label in database.execute(select(Grant.id, Grant.attribution_label))
        ],
        "categories": list(
            database.scalars(select(distinct(Product.category)).order_by(Product.category))
        ),
    }


def _household_mix(database: Session, f: ReportFilters) -> dict[str, int]:
    rows = database.execute(
        _from_items(
            select(Client.Household_Size, func.count(distinct(Visit.client_id))), f
        ).group_by(Client.Household_Size)
    ).all()
    mix = {"1 person": 0, "2 people": 0, "3-4 people": 0, "5+ people": 0}
    for size, families in rows:
        key = (
            "1 person"
            if size == 1
            else "2 people"
            if size == 2
            else "3-4 people"
            if size <= 4
            else "5+ people"
        )
        mix[key] += families
    return mix


def _by_label(
    database: Session, f: ReportFilters, label_column, owner_id, owner
) -> list[dict[str, Any]]:
    rows = database.execute(
        _from_items(select(label_column, _ITEMS, _POUNDS, func.count(distinct(Visit.client_id))), f)
        .join(owner, owner.id == owner_id)
        .group_by(label_column)
        .order_by(_ITEMS.desc())
    ).all()
    return [
        {
            "label": label,
            "items": int(items),
            "pounds": round(float(pounds or 0), 1),
            "households": families,
        }
        for label, items, pounds, families in rows
    ]


def summary(database: Session, f: ReportFilters) -> dict[str, Any]:
    """Aggregates only: what the written report and its AI draft are allowed to see."""
    categories = database.execute(
        _from_items(select(Product.category, _ITEMS), f)
        .group_by(Product.category)
        .order_by(_ITEMS.desc())
        .limit(TOP_CATEGORIES)
    ).all()
    return {
        **totals(database, f),
        "household_sizes": _household_mix(database, f),
        "top_categories": [{"category": name, "items": int(items)} for name, items in categories],
        "by_donor": _by_label(database, f, Donor.attribution_label, InventoryLot.donor_id, Donor),
        "by_grant": _by_label(database, f, Grant.attribution_label, InventoryLot.grant_id, Grant),
    }


def weekly(database: Session, f: ReportFilters) -> list[dict[str, Any]]:
    """Visits and items per week (Monday start) for the charts. Not part of `summary`: the AI only
    gets aggregates without dates."""
    day = func.date(Visit.completed_at)
    rows = database.execute(
        _from_items(select(day, func.count(distinct(Visit.id)), _ITEMS), f).group_by(day)
    ).all()
    weeks: dict[date, dict[str, Any]] = {}
    for visit_day, visits, items in rows:
        visit_day = visit_day if isinstance(visit_day, date) else date.fromisoformat(str(visit_day))
        monday = visit_day - timedelta(days=visit_day.weekday())
        week = weeks.setdefault(monday, {"week": monday, "visits": 0, "items": 0})
        week["visits"] += visits
        week["items"] += int(items or 0)
    return [weeks[monday] for monday in sorted(weeks)]
