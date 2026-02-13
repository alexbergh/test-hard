"""API routes."""

from app.api import auth, dashboard, health, hosts, notifications, scans, schedules, users
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(hosts.router, prefix="/hosts", tags=["hosts"])
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["schedules"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
