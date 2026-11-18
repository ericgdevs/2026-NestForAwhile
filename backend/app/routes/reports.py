import csv
from datetime import date, timedelta
from io import BytesIO, StringIO
from typing import Literal
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import Role, require_roles
from app.db import get_db
from app.models import Report, User
from app.services import report_data
from app.services.report_data import ReportFilters
from app.services.report_narrative import report_content
from app.services.reports import build_docx, build_report_docx, report_metrics

router = APIRouter()


class ReportPeriod(BaseModel):
    period_start: date | None = None
    period_end: date | None = None


DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
ReportReader = Depends(require_roles(Role.WAREHOUSE_MANAGER, Role.DIRECTOR))
EXPORT_COLUMNS = (
    "participant_id", "visit_date", "household_size", "items", "pounds", "donors", "grants",
)  # fmt: skip


def report_filters(
    date_from: date | None = None,
    date_to: date | None = None,
    attributed: Literal["donor", "grant"] | None = None,
    donor_id: int | None = None,
    grant_id: int | None = None,
    category: str | None = Query(None, max_length=100),
    household_min: int | None = Query(None, ge=1),
    household_max: int | None = Query(None, ge=1),
) -> ReportFilters:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must be before date_to")
    if household_min and household_max and household_min > household_max:
        raise HTTPException(status_code=422, detail="household_min must not exceed household_max")
    return ReportFilters(
        date_from,
        date_to,
        attributed,
        donor_id,
        grant_id,
        category or None,
        household_min,
        household_max,
    )


@router.get("/reports/options")
def report_options(_: User = ReportReader, database: Session = Depends(get_db)):
    return report_data.options(database)


@router.get("/reports/preview")
def report_preview(
    filters: ReportFilters = Depends(report_filters),
    _: User = ReportReader,
    database: Session = Depends(get_db),
):
    return report_data.preview(database, filters)


@router.get("/reports/export")
def report_export(
    format: Literal["csv", "json"],
    filters: ReportFilters = Depends(report_filters),
    _: User = ReportReader,
    database: Session = Depends(get_db),
):
    rows = report_data.export_rows(database, filters)
    headers = {"Content-Disposition": f'attachment; filename="report-data.{format}"'}
    if format == "json":
        return JSONResponse(rows, headers=headers)
    out = StringIO()
    writer = csv.DictWriter(out, fieldnames=EXPORT_COLUMNS)
    writer.writeheader()
    for row in rows:
        joined = {"donors": "; ".join(row["donors"]), "grants": "; ".join(row["grants"])}
        writer.writerow({**row, **joined})
    return Response(out.getvalue(), media_type="text/csv", headers=headers)


@router.post("/reports/written")
def written_report(
    preset: Literal["donor", "grant", "general"],
    format: Literal["pdf", "docx", "both"] = "docx",
    filters: ReportFilters = Depends(report_filters),
    current_user: User = ReportReader,
    database: Session = Depends(get_db),
):
    # Imported here so the charting and PDF libraries load only when a report is requested.
    from app.services.report_charts import charts_for
    from app.services.report_pdf import build_report_pdf

    end = filters.date_to or date.today()
    start = filters.date_from or end - timedelta(days=30)
    filters = ReportFilters(**{**filters.__dict__, "date_from": start, "date_to": end})
    summary = report_data.summary(database, filters)
    charts = charts_for(preset, summary, report_data.weekly(database, filters))
    audit = Report(type=preset, period_start=start, period_end=end, generated_by=current_user.id)
    database.add(audit)
    database.commit()
    content = report_content(preset, f"{start:%b %d, %Y} to {end:%b %d, %Y}", summary)
    word = build_report_docx(content, charts).getvalue() if format != "pdf" else b""
    pdf = build_report_pdf(content, charts) if format != "docx" else b""
    files = {"docx": (word, DOCX_TYPE), "pdf": (pdf, "application/pdf")}
    if format == "both":
        bundle = BytesIO()
        with ZipFile(bundle, "w", ZIP_DEFLATED) as archive:
            archive.writestr(f"{preset}-report.docx", word)
            archive.writestr(f"{preset}-report.pdf", pdf)
        data, media_type, extension = bundle.getvalue(), "application/zip", "zip"
    else:
        (data, media_type), extension = files[format], format
    return Response(
        data,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{preset}-report.{extension}"'},
    )


@router.post("/reports/{type}")
def generate_report(
    type: str,
    payload: ReportPeriod,
    current_user: User = Depends(require_roles(Role.WAREHOUSE_MANAGER, Role.DIRECTOR)),
    database: Session = Depends(get_db),
):
    if type not in {"donor", "grant"}:
        raise HTTPException(status_code=404, detail="Report type not found")
    end = payload.period_end or date.today()
    start = payload.period_start or end - timedelta(days=30)
    if start > end:
        raise HTTPException(status_code=422, detail="period_start must be before period_end")
    metrics = report_metrics(database, type, start, end)
    database.add(
        Report(
            type=type,
            period_start=start,
            period_end=end,
            generated_by=current_user.id,
        )
    )
    database.commit()
    document = build_docx(f"{type.title()} report", metrics)
    return StreamingResponse(
        document,
        media_type=DOCX_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{type}-report.docx"'},
    )
