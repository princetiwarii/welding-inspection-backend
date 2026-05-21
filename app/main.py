"""
AI Welding Inspection System — FastAPI Application Entry Point
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger

from app.core.config import settings
from app.api.v1.router import api_router
from app.db.session import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run on startup and shutdown."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    # Create all DB tables on startup (use Alembic migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created")
    yield
    logger.info("Shutting down...")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## AI-Based Welding Inspection & Dimension Measurement System

### Features
- 🔐 JWT Authentication with role-based access
- 🏗️ Object/Part management
- 🔍 Full inspection lifecycle (Create → Upload → Submit → AI Analysis)
- 🤖 Google Gemini AI weld defect detection
- 📊 PDF & Excel report generation
- ☁️ AWS S3 image storage
- 📈 Dashboard analytics

### Workflow
1. Register/Login to get JWT token
2. Create an Object (weld part)
3. Create an Inspection for that Object
4. Upload panorama image(s)
5. Submit → AI analysis runs automatically
6. Download PDF/Excel report
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Exception Handler ───────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error", "data": None}
    )


# ── Include All Routes ─────────────────────────────────────────────────────
app.include_router(api_router)


# ── Health Check ───────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/", tags=["Health"])
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}", "docs": "/docs"}
