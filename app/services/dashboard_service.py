from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.models import Inspection, Object, AIResult, Defect, InspectionStatus, OverallResult


class DashboardService:

    @staticmethod
    async def get_summary(db: AsyncSession) -> dict:
        total = await db.execute(select(func.count(Inspection.id)))
        pending = await db.execute(
            select(func.count(Inspection.id)).where(
                Inspection.status.in_([InspectionStatus.DRAFT, InspectionStatus.SUBMITTED, InspectionStatus.AI_PROCESSING])
            )
        )
        completed = await db.execute(
            select(func.count(Inspection.id)).where(Inspection.status == InspectionStatus.COMPLETED)
        )
        failed = await db.execute(
            select(func.count(Inspection.id)).where(Inspection.status == InspectionStatus.FAILED)
        )
        total_objects = await db.execute(select(func.count(Object.id)).where(Object.is_active == True))
        total_defects = await db.execute(select(func.count(Defect.id)))

        total_val = total.scalar() or 0
        completed_val = completed.scalar() or 0
        pass_rate = round((completed_val / total_val * 100), 1) if total_val > 0 else 0.0

        return {
            "total_inspections": total_val,
            "pending_inspections": pending.scalar() or 0,
            "completed_inspections": completed_val,
            "failed_inspections": failed.scalar() or 0,
            "total_objects": total_objects.scalar() or 0,
            "total_defects_found": total_defects.scalar() or 0,
            "pass_rate_pct": pass_rate,
        }

    @staticmethod
    async def get_recent_inspections(db: AsyncSession, limit: int = 10) -> list:
        result = await db.execute(
            select(Inspection).order_by(Inspection.created_at.desc()).limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_analytics(db: AsyncSession) -> dict:
        # Defect type distribution
        defect_dist_q = await db.execute(
            select(Defect.defect_type, func.count(Defect.id).label("count"))
            .group_by(Defect.defect_type)
            .order_by(func.count(Defect.id).desc())
        )
        defect_dist = [{"type": r[0], "count": r[1]} for r in defect_dist_q.all()]

        # Severity distribution
        severity_dist_q = await db.execute(
            select(Defect.severity, func.count(Defect.id).label("count"))
            .group_by(Defect.severity)
        )
        severity_dist = [{"severity": str(r[0]).split(".")[-1], "count": r[1]} for r in severity_dist_q.all()]

        # Pass/Fail trend (last 30 inspections)
        trend_q = await db.execute(
            select(Inspection.overall_result, func.count(Inspection.id).label("count"))
            .where(Inspection.status == InspectionStatus.COMPLETED)
            .group_by(Inspection.overall_result)
        )
        pass_fail = [{"result": str(r[0]).split(".")[-1], "count": r[1]} for r in trend_q.all()]

        return {
            "defect_type_distribution": defect_dist,
            "inspections_over_time": [],  # Extend with date-based grouping as needed
            "severity_distribution": severity_dist,
            "pass_fail_trend": pass_fail,
        }
