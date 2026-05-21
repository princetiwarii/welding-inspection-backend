from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException

from app.models.models import Object, Inspection
from app.schemas.schemas import ObjectCreate, ObjectUpdate
from app.utils.id_generator import generate_object_id


class ObjectService:

    @staticmethod
    async def create_object(db: AsyncSession, data: ObjectCreate) -> Object:
        # Check duplicate part number
        exists = await db.execute(select(Object).where(Object.part_number == data.part_number))
        if exists.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Part number already exists")

        obj = Object(
            object_id=generate_object_id(),
            object_name=data.object_name,
            part_number=data.part_number,
            part_dimensions=data.part_dimensions,
            material_type=data.material_type,
            welding_type=data.welding_type,
            drawing_number=data.drawing_number,
            description=data.description,
        )
        db.add(obj)
        await db.flush()
        return obj

    @staticmethod
    async def get_all_objects(db: AsyncSession, skip: int = 0, limit: int = 50) -> list:
        result = await db.execute(
            select(Object).where(Object.is_active == True).offset(skip).limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_object_by_id(db: AsyncSession, object_id: str) -> Object:
        result = await db.execute(select(Object).where(Object.object_id == object_id))
        obj = result.scalar_one_or_none()
        if not obj:
            raise HTTPException(status_code=404, detail=f"Object {object_id} not found")
        return obj

    @staticmethod
    async def update_object(db: AsyncSession, object_id: str, data: ObjectUpdate) -> Object:
        obj = await ObjectService.get_object_by_id(db, object_id)
        update_data = data.model_dump(exclude_none=True)
        for key, val in update_data.items():
            setattr(obj, key, val)
        await db.flush()
        return obj

    @staticmethod
    async def delete_object(db: AsyncSession, object_id: str):
        obj = await ObjectService.get_object_by_id(db, object_id)
        # Soft delete
        obj.is_active = False
        await db.flush()

    @staticmethod
    async def count_inspections(db: AsyncSession, object_id: str) -> int:
        result = await db.execute(
            select(func.count(Inspection.id)).where(Inspection.object_id == object_id)
        )
        return result.scalar() or 0
