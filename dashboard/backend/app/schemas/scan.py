"""Scan schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ScanCreate(BaseModel):
    """Schema for creating a new scan."""

    host_id: int
    scanner: str = "lynis"  # openscap, lynis, trivy, atomic
    profile: str | None = None


class ScanSummary(BaseModel):
    """Schema for scan summary in lists."""

    id: int
    host_id: int
    host_name: str | None = None
    scanner: str
    status: str
    score: int | None
    passed: int
    failed: int
    warnings: int
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: int | None

    model_config = {"from_attributes": True}


class ScanResultResponse(BaseModel):
    """Schema for individual scan result."""

    id: int
    rule_id: str
    title: str
    description: str | None
    severity: str
    status: str
    category: str | None
    remediation: str | None
    references: list

    model_config = {"from_attributes": True}


class ScanResponse(BaseModel):
    """Schema for full scan response."""

    id: int
    host_id: int
    user_id: int | None
    schedule_id: int | None
    scanner: str
    profile: str | None
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: int | None
    score: int | None
    passed: int
    failed: int
    warnings: int
    errors: int
    report_path: str | None
    html_report_path: str | None
    error_message: str | None
    created_at: datetime
    results: list[ScanResultResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ScanScheduleCreate(BaseModel):
    """Schema for creating a scan schedule."""

    host_id: int
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    scanner: str = "lynis"
    profile: str | None = None
    cron_expression: str = Field(..., pattern=r"^[\d\*\/\-\,\s]+$")  # Basic cron validation
    timezone: str = "UTC"
    notify_on_completion: bool = True
    notify_on_failure: bool = True
    notification_channels: list[str] = Field(default_factory=list)


class ScanScheduleUpdate(BaseModel):
    """Schema for updating a scan schedule."""

    name: str | None = None
    description: str | None = None
    scanner: str | None = None
    profile: str | None = None
    cron_expression: str | None = None
    timezone: str | None = None
    is_active: bool | None = None
    notify_on_completion: bool | None = None
    notify_on_failure: bool | None = None
    notification_channels: list[str] | None = None


class ScanScheduleResponse(BaseModel):
    """Schema for scan schedule response."""

    id: int
    host_id: int
    user_id: int
    name: str
    description: str | None
    scanner: str
    profile: str | None
    cron_expression: str
    timezone: str
    is_active: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    run_count: int
    notify_on_completion: bool
    notify_on_failure: bool
    notification_channels: list
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
