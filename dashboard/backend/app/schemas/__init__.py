"""Pydantic schemas for API."""

from app.schemas.auth import EmailUpdate, PasswordChange, RefreshTokenRequest, Token, TokenData, UserCreate, UserLogin, UserResponse
from app.schemas.cluster import ClusterCreate, ClusterResponse, ClusterTestResult, ClusterUpdate, DiscoveryResult
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
    "EmailUpdate",
    "PasswordChange",
    "RefreshTokenRequest",
    "Token",
    "TokenData",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "ClusterCreate",
    "ClusterResponse",
    "ClusterTestResult",
    "ClusterUpdate",
    "DiscoveryResult",
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
