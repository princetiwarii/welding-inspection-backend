from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


# ── Standard Response Wrapper ──────────────────────────────────────────────

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

    @classmethod
    def ok(cls, data=None, message="Request completed successfully"):
        return cls(success=True, message=message, data=data)

    @classmethod
    def fail(cls, message="An error occurred"):
        return cls(success=False, message=message, data=None)


# ── Enum Schemas ───────────────────────────────────────────────────────────

class UserRoleEnum(str, Enum):
    ADMIN = "Admin"
    INSPECTOR = "Inspector"
    VIEWER = "Viewer"

class WeldingPositionEnum(str, Enum):
    FLAT = "Flat"
    HORIZONTAL = "Horizontal"
    VERTICAL = "Vertical"
    OVERHEAD = "Overhead"

class ReportFormatEnum(str, Enum):
    PDF = "PDF"
    EXCEL = "Excel"


# ── Auth ───────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserBasic(BaseModel):
    id: int
    name: str
    role: str
    email: str
    model_config = {"from_attributes": True}

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserBasic

class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ── Users ──────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRoleEnum = UserRoleEnum.INSPECTOR
    phone: Optional[str] = None
    company: Optional[str] = None

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    phone: Optional[str] = None
    company: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    is_active: Optional[bool] = None


# ── Objects ────────────────────────────────────────────────────────────────

class ObjectCreate(BaseModel):
    object_name: str = Field(..., min_length=2, max_length=200)
    part_number: str = Field(..., min_length=1, max_length=100)
    part_dimensions: Optional[str] = None
    material_type: Optional[str] = None
    welding_type: Optional[str] = None
    drawing_number: Optional[str] = None
    description: Optional[str] = None

class ObjectUpdate(BaseModel):
    object_name: Optional[str] = None
    part_dimensions: Optional[str] = None
    material_type: Optional[str] = None
    welding_type: Optional[str] = None
    drawing_number: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ObjectOut(BaseModel):
    id: int
    object_id: str
    object_name: str
    part_number: str
    part_dimensions: Optional[str] = None
    material_type: Optional[str] = None
    welding_type: Optional[str] = None
    drawing_number: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


# ── Inspections ────────────────────────────────────────────────────────────

class InspectionCreate(BaseModel):
    object_id: str
    welding_position: Optional[WeldingPositionEnum] = None
    remarks: Optional[str] = None
    scan_length_meters: Optional[float] = Field(None, ge=0, le=5)
    scan_start_time: Optional[datetime] = None
    scan_end_time: Optional[datetime] = None

class InspectionUpdate(BaseModel):
    welding_position: Optional[WeldingPositionEnum] = None
    remarks: Optional[str] = None

class ImageOut(BaseModel):
    id: int
    inspection_id: str
    image_type: str
    s3_url: str
    file_name: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}

class MeasurementOut(BaseModel):
    id: int
    inspection_id: str
    total_length_mm: Optional[float] = None
    weld_width_mm: Optional[float] = None
    weld_height_mm: Optional[float] = None
    weld_depth_mm: Optional[float] = None
    calculated_length_mm: Optional[float] = None
    measurement_accuracy_pct: Optional[float] = None
    created_at: datetime
    model_config = {"from_attributes": True}

class DefectOut(BaseModel):
    id: int
    defect_type: str
    severity: str
    description: Optional[str] = None
    ai_accuracy_pct: Optional[float] = None
    length_mm: Optional[float] = None
    depth_mm: Optional[float] = None
    count: Optional[int] = None
    position: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}

class AIResultOut(BaseModel):
    id: int
    inspection_id: str
    status: str
    overall_status: str
    total_defects_found: int
    total_length_analyzed_mm: Optional[float] = None
    marked_image_url: Optional[str] = None
    processing_duration_seconds: Optional[float] = None
    gemini_model_used: Optional[str] = None
    defects: List[DefectOut] = []
    created_at: datetime
    model_config = {"from_attributes": True}

class ReportOut(BaseModel):
    id: int
    inspection_id: str
    report_format: str
    s3_url: str
    file_name: str
    file_size_bytes: Optional[int] = None
    generated_at: datetime
    model_config = {"from_attributes": True}

class InspectionOut(BaseModel):
    id: int
    inspection_id: str
    weld_uuid: UUID
    object_id: str
    inspector_id: int
    welding_position: Optional[str] = None
    remarks: Optional[str] = None
    status: str
    overall_result: str
    scan_length_meters: Optional[float] = None
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class InspectionDetail(InspectionOut):
    images: List[ImageOut] = []
    measurements: List[MeasurementOut] = []
    ai_result: Optional[AIResultOut] = None
    reports: List[ReportOut] = []


# ── Measurements ───────────────────────────────────────────────────────────

class MeasurementCreate(BaseModel):
    total_length_mm: Optional[float] = None
    weld_width_mm: Optional[float] = None
    weld_height_mm: Optional[float] = None
    weld_depth_mm: Optional[float] = None
    accelerometer_data: Optional[dict] = None
    gyroscope_data: Optional[dict] = None
    distance_per_frame: Optional[dict] = None


# ── Report ─────────────────────────────────────────────────────────────────

class ReportGenerateRequest(BaseModel):
    format: ReportFormatEnum = ReportFormatEnum.PDF


# ── Dashboard ──────────────────────────────────────────────────────────────

class DashboardSummary(BaseModel):
    total_inspections: int
    pending_inspections: int
    completed_inspections: int
    failed_inspections: int
    total_objects: int
    total_defects_found: int
    pass_rate_pct: float

class RecentInspectionItem(BaseModel):
    inspection_id: str
    object_name: str
    inspector_name: str
    status: str
    overall_result: str
    created_at: datetime

class AnalyticsData(BaseModel):
    defect_type_distribution: List[dict]
    inspections_over_time: List[dict]
    severity_distribution: List[dict]
    pass_fail_trend: List[dict]


# ── Pagination ─────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
