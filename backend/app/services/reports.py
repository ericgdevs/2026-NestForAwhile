from __future__ import annotations

from datetime import date
from io import BytesIO
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CheckoutItem, Donor, Grant, InventoryLot, Visit


def report_metrics(database: Session, report_type: str, start: date, end: date) -> dict:
    owner = Donor if report_type == "donor" else Grant
    owner_id = InventoryLot.donor_id if report_type == "donor" else InventoryLot.grant_id
    owners = database.scalars(select(owner)).all()
    distributions = database.scalar(
        select(func.coalesce(func.sum(CheckoutItem.quantity), 0))
        .join(InventoryLot, InventoryLot.id == CheckoutItem.lot_id)
        .where(owner_id.is_not(None))
    ) or 0
    visits = database.scalar(
        select(func.count(Visit.id)).where(
            Visit.completed_at.is_not(None),
            Visit.completed_at >= start,
            Visit.completed_at <= end,
        )
    ) or 0
    pounds = database.scalar(
        select(func.coalesce(func.sum(Visit.pounds_distributed), 0)).where(
            Visit.completed_at.is_not(None),
            Visit.completed_at >= start,
            Visit.completed_at <= end,
        )
    ) or 0
    return {
        "attribution": [owner.attribution_label for owner in owners],
        "distribution_total": int(distributions),
        "visit_count": int(visits),
        "pounds_distributed": float(pounds),
    }


def _doc_xml(title: str, metrics: dict) -> str:
    paragraphs = [
        title,
        "Attribution",
        ", ".join(metrics["attribution"]) or "No attributed donor or grant records.",
        "Distribution totals",
        f"Items distributed: {metrics['distribution_total']}",
        "Visit metrics",
        f"Completed visits: {metrics['visit_count']}",
        "Inventory and waste summary",
        f"Pounds distributed: {metrics['pounds_distributed']:.2f}",
    ]
    return "".join(
        f"<w:p><w:r><w:t>{escape(str(paragraph))}</w:t></w:r></w:p>" for paragraph in paragraphs
    )


def build_docx(title: str, metrics: dict) -> BytesIO:
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{_doc_xml(title, metrics)}<w:sectPr/></w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        "</Relationships>"
    )
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document)
    output.seek(0)
    return output
