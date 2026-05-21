from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.schemas.schemas import ReportGenerateRequest, ReportOut, APIResponse
from app.services.report_service import ReportService
from app.models.models import Report
from app.core.security import get_current_user
from app.utils.audit import log_action

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate/{inspection_id}", response_model=APIResponse, summary="Generate PDF or Excel report")
async def generate_report(
    inspection_id: str,
    data: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    report = await ReportService.generate_report(db, inspection_id, data.format.value, current_user.id)
    await log_action(db, "GENERATE_REPORT", current_user.id, "Report", inspection_id,
                     f"Generated {data.format.value} report")
    return APIResponse.ok(
        data=ReportOut.model_validate(report),
        message=f"{data.format.value} report generated successfully"
    )


@router.get("/download/{inspection_id}", summary="Download latest report for inspection")
async def download_report(
    inspection_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Redirects to the S3 URL of the most recently generated report."""
    result = await db.execute(
        select(Report)
        .where(Report.inspection_id == inspection_id)
        .order_by(Report.generated_at.desc())
    )
    report = result.scalar_one_or_none()
    if not report:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No report found for this inspection")
    return RedirectResponse(url=report.s3_url)


@router.get("/list/{inspection_id}", response_model=APIResponse, summary="List all reports for an inspection")
async def list_reports(
    inspection_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(Report).where(Report.inspection_id == inspection_id).order_by(Report.generated_at.desc())
    )
    reports = result.scalars().all()
    return APIResponse.ok(data=[ReportOut.model_validate(r) for r in reports])
