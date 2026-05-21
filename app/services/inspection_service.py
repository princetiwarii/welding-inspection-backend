from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, UploadFile
from datetime import datetime
from typing import List

from app.models.models import (
    Inspection, InspectionImage, Measurement,
    ImageType, InspectionStatus, Object
)
from app.schemas.schemas import InspectionCreate, InspectionUpdate, MeasurementCreate
from app.utils.id_generator import generate_inspection_id
from app.utils.s3 import upload_upload_file
import uuid


class InspectionService:

    @staticmethod
    async def create_inspection(
        db: AsyncSession, data: InspectionCreate, inspector_id: int
    ) -> Inspection:
        # Verify object exists
        obj_result = await db.execute(
            select(Object).where(Object.object_id == data.object_id)
        )
        if not obj_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"Object {data.object_id} not found")

        inspection = Inspection(
            inspection_id=generate_inspection_id(),
            weld_uuid=uuid.uuid4(),
            object_id=data.object_id,
            inspector_id=inspector_id,
            welding_position=data.welding_position.value if data.welding_position else None,
            remarks=data.remarks,
            scan_length_meters=data.scan_length_meters,
            scan_start_time=data.scan_start_time,
            scan_end_time=data.scan_end_time,
            status=InspectionStatus.DRAFT,
        )
        db.add(inspection)
        await db.flush()
        return inspection

    @staticmethod
    async def get_inspection(db: AsyncSession, inspection_id: str) -> Inspection:
        result = await db.execute(
            select(Inspection).where(Inspection.inspection_id == inspection_id)
        )
        insp = result.scalar_one_or_none()
        if not insp:
            raise HTTPException(status_code=404, detail=f"Inspection {inspection_id} not found")
        return insp

    @staticmethod
    async def get_all_inspections(
        db: AsyncSession,
        status: str = None,
        object_id: str = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list:
        query = select(Inspection)
        if status:
            query = query.where(Inspection.status == status)
        if object_id:
            query = query.where(Inspection.object_id == object_id)
        query = query.order_by(Inspection.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def upload_images(
        db: AsyncSession,
        inspection_id: str,
        panorama: UploadFile = None,
        additional_files: List[UploadFile] = None,
    ) -> list:
        insp = await InspectionService.get_inspection(db, inspection_id)
        uploaded = []
        prefix = f"inspections/{inspection_id}"

        if panorama:
            info = await upload_upload_file(panorama, prefix)
            img = InspectionImage(
                inspection_id=inspection_id,
                image_type=ImageType.PANORAMA,
                **info,
            )
            db.add(img)
            uploaded.append(img)

        if additional_files:
            for f in additional_files:
                info = await upload_upload_file(f, prefix)
                img = InspectionImage(
                    inspection_id=inspection_id,
                    image_type=ImageType.ADDITIONAL,
                    **info,
                )
                db.add(img)
                uploaded.append(img)

        await db.flush()
        return uploaded

    @staticmethod
    async def save_measurements(
        db: AsyncSession, inspection_id: str, data: MeasurementCreate
    ) -> Measurement:
        await InspectionService.get_inspection(db, inspection_id)
        m = Measurement(inspection_id=inspection_id, **data.model_dump())
        db.add(m)
        await db.flush()
        return m

    @staticmethod
    async def submit_inspection(db: AsyncSession, inspection_id: str) -> Inspection:
        insp = await InspectionService.get_inspection(db, inspection_id)

        if insp.status not in [InspectionStatus.DRAFT]:
            raise HTTPException(
                status_code=400,
                detail=f"Inspection already {insp.status}, cannot submit again"
            )

        # Check panorama image exists
        imgs_result = await db.execute(
            select(InspectionImage).where(
                InspectionImage.inspection_id == inspection_id,
                InspectionImage.image_type == ImageType.PANORAMA,
            )
        )
        panorama = imgs_result.scalar_one_or_none()
        if not panorama:
            raise HTTPException(status_code=400, detail="Panorama image is required before submitting")

        insp.status = InspectionStatus.SUBMITTED
        insp.submitted_at = datetime.utcnow()
        await db.flush()
        return insp

    @staticmethod
    async def update_inspection(
        db: AsyncSession, inspection_id: str, data: InspectionUpdate
    ) -> Inspection:
        insp = await InspectionService.get_inspection(db, inspection_id)
        update_data = data.model_dump(exclude_none=True)
        for key, val in update_data.items():
            setattr(insp, key, val)
        await db.flush()
        return insp
