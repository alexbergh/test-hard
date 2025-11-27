"""Scan schedule management endpoints."""

from datetime import datetime, timezone

from app.api.deps import CurrentUser, DbSession, OperatorUser
from app.models import ScanSchedule
from app.schemas import ScanScheduleCreate, ScanScheduleResponse, ScanScheduleUpdate
from app.services.scheduler import scheduler_service
from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

router = APIRouter()


@router.get("", response_model=list[ScanScheduleResponse])
async def list_schedules(
    session: DbSession,
    current_user: CurrentUser,
    host_id: int | None = None,
    active_only: bool = True,
) -> list[ScanScheduleResponse]:
    """List all scan schedules."""
    query = select(ScanSchedule)

    if host_id:
        query = query.where(ScanSchedule.host_id == host_id)
    if active_only:
        query = query.where(ScanSchedule.is_active == True)  # noqa: E712

    query = query.order_by(ScanSchedule.name)
    result = await session.execute(query)
    schedules = result.scalars().all()

    return [ScanScheduleResponse.model_validate(s) for s in schedules]


@router.get("/{schedule_id}", response_model=ScanScheduleResponse)
async def get_schedule(
    schedule_id: int,
    session: DbSession,
    current_user: CurrentUser,
) -> ScanScheduleResponse:
    """Get schedule by ID."""
    schedule = await session.get(ScanSchedule, schedule_id)

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    return ScanScheduleResponse.model_validate(schedule)


@router.post("", response_model=ScanScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScanScheduleCreate,
    session: DbSession,
    current_user: OperatorUser,
) -> ScanScheduleResponse:
    """Create a new scan schedule."""
    # Validate cron expression
    try:
        trigger = CronTrigger.from_crontab(schedule_data.cron_expression)
        next_run = trigger.get_next_fire_time(None, datetime.now(timezone.utc))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid cron expression: {e}",
        )

    schedule = ScanSchedule(
        host_id=schedule_data.host_id,
        user_id=current_user.id,
        name=schedule_data.name,
        description=schedule_data.description,
        scanner=schedule_data.scanner,
        profile=schedule_data.profile,
        cron_expression=schedule_data.cron_expression,
        timezone=schedule_data.timezone,
        next_run_at=next_run,
        notify_on_completion=schedule_data.notify_on_completion,
        notify_on_failure=schedule_data.notify_on_failure,
        notification_channels=schedule_data.notification_channels,
    )

    session.add(schedule)
    await session.flush()
    await session.refresh(schedule)

    # Add to scheduler
    scheduler_service.add_schedule(schedule)

    return ScanScheduleResponse.model_validate(schedule)


@router.patch("/{schedule_id}", response_model=ScanScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: ScanScheduleUpdate,
    session: DbSession,
    current_user: OperatorUser,
) -> ScanScheduleResponse:
    """Update an existing schedule."""
    schedule = await session.get(ScanSchedule, schedule_id)

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    # Validate new cron expression if provided
    if schedule_data.cron_expression:
        try:
            trigger = CronTrigger.from_crontab(schedule_data.cron_expression)
            next_run = trigger.get_next_fire_time(None, datetime.now(timezone.utc))
            schedule.next_run_at = next_run
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid cron expression: {e}",
            )

    # Update fields
    update_data = schedule_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)

    await session.flush()
    await session.refresh(schedule)

    # Update scheduler
    scheduler_service.update_schedule(schedule)

    return ScanScheduleResponse.model_validate(schedule)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    session: DbSession,
    current_user: OperatorUser,
) -> None:
    """Delete a schedule."""
    schedule = await session.get(ScanSchedule, schedule_id)

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    # Remove from scheduler
    scheduler_service.remove_schedule(schedule_id)

    await session.delete(schedule)


@router.post("/{schedule_id}/toggle", response_model=ScanScheduleResponse)
async def toggle_schedule(
    schedule_id: int,
    session: DbSession,
    current_user: OperatorUser,
) -> ScanScheduleResponse:
    """Toggle schedule active status."""
    schedule = await session.get(ScanSchedule, schedule_id)

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    schedule.is_active = not schedule.is_active

    if schedule.is_active:
        # Recalculate next run time
        try:
            trigger = CronTrigger.from_crontab(schedule.cron_expression)
            schedule.next_run_at = trigger.get_next_fire_time(None, datetime.now(timezone.utc))
        except ValueError:
            pass

    await session.flush()
    await session.refresh(schedule)

    # Update scheduler
    scheduler_service.update_schedule(schedule)

    return ScanScheduleResponse.model_validate(schedule)


@router.get("/jobs/status", response_model=list[dict])
async def get_scheduler_jobs(
    current_user: CurrentUser,
) -> list[dict]:
    """Get all active scheduler jobs."""
    return scheduler_service.get_all_jobs()
