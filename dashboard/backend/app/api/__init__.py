"""API routes."""

from fastapi import APIRouter

from app.api import auth, hosts, scans, schedules, health

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(hosts.router, prefix="/hosts", tags=["hosts"])
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["schedules"])
