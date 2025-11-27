"""Scan models for tracking scan jobs and results."""

from datetime import datetime
from typing import TYPE_CHECKING, Literal

from app.models.base import Base, TimestampMixin
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.host import Host
    from app.models.user import User

ScanStatus = Literal["pending", "running", "completed", "failed", "cancelled"]
ScannerType = Literal["openscap", "lynis", "trivy", "atomic"]


class Scan(Base, TimestampMixin):
    """Scan job model."""

    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Relations
    host_id: Mapped[int] = mapped_column(ForeignKey("hosts.id"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    schedule_id: Mapped[int | None] = mapped_column(ForeignKey("scan_schedules.id"), nullable=True)

    # Scan info
    scanner: Mapped[str] = mapped_column(String(50))  # openscap, lynis, trivy, atomic
    profile: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(nullable=True)

    # Results summary
    score: Mapped[int | None] = mapped_column(nullable=True)  # 0-100
    passed: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    warnings: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[int] = mapped_column(Integer, default=0)

    # Report paths
    report_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    html_report_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Error info
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    host: Mapped["Host"] = relationship("Host", back_populates="scans")
    user: Mapped["User | None"] = relationship("User", back_populates="scans")
    schedule: Mapped["ScanSchedule | None"] = relationship("ScanSchedule", back_populates="scans")
    results: Mapped[list["ScanResult"]] = relationship(
        "ScanResult", back_populates="scan", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Scan(id={self.id}, host_id={self.host_id}, scanner={self.scanner}, status={self.status})>"


class ScanResult(Base):
    """Individual scan result/finding."""

    __tablename__ = "scan_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)

    # Result info
    rule_id: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20))  # critical, high, medium, low, info
    status: Mapped[str] = mapped_column(String(20))  # pass, fail, error, notapplicable
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Remediation
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    references: Mapped[list] = mapped_column(JSON, default=list)

    # Relationship
    scan: Mapped["Scan"] = relationship("Scan", back_populates="results")

    def __repr__(self) -> str:
        return f"<ScanResult(id={self.id}, rule_id={self.rule_id}, status={self.status})>"


class ScanSchedule(Base, TimestampMixin):
    """Scheduled scan configuration."""

    __tablename__ = "scan_schedules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Relations
    host_id: Mapped[int] = mapped_column(ForeignKey("hosts.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Schedule info
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scanner: Mapped[str] = mapped_column(String(50))
    profile: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Cron expression
    cron_expression: Mapped[str] = mapped_column(String(100))  # e.g., "0 2 * * *"
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    is_active: Mapped[bool] = mapped_column(default=True)

    # Execution tracking
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    run_count: Mapped[int] = mapped_column(Integer, default=0)

    # Notification settings
    notify_on_completion: Mapped[bool] = mapped_column(default=True)
    notify_on_failure: Mapped[bool] = mapped_column(default=True)
    notification_channels: Mapped[list] = mapped_column(JSON, default=list)  # ["email", "slack"]

    # Relationships
    host: Mapped["Host"] = relationship("Host", back_populates="schedules")
    user: Mapped["User"] = relationship("User", back_populates="schedules")
    scans: Mapped[list["Scan"]] = relationship("Scan", back_populates="schedule")

    def __repr__(self) -> str:
        return f"<ScanSchedule(id={self.id}, name={self.name}, cron={self.cron_expression})>"
