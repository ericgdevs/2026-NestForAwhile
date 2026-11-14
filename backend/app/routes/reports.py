from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import Role, require_roles
from app.db import get_db
from app.models import Report, User
from app.services.reports import build_docx, report_metrics

router = APIRouter()


class ReportPeriod(BaseModel):
    period_start: date | None = None
    period_end: date | None = None


@router.post("/reports/{report_type}")
def generate_report(
    report_type: str,
    payload: ReportPeriod,
    current_user: User = Depends(require_roles(Role.WAREHOUSE_MANAGER, Role.DIRECTOR)),
    database: Session = Depends(get_db),
):
    if report_type not in {"donor", "grant"}:
        raise HTTPException(status_code=404, detail="Report type not found")
    end = payload.period_end or date.today()
    start = payload.period_start or end - timedelta(days=30)
    if start > end:
        raise HTTPException(status_code=422, detail="period_start must be before period_end")
    metrics = report_metrics(database, report_type, start, end)
    database.add(
        Report(
            type=report_type,
            period_start=start,
            period_end=end,
            generated_by=current_user.id,
        )
    )
    database.commit()
    document = build_docx(f"{report_type.title()} report", metrics)
    return StreamingResponse(
        document,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{report_type}-report.docx"'},
    )
