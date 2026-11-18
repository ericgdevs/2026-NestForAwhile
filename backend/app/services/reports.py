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
    return _paragraphs_xml(paragraphs)


def _paragraphs_xml(paragraphs: list[str]) -> str:
    return "".join(
        f"<w:p><w:r><w:t>{escape(str(paragraph))}</w:t></w:r></w:p>" for paragraph in paragraphs
    )


def build_docx(title: str, metrics: dict) -> BytesIO:
    return _package(_doc_xml(title, metrics))


def _run(text: str, *, bold: bool = False, italic: bool = False, size: int = 22) -> str:
    props = f'{"<w:b/>" if bold else ""}{"<w:i/>" if italic else ""}<w:sz w:val="{size}"/>'
    return (
        '<w:p><w:pPr><w:spacing w:after="160"/></w:pPr>'
        f"<w:r><w:rPr>{props}</w:rPr><w:t>{escape(text)}</w:t></w:r></w:p>"
    )


def _picture(number: int, chart) -> str:
    """A chart PNG placed inline, 6 inches wide, with its text version as alt text."""
    cx = 5486400  # 6 in, in EMU
    cy = cx * chart.height // chart.width
    alt = escape(chart.alt, {'"': "&quot;"})
    return (
        "<w:p><w:r><w:drawing>"
        f'<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
        f'<wp:docPr id="{number}" name="Chart {number}" descr="{alt}"/>'
        '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:pic><pic:nvPicPr><pic:cNvPr id="{number}" name="chart{number}.png"/><pic:cNvPicPr/>'
        f'</pic:nvPicPr><pic:blipFill><a:blip r:embed="rIdChart{number}"/><a:stretch><a:fillRect/>'
        '</a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/>'
        f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        "</pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>"
    )


def build_report_docx(content, charts) -> BytesIO:
    """Title, optional AI note, the story, the charts, then the real figures."""
    body = [_run(content.title, bold=True, size=40)]
    if content.note:
        body.append(_run(content.note, italic=True, size=20))
    body += [_run(paragraph) for paragraph in content.story]
    body += [_picture(number, chart) for number, chart in enumerate(charts, start=1)]
    body.append(_run("Figures", bold=True, size=28))
    body += [_run(line) for line in content.figures]
    return _package("".join(body), [chart.png for chart in charts])


def _package(body_xml: str, images: list[bytes] | None = None) -> BytesIO:
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f"<w:body>{body_xml}<w:sectPr/></w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Default Extension="png" ContentType="image/png"/>'
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
        if images:
            image_rels = "".join(
                f'<Relationship Id="rIdChart{number}" Type="http://schemas.openxmlformats.org/'
                f'officeDocument/2006/relationships/image" Target="media/chart{number}.png"/>'
                for number in range(1, len(images) + 1)
            )
            archive.writestr(
                "word/_rels/document.xml.rels",
                '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.'
                f'openxmlformats.org/package/2006/relationships">{image_rels}</Relationships>',
            )
            for number, png in enumerate(images, start=1):
                archive.writestr(f"word/media/chart{number}.png", png)
    output.seek(0)
    return output
