from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.db.session import get_db
from app.schemas.schemas import (
    InspectionCreate, InspectionUpdate, InspectionOut,
    InspectionDetail, MeasurementCreate, APIResponse
)
from app.services.inspection_service import InspectionService
from app.services.ai_service import AIService
from app.core.security import get_current_user
from app.utils.audit import log_action

router = APIRouter(prefix="/inspections", tags=["Inspections"])


@router.post("", response_model=APIResponse, summary="Create new inspection")
async def create_inspection(
    data: InspectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    insp = await InspectionService.create_inspection(db, data, current_user.id)
    await log_action(db, "CREATE_INSPECTION", current_user.id, "Inspection", insp.inspection_id)
    return APIResponse.ok(
        data={"inspection_id": insp.inspection_id, "weld_uuid": str(insp.weld_uuid)},
        message="Inspection created"
    )


@router.get("", response_model=APIResponse, summary="Get all inspections with optional filters")
async def get_all_inspections(
    status: Optional[str] = Query(None),
    object_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    inspections = await InspectionService.get_all_inspections(db, status, object_id, skip, limit)
    data = [InspectionOut.model_validate(i) for i in inspections]
    return APIResponse.ok(data=data, message=f"{len(data)} inspections retrieved")


@router.get("/{inspection_id}", response_model=APIResponse, summary="Get inspection details")
async def get_inspection(
    inspection_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    insp = await InspectionService.get_inspection(db, inspection_id)
    return APIResponse.ok(data=InspectionOut.model_validate(insp))


@router.put("/{inspection_id}", response_model=APIResponse, summary="Update inspection remarks/position")
async def update_inspection(
    inspection_id: str,
    data: InspectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    insp = await InspectionService.update_inspection(db, inspection_id, data)
    return APIResponse.ok(data=InspectionOut.model_validate(insp), message="Inspection updated")


@router.post("/{inspection_id}/upload", response_model=APIResponse, summary="Upload weld images")
async def upload_images(
    inspection_id: str,
    panorama: Optional[UploadFile] = File(None, description="Main panorama image (required for AI analysis)"),
    additional_files: Optional[List[UploadFile]] = File(None, description="Additional close-up images"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    uploaded = await InspectionService.upload_images(db, inspection_id, panorama, additional_files)
    await log_action(db, "UPLOAD_IMAGES", current_user.id, "Inspection", inspection_id,
                     f"Uploaded {len(uploaded)} image(s)")
    return APIResponse.ok(
        data={"uploaded_count": len(uploaded)},
        message="Files uploaded successfully"
    )


@router.post("/{inspection_id}/measurements", response_model=APIResponse, summary="Save measurement data from mobile")
async def save_measurements(
    inspection_id: str,
    data: MeasurementCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    measurement = await InspectionService.save_measurements(db, inspection_id, data)
    return APIResponse.ok(
        data={"measurement_id": measurement.id},
        message="Measurements saved"
    )


@router.post("/{inspection_id}/submit", response_model=APIResponse, summary="Submit inspection and trigger AI analysis")
async def submit_inspection(
    inspection_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Step 1: Mark as submitted
    await InspectionService.submit_inspection(db, inspection_id)
    await log_action(db, "SUBMIT_INSPECTION", current_user.id, "Inspection", inspection_id)

    # Step 2: Trigger AI processing (synchronous here; use Celery for async in production)
    ai_result = await AIService.process_inspection(db, inspection_id)

    return APIResponse.ok(
        data={
            "inspection_id": inspection_id,
            "ai_status": ai_result.status,
            "overall_result": str(ai_result.overall_status).split(".")[-1],
            "defects_found": ai_result.total_defects_found,
            "marked_image_url": ai_result.marked_image_url,
        },
        message="Inspection submitted and AI analysis completed"
    )
