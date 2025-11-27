"""FastAPI application entry point."""

import logging
import traceback
from contextlib import asynccontextmanager

from app.api import api_router
from app.config import get_settings
from app.database import init_db
from app.services.scheduler import scheduler_service
from app.tracing import setup_tracing
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Start scheduler
    await scheduler_service.start()

    yield

    # Shutdown
    logger.info("Shutting down...")
    await scheduler_service.stop()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Security Hardening & Monitoring Dashboard API",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup tracing
    setup_tracing(app)

    # Mount Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    # Global exception handler for debugging
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        error_detail = traceback.format_exc()
        logger.error(f"Unhandled exception: {error_detail}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "traceback": error_detail},
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
