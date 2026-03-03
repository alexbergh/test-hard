"""Health check endpoints."""

from app.config import get_settings
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

router = APIRouter()
settings = get_settings()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    environment: str
    database: str


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    status: str
    database: str
    scheduler: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint with database connectivity verification."""
    from app.database import get_session_context

    db_status = "connected"
    try:
        async with get_session_context() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    overall = "healthy" if db_status == "connected" else "degraded"

    return HealthResponse(
        status=overall,
        version=settings.app_version,
        environment=settings.environment,
        database=db_status,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """Readiness check with dependency status."""
    from app.services.scheduler import scheduler_service

    # Check database
    from app.database import get_session_context

    db_status = "healthy"
    try:
        async with get_session_context() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    # Check scheduler
    scheduler_status = "healthy" if scheduler_service.scheduler.running else "stopped"

    overall_status = "ready" if db_status == "healthy" else "not_ready"

    return ReadinessResponse(
        status=overall_status,
        database=db_status,
        scheduler=scheduler_status,
    )
