"""User model for authentication."""

from typing import TYPE_CHECKING

from app.models.base import Base, TimestampMixin
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.scan import Scan, ScanSchedule


class User(Base, TimestampMixin):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String(50), default="viewer")  # viewer, operator, admin

    # Relationships
    scans: Mapped[list["Scan"]] = relationship("Scan", back_populates="user")
    schedules: Mapped[list["ScanSchedule"]] = relationship("ScanSchedule", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
