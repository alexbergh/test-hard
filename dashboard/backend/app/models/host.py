"""Host model for scan targets."""

from typing import TYPE_CHECKING, Literal

from app.models.base import Base, TimestampMixin
from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.cluster import Cluster
    from app.models.scan import Scan, ScanSchedule

HostType = Literal["container", "ssh", "local", "k8s_node", "k8s_pod"]
HostStatus = Literal["online", "offline", "unknown", "scanning"]


class Host(Base, TimestampMixin):
    """Host model representing a scan target."""

    __tablename__ = "hosts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Connection settings
    host_type: Mapped[str] = mapped_column(String(50), default="container")  # container, ssh, local
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)  # IP or container name
    port: Mapped[int | None] = mapped_column(nullable=True)  # SSH port
    ssh_user: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ssh_key_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Host info
    os_family: Mapped[str | None] = mapped_column(String(50), nullable=True)  # debian, fedora, centos, etc.
    os_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    architecture: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="unknown")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Scan settings
    enabled_scanners: Mapped[dict] = mapped_column(JSON, default=lambda: {"openscap": True, "lynis": True})
    scan_profile: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Last scan info
    last_scan_id: Mapped[int | None] = mapped_column(nullable=True)
    last_scan_score: Mapped[int | None] = mapped_column(nullable=True)

    # Cluster association (optional -- None for standalone Docker hosts)
    cluster_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True
    )

    # Kubernetes metadata (populated for k8s_node / k8s_pod)
    k8s_namespace: Mapped[str | None] = mapped_column(String(255), nullable=True)
    k8s_pod_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    k8s_node_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    k8s_labels: Mapped[dict] = mapped_column(JSON, default=dict)
    k8s_annotations: Mapped[dict] = mapped_column(JSON, default=dict)
    container_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    container_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    container_runtime: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # docker, containerd, cri-o

    # Security context (extracted from K8s pod spec or Docker inspect)
    security_context: Mapped[dict] = mapped_column(JSON, default=dict)

    # Tags for filtering
    tags: Mapped[list] = mapped_column(JSON, default=list)

    # Relationships
    cluster: Mapped["Cluster | None"] = relationship("Cluster", back_populates="hosts")
    scans: Mapped[list["Scan"]] = relationship("Scan", back_populates="host")
    schedules: Mapped[list["ScanSchedule"]] = relationship("ScanSchedule", back_populates="host")

    def __repr__(self) -> str:
        return f"<Host(id={self.id}, name={self.name}, type={self.host_type}, status={self.status})>"
