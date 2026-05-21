import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text,
    DateTime, ForeignKey, Enum, JSON, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


# ── Enums ──────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    ADMIN = "Admin"
    INSPECTOR = "Inspector"
    VIEWER = "Viewer"

class WeldingPosition(str, enum.Enum):
    FLAT = "Flat"
    HORIZONTAL = "Horizontal"
    VERTICAL = "Vertical"
    OVERHEAD = "Overhead"

class InspectionStatus(str, enum.Enum):
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    AI_PROCESSING = "AI Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"

class OverallResult(str, enum.Enum):
    PASS = "Pass"
    FAIL = "Fail"
    PENDING = "Pending"

class DefectSeverity(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class ImageType(str, enum.Enum):
    PANORAMA = "Panorama"
    CLOSEUP = "CloseUp"
    MARKED = "Marked"
    ADDITIONAL = "Additional"

class ReportFormat(str, enum.Enum):
    PDF = "PDF"
    EXCEL = "Excel"


# ── Timestamp Mixin ────────────────────────────────────────────────────────

class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


# ── Users ──────────────────────────────────────────────────────────────────

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    name          = Column(String(150), nullable=False)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role          = Column(Enum(UserRole), nullable=False, default=UserRole.INSPECTOR)
    is_active     = Column(Boolean, default=True, nullable=False)
    last_login    = Column(DateTime(timezone=True), nullable=True)
    phone         = Column(String(20), nullable=True)
    company       = Column(String(150), nullable=True)

    inspections = relationship("Inspection", back_populates="inspector")
    audit_logs  = relationship("AuditLog", back_populates="user")


# ── Token Blacklist ────────────────────────────────────────────────────────

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    token          = Column(Text, nullable=False, unique=True)
    blacklisted_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at     = Column(DateTime(timezone=True), nullable=False)


# ── Objects ────────────────────────────────────────────────────────────────

class Object(Base, TimestampMixin):
    __tablename__ = "objects"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    object_id       = Column(String(50), unique=True, nullable=False, index=True)
    object_name     = Column(String(200), nullable=False)
    part_number     = Column(String(100), nullable=False, unique=True)
    part_dimensions = Column(String(100), nullable=True)
    material_type   = Column(String(100), nullable=True)
    welding_type    = Column(String(100), nullable=True)
    drawing_number  = Column(String(100), nullable=True)
    description     = Column(Text, nullable=True)
    is_active       = Column(Boolean, default=True)

    inspections = relationship("Inspection", back_populates="object")


# ── Inspections ────────────────────────────────────────────────────────────

class Inspection(Base, TimestampMixin):
    __tablename__ = "inspections"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    inspection_id   = Column(String(50), unique=True, nullable=False, index=True)
    weld_uuid       = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    object_id       = Column(String(50), ForeignKey("objects.object_id"), nullable=False)
    inspector_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    welding_position = Column(Enum(WeldingPosition), nullable=True)
    remarks         = Column(Text, nullable=True)
    status          = Column(Enum(InspectionStatus), default=InspectionStatus.DRAFT, nullable=False)
    overall_result  = Column(Enum(OverallResult), default=OverallResult.PENDING)
    scan_length_meters = Column(Float, nullable=True)
    scan_start_time = Column(DateTime(timezone=True), nullable=True)
    scan_end_time   = Column(DateTime(timezone=True), nullable=True)
    submitted_at    = Column(DateTime(timezone=True), nullable=True)
    completed_at    = Column(DateTime(timezone=True), nullable=True)

    object      = relationship("Object", back_populates="inspections")
    inspector   = relationship("User", back_populates="inspections")
    images      = relationship("InspectionImage", back_populates="inspection", cascade="all, delete-orphan")
    measurements = relationship("Measurement", back_populates="inspection", cascade="all, delete-orphan")
    ai_result   = relationship("AIResult", back_populates="inspection", uselist=False, cascade="all, delete-orphan")
    reports     = relationship("Report", back_populates="inspection", cascade="all, delete-orphan")


# ── Inspection Images ──────────────────────────────────────────────────────

class InspectionImage(Base, TimestampMixin):
    __tablename__ = "inspection_images"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    inspection_id = Column(String(50), ForeignKey("inspections.inspection_id"), nullable=False)
    image_type    = Column(Enum(ImageType), nullable=False)
    s3_key        = Column(String(500), nullable=False)
    s3_url        = Column(Text, nullable=False)
    file_name     = Column(String(255), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=True)
    mime_type     = Column(String(100), nullable=True)
    width_px      = Column(Integer, nullable=True)
    height_px     = Column(Integer, nullable=True)

    inspection = relationship("Inspection", back_populates="images")


# ── Measurements ───────────────────────────────────────────────────────────

class Measurement(Base, TimestampMixin):
    __tablename__ = "measurements"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    inspection_id   = Column(String(50), ForeignKey("inspections.inspection_id"), nullable=False)
    total_length_mm = Column(Float, nullable=True)
    weld_width_mm   = Column(Float, nullable=True)
    weld_height_mm  = Column(Float, nullable=True)
    weld_depth_mm   = Column(Float, nullable=True)
    accelerometer_data  = Column(JSON, nullable=True)
    gyroscope_data      = Column(JSON, nullable=True)
    distance_per_frame  = Column(JSON, nullable=True)
    calculated_length_mm    = Column(Float, nullable=True)
    measurement_accuracy_pct = Column(Float, nullable=True)

    inspection = relationship("Inspection", back_populates="measurements")


# ── AI Results ─────────────────────────────────────────────────────────────

class AIResult(Base, TimestampMixin):
    __tablename__ = "ai_results"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    inspection_id   = Column(String(50), ForeignKey("inspections.inspection_id"), nullable=False, unique=True)
    status          = Column(String(50), default="Pending")
    overall_status  = Column(Enum(OverallResult), default=OverallResult.PENDING)
    raw_gemini_response  = Column(JSON, nullable=True)
    total_defects_found  = Column(Integer, default=0)
    total_length_analyzed_mm = Column(Float, nullable=True)
    marked_image_s3_key  = Column(String(500), nullable=True)
    marked_image_url     = Column(Text, nullable=True)
    processing_started_at   = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_duration_seconds = Column(Float, nullable=True)
    gemini_model_used   = Column(String(100), nullable=True)
    prompt_tokens_used  = Column(Integer, nullable=True)

    inspection = relationship("Inspection", back_populates="ai_result")
    defects    = relationship("Defect", back_populates="ai_result", cascade="all, delete-orphan")


# ── Defects ────────────────────────────────────────────────────────────────

class Defect(Base, TimestampMixin):
    __tablename__ = "defects"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    ai_result_id = Column(Integer, ForeignKey("ai_results.id"), nullable=False)
    defect_type  = Column(String(100), nullable=False)
    severity     = Column(Enum(DefectSeverity), nullable=False)
    description  = Column(Text, nullable=True)
    ai_accuracy_pct = Column(Float, nullable=True)
    length_mm    = Column(Float, nullable=True)
    depth_mm     = Column(Float, nullable=True)
    width_mm     = Column(Float, nullable=True)
    count        = Column(Integer, nullable=True)
    position     = Column(String(200), nullable=True)
    die          = Column(String(100), nullable=True)
    bbox_x       = Column(Float, nullable=True)
    bbox_y       = Column(Float, nullable=True)
    bbox_width   = Column(Float, nullable=True)
    bbox_height  = Column(Float, nullable=True)

    ai_result = relationship("AIResult", back_populates="defects")


# ── Reports ────────────────────────────────────────────────────────────────

class Report(Base, TimestampMixin):
    __tablename__ = "reports"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    inspection_id = Column(String(50), ForeignKey("inspections.inspection_id"), nullable=False)
    report_format = Column(Enum(ReportFormat), nullable=False)
    s3_key        = Column(String(500), nullable=False)
    s3_url        = Column(Text, nullable=False)
    file_name     = Column(String(255), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=True)
    generated_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    generated_at  = Column(DateTime(timezone=True), server_default=func.now())

    inspection = relationship("Inspection", back_populates="reports")


# ── Audit Logs ─────────────────────────────────────────────────────────────

class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=True)
    action      = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=True)
    entity_id   = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    ip_address  = Column(String(50), nullable=True)
    user_agent  = Column(Text, nullable=True)
    extra_data  = Column(JSON, nullable=True)

    user = relationship("User", back_populates="audit_logs")
