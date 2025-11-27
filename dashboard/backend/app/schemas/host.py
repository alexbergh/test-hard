"""Host schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class HostCreate(BaseModel):
    """Schema for creating a new host."""

    name: str = Field(..., min_length=1, max_length=255)
    display_name: str | None = None
    description: str | None = None
    host_type: str = "container"  # container, ssh, local
    address: str | None = None
    port: int | None = None
    ssh_user: str | None = None
    ssh_key_path: str | None = None
    os_family: str | None = None
    os_version: str | None = None
    enabled_scanners: dict = Field(default_factory=lambda: {"openscap": True, "lynis": True})
    scan_profile: str | None = None
    tags: list[str] = Field(default_factory=list)


class HostUpdate(BaseModel):
    """Schema for updating a host."""

    display_name: str | None = None
    description: str | None = None
    address: str | None = None
    port: int | None = None
    ssh_user: str | None = None
    ssh_key_path: str | None = None
    os_family: str | None = None
    os_version: str | None = None
    is_active: bool | None = None
    enabled_scanners: dict | None = None
    scan_profile: str | None = None
    tags: list[str] | None = None


class HostResponse(BaseModel):
    """Schema for host response."""

    id: int
    name: str
    display_name: str | None
    description: str | None
    host_type: str
    address: str | None
    port: int | None
    ssh_user: str | None
    os_family: str | None
    os_version: str | None
    architecture: str | None
    status: str
    is_active: bool
    enabled_scanners: dict
    scan_profile: str | None
    last_scan_id: int | None
    last_scan_score: int | None
    tags: list
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
