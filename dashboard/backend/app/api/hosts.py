"""Host management endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AdminUser, CurrentUser, DbSession, OperatorUser
from app.schemas import HostCreate, HostResponse, HostUpdate
from app.services.host import HostService

router = APIRouter()


@router.get("", response_model=list[HostResponse])
async def list_hosts(
    session: DbSession,
    current_user: CurrentUser,
    include_inactive: bool = False,
) -> list[HostResponse]:
    """List all hosts."""
    host_service = HostService(session)
    hosts = await host_service.get_all_hosts(include_inactive=include_inactive)
    return [HostResponse.model_validate(h) for h in hosts]


@router.get("/{host_id}", response_model=HostResponse)
async def get_host(
    host_id: int,
    session: DbSession,
    current_user: CurrentUser,
) -> HostResponse:
    """Get host by ID."""
    host_service = HostService(session)
    host = await host_service.get_host_by_id(host_id)

    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host not found",
        )

    return HostResponse.model_validate(host)


@router.post("", response_model=HostResponse, status_code=status.HTTP_201_CREATED)
async def create_host(
    host_data: HostCreate,
    session: DbSession,
    current_user: OperatorUser,
) -> HostResponse:
    """Create a new host."""
    host_service = HostService(session)

    # Check if host name exists
    existing = await host_service.get_host_by_name(host_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Host with this name already exists",
        )

    host = await host_service.create_host(host_data)
    return HostResponse.model_validate(host)


@router.patch("/{host_id}", response_model=HostResponse)
async def update_host(
    host_id: int,
    host_data: HostUpdate,
    session: DbSession,
    current_user: OperatorUser,
) -> HostResponse:
    """Update an existing host."""
    host_service = HostService(session)
    host = await host_service.update_host(host_id, host_data)

    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host not found",
        )

    return HostResponse.model_validate(host)


@router.delete("/{host_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_host(
    host_id: int,
    session: DbSession,
    current_user: AdminUser,
) -> None:
    """Delete a host."""
    host_service = HostService(session)
    deleted = await host_service.delete_host(host_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host not found",
        )


@router.post("/{host_id}/check-status", response_model=dict)
async def check_host_status(
    host_id: int,
    session: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Check host connectivity status."""
    host_service = HostService(session)
    host = await host_service.get_host_by_id(host_id)

    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host not found",
        )

    status_result = await host_service.check_host_status(host)
    return {"host_id": host_id, "status": status_result}


@router.post("/sync-docker", response_model=list[HostResponse])
async def sync_docker_containers(
    session: DbSession,
    current_user: OperatorUser,
) -> list[HostResponse]:
    """Sync hosts from running Docker containers."""
    host_service = HostService(session)
    created_hosts = await host_service.sync_docker_containers()
    return [HostResponse.model_validate(h) for h in created_hosts]
