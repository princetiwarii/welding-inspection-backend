from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.schemas.schemas import ObjectCreate, ObjectUpdate, ObjectOut, APIResponse
from app.services.object_service import ObjectService
from app.core.security import get_current_user
from app.utils.audit import log_action

router = APIRouter(prefix="/objects", tags=["Object Management"])


@router.post("", response_model=APIResponse, summary="Create a new weld object/part")
async def create_object(
    data: ObjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    obj = await ObjectService.create_object(db, data)
    await log_action(db, "CREATE_OBJECT", current_user.id, "Object", obj.object_id,
                     f"Created object {obj.object_name}")
    return APIResponse.ok(
        data={"object_id": obj.object_id, "object_name": obj.object_name},
        message="Object created successfully"
    )


@router.get("", response_model=APIResponse, summary="Get all objects")
async def get_all_objects(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    objects = await ObjectService.get_all_objects(db, skip, limit)
    data = [ObjectOut.model_validate(o) for o in objects]
    return APIResponse.ok(data=data, message=f"{len(data)} objects retrieved")


@router.get("/{object_id}", response_model=APIResponse, summary="Get object by ID")
async def get_object(
    object_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    obj = await ObjectService.get_object_by_id(db, object_id)
    count = await ObjectService.count_inspections(db, object_id)
    result = ObjectOut.model_validate(obj)
    return APIResponse.ok(
        data={"object": result, "inspection_count": count}
    )


@router.put("/{object_id}", response_model=APIResponse, summary="Update object")
async def update_object(
    object_id: str,
    data: ObjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    obj = await ObjectService.update_object(db, object_id, data)
    await log_action(db, "UPDATE_OBJECT", current_user.id, "Object", object_id)
    return APIResponse.ok(data=ObjectOut.model_validate(obj), message="Object updated")


@router.delete("/{object_id}", response_model=APIResponse, summary="Soft delete object")
async def delete_object(
    object_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    await ObjectService.delete_object(db, object_id)
    await log_action(db, "DELETE_OBJECT", current_user.id, "Object", object_id)
    return APIResponse.ok(message=f"Object {object_id} deleted successfully")
