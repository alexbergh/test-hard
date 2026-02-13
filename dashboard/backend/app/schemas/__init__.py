"""Pydantic schemas for API."""

from app.schemas.auth import PasswordChange, Token, TokenData, UserCreate, UserLogin, UserResponse
from app.schemas.host import HostCreate, HostResponse, HostUpdate
from app.schemas.scan import (
    ScanCreate,
    ScanResponse,
    ScanResultResponse,
    ScanScheduleCreate,
    ScanScheduleResponse,
    ScanScheduleUpdate,
    ScanSummary,
)

__all__ = [
    "PasswordChange",
    "Token",
    "TokenData",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "HostCreate",
    "HostResponse",
    "HostUpdate",
    "ScanCreate",
    "ScanResponse",
    "ScanResultResponse",
    "ScanScheduleCreate",
    "ScanScheduleResponse",
    "ScanScheduleUpdate",
    "ScanSummary",
]
