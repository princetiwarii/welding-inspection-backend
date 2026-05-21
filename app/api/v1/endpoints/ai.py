from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.schemas.schemas import APIResponse, AIResultOut, DefectOut
from app.models.models import AIResult, Defect
from app.services.ai_service import AIService
from app.core.security import get_current_user

router = APIRouter(prefix="/ai", tags=["AI Processing"])


@router.post("/process/{inspection_id}", response_model=APIResponse, summary="Manually trigger AI processing")
async def trigger_ai_processing(
    inspection_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Manually re-trigger AI analysis for a submitted inspection."""
    ai_result = await AIService.process_inspection(db, inspection_id)
    return APIResponse.ok(
        data={"ai_result_id": ai_result.id, "status": ai_result.status},
        message="AI processing triggered"
    )


@router.get("/results/{inspection_id}", response_model=APIResponse, summary="Get AI results for an inspection")
async def get_ai_results(
    inspection_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(AIResult).where(AIResult.inspection_id == inspection_id)
    )
    ai_result = result.scalar_one_or_none()
    if not ai_result:
        return APIResponse.fail("No AI results found for this inspection")

    defects_q = await db.execute(
        select(Defect).where(Defect.ai_result_id == ai_result.id)
    )
    defects = defects_q.scalars().all()

    return APIResponse.ok(data={
        "inspection_id": inspection_id,
        "status": ai_result.status,
        "overall_status": str(ai_result.overall_status).split(".")[-1],
        "total_defects": ai_result.total_defects_found,
        "total_length_analyzed_mm": ai_result.total_length_analyzed_mm,
        "marked_image_url": ai_result.marked_image_url,
        "processing_duration_seconds": ai_result.processing_duration_seconds,
        "gemini_model": ai_result.gemini_model_used,
        "defects": [DefectOut.model_validate(d) for d in defects],
    })
