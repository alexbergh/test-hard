"""FastAPI application entry point."""

import asyncio
import contextlib
import logging
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api import api_router
from app.config import get_settings
from app.database import init_db
from app.services.scheduler import scheduler_service
from app.tracing import setup_tracing

settings = get_settings()

# Configure logging
log_level = logging.DEBUG if settings.debug else logging.INFO

if settings.environment == "production":
    from pythonjsonlogger import jsonlogger

    handler = logging.StreamHandler()
    handler.setFormatter(
        jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            rename_fields={"asctime": "timestamp", "levelname": "level"},
        )
    )
    logging.root.handlers = [handler]
    logging.root.setLevel(log_level)
else:
    logging.basicConfig(
        level=log_level,
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

    # Start WebSocket broadcast worker
    from app.services.ws_manager import message_queue, ws_manager

    async def _ws_broadcast_worker():
        while True:
            try:
                msg = await message_queue.get()
                await ws_manager.broadcast(msg)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("WS broadcast error: %s", e)

    ws_task = asyncio.create_task(_ws_broadcast_worker())  # noqa: F823

    yield

    ws_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await ws_task

    # Shutdown
    logger.info("Shutting down...")

    # Cancel running scan tasks gracefully
    from app.services.scan import _background_tasks

    if _background_tasks:
        logger.info("Cancelling %d running scan task(s)...", len(_background_tasks))
        for task in _background_tasks:
            task.cancel()
        import asyncio

        results = await asyncio.gather(*_background_tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception) and not isinstance(r, asyncio.CancelledError):
                logger.error("Scan task error during shutdown: %s", r)
        logger.info("All scan tasks stopped")

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

    # Rate limiter
    limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )

    # Setup tracing
    setup_tracing(app)

    # Mount Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # Include API routes (v1 is current, v2 reserved for future)
    app.include_router(api_router, prefix="/api/v1")

    # API version deprecation middleware
    @app.middleware("http")
    async def api_version_header(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-API-Version"] = "v1"
        if request.url.path.startswith("/api/v1"):
            response.headers["X-API-Supported-Versions"] = "v1"
        return response

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        error_detail = traceback.format_exc()
        logger.error(f"Unhandled exception: {error_detail}")
        if settings.debug:
            content = {"detail": str(exc), "traceback": error_detail}
        else:
            content = {"detail": "Internal server error"}
        return JSONResponse(status_code=500, content=content)

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
