"""Scheduled scanning service using APScheduler."""

import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from app.config import get_settings
from app.database import get_session_context
from app.models import Scan, ScanSchedule
from app.models.scan import ScanResult
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import delete, select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession  # noqa: F401

settings = get_settings()
logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing scheduled scans."""

    _instance: "SchedulerService | None" = None
    _scheduler: AsyncIOScheduler | None = None

    def __new__(cls) -> "SchedulerService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._scheduler is None:
            self._scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)

    @property
    def scheduler(self) -> AsyncIOScheduler:
        """Get the scheduler instance."""
        if self._scheduler is None:
            self._scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)
        return self._scheduler

    async def start(self) -> None:
        """Start the scheduler and load all active schedules."""
        if not settings.scheduler_enabled:
            logger.info("Scheduler is disabled")
            return

        if self.scheduler.running:
            logger.warning("Scheduler is already running")
            return

        # Load existing schedules from database
        await self._load_schedules()

        # Add daily cleanup job for scan retention (30 days)
        self.scheduler.add_job(
            self._cleanup_old_scans,
            CronTrigger(hour=3, minute=0),
            id="scan_retention_cleanup",
            name="Scan retention cleanup (30 days)",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("Scheduler started")

    async def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")

    async def _load_schedules(self) -> None:
        """Load all active schedules from database."""
        async with get_session_context() as session:
            result = await session.execute(select(ScanSchedule).where(ScanSchedule.is_active == True))  # noqa: E712
            schedules = result.scalars().all()

            for schedule in schedules:
                self.add_schedule(schedule)
                logger.info(f"Loaded schedule: {schedule.name} (ID: {schedule.id})")

    def add_schedule(self, schedule: ScanSchedule) -> None:
        """Add a scan schedule to the scheduler."""
        job_id = f"scan_schedule_{schedule.id}"

        # Remove existing job if any
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        # Parse cron expression
        try:
            trigger = CronTrigger.from_crontab(
                schedule.cron_expression,
                timezone=schedule.timezone,
            )
        except ValueError as e:
            logger.error(f"Invalid cron expression for schedule {schedule.id}: {e}")
            return

        # Add job
        self.scheduler.add_job(
            self._execute_scheduled_scan,
            trigger=trigger,
            id=job_id,
            args=[schedule.id],
            name=schedule.name,
            replace_existing=True,
        )

        logger.info(f"Added schedule job: {schedule.name} ({schedule.cron_expression})")

    def remove_schedule(self, schedule_id: int) -> None:
        """Remove a scan schedule from the scheduler."""
        job_id = f"scan_schedule_{schedule_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed schedule job: {job_id}")

    def update_schedule(self, schedule: ScanSchedule) -> None:
        """Update an existing schedule."""
        if schedule.is_active:
            self.add_schedule(schedule)
        else:
            self.remove_schedule(schedule.id)

    async def _execute_scheduled_scan(self, schedule_id: int) -> None:
        """Execute a scheduled scan."""
        logger.info(f"Executing scheduled scan: {schedule_id}")

        async with get_session_context() as session:
            # Get schedule
            schedule = await session.get(ScanSchedule, schedule_id)
            if not schedule or not schedule.is_active:
                logger.warning(f"Schedule {schedule_id} not found or inactive")
                return

            # Create scan
            scan = Scan(
                host_id=schedule.host_id,
                user_id=schedule.user_id,
                schedule_id=schedule.id,
                scanner=schedule.scanner,
                profile=schedule.profile,
                status="pending",
            )
            session.add(scan)

            # Update schedule tracking
            schedule.last_run_at = datetime.now(timezone.utc)
            schedule.run_count += 1

            # Calculate next run
            job = self.scheduler.get_job(f"scan_schedule_{schedule_id}")
            if job and job.next_run_time:
                schedule.next_run_at = job.next_run_time

            await session.commit()
            await session.refresh(scan)

            logger.info(f"Created scan {scan.id} from schedule {schedule_id}")

            # Start scan execution
            from app.services.scan import ScanService

            scan_service = ScanService(session)
            await scan_service.start_scan(scan.id)

    async def _cleanup_old_scans(self) -> None:
        """Remove scans older than 30 days to enforce retention policy."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        logger.info(f"Running scan retention cleanup, removing scans before {cutoff}")

        async with get_session_context() as session:
            # Find old scan IDs
            result = await session.execute(select(Scan.id).where(Scan.created_at < cutoff))
            old_ids = [row[0] for row in result.all()]

            if old_ids:
                # Delete results first (cascade should handle it, but be explicit)
                await session.execute(delete(ScanResult).where(ScanResult.scan_id.in_(old_ids)))
                # Delete scans
                await session.execute(delete(Scan).where(Scan.id.in_(old_ids)))
                await session.commit()
                logger.info(f"Cleaned up {len(old_ids)} scans older than 30 days")
            else:
                logger.info("No old scans to clean up")

    async def get_schedule_status(self, schedule_id: int) -> dict | None:
        """Get status of a scheduled job."""
        job_id = f"scan_schedule_{schedule_id}"
        job = self.scheduler.get_job(job_id)

        if not job:
            return None

        return {
            "id": schedule_id,
            "job_id": job_id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "pending": job.pending,
        }

    def get_all_jobs(self) -> list[dict]:
        """Get all scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "pending": job.pending,
                }
            )
        return jobs


# Singleton instance
scheduler_service = SchedulerService()
