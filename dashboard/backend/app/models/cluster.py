"""Cluster model for Kubernetes and Podman connections."""

from typing import TYPE_CHECKING, Literal

from sqlalchemy import JSON, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.host import Host

ClusterType = Literal["kubernetes", "podman", "containerd"]
ClusterStatus = Literal["connected", "disconnected", "error", "unknown"]


class Cluster(Base, TimestampMixin):
    """Cluster model representing a K8s or Podman connection target."""

    __tablename__ = "clusters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Connection type: kubernetes, podman, containerd
    cluster_type: Mapped[str] = mapped_column(String(50), default="kubernetes")

    # Kubernetes connection settings
    k8s_api_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    k8s_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    k8s_ca_cert: Mapped[str | None] = mapped_column(Text, nullable=True)
    k8s_client_cert: Mapped[str | None] = mapped_column(Text, nullable=True)
    k8s_client_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    kubeconfig_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    kubeconfig_context: Mapped[str | None] = mapped_column(String(255), nullable=True)
    k8s_namespace: Mapped[str | None] = mapped_column(String(255), nullable=True)  # None = all namespaces

    # Podman connection settings
    podman_host: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )  # tcp://host:2376 or unix:///run/podman/podman.sock
    podman_tls_verify: Mapped[bool] = mapped_column(Boolean, default=False)
    podman_cert_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # containerd connection settings
    containerd_socket: Mapped[str | None] = mapped_column(String(500), nullable=True)  # /run/containerd/containerd.sock

    # Status
    status: Mapped[str] = mapped_column(String(20), default="unknown")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Discovery settings
    auto_discover: Mapped[bool] = mapped_column(Boolean, default=True)
    discover_filter: Mapped[dict] = mapped_column(JSON, default=dict)  # label selectors, namespace filters

    # Cluster info (populated after connection)
    cluster_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    node_count: Mapped[int | None] = mapped_column(nullable=True)
    pod_count: Mapped[int | None] = mapped_column(nullable=True)
    namespace_count: Mapped[int | None] = mapped_column(nullable=True)

    # Tags
    tags: Mapped[list] = mapped_column(JSON, default=list)

    # Relationships
    hosts: Mapped[list["Host"]] = relationship("Host", back_populates="cluster")

    def __repr__(self) -> str:
        return f"<Cluster(id={self.id}, name={self.name}, type={self.cluster_type}, status={self.status})>"
