from fastapi import APIRouter
from app.api.v1.endpoints import auth, objects, inspections, ai, reports, dashboard

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(objects.router)
api_router.include_router(inspections.router)
api_router.include_router(ai.router)
api_router.include_router(reports.router)
api_router.include_router(dashboard.router)
