from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import APIResponse, DashboardSummary, AnalyticsData
from app.services.dashboard_service import DashboardService
from app.core.security import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=APIResponse, summary="Get dashboard summary counts")
async def get_summary(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    data = await DashboardService.get_summary(db)
    return APIResponse.ok(data=DashboardSummary(**data))


@router.get("/recent-inspections", response_model=APIResponse, summary="Get recent inspections")
async def get_recent(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    inspections = await DashboardService.get_recent_inspections(db, limit)
    from app.schemas.schemas import InspectionOut
    data = [InspectionOut.model_validate(i) for i in inspections]
    return APIResponse.ok(data=data)


@router.get("/analytics", response_model=APIResponse, summary="Get analytics data")
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    data = await DashboardService.get_analytics(db)
    return APIResponse.ok(data=AnalyticsData(**data))
