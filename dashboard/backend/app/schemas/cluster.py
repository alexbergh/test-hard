"""Cluster schemas for API."""

from datetime import datetime

from pydantic import BaseModel, Field


class ClusterCreate(BaseModel):
    """Schema for creating a new cluster connection."""

    name: str = Field(..., min_length=1, max_length=255)
    display_name: str | None = None
    description: str | None = None
    cluster_type: str = "kubernetes"  # kubernetes, docker, containerd

    # Kubernetes
    k8s_api_url: str | None = None  # https://host:6443
    k8s_token: str | None = None
    k8s_ca_cert: str | None = None
    k8s_client_cert: str | None = None
    k8s_client_key: str | None = None
    kubeconfig_path: str | None = None
    kubeconfig_context: str | None = None
    k8s_namespace: str | None = None  # None = all namespaces

    # Docker
    docker_host: str | None = None  # tcp://host:2376 or unix:///...
    docker_tls_verify: bool = False
    docker_cert_path: str | None = None

    # containerd
    containerd_socket: str | None = None

    # Settings
    auto_discover: bool = True
    discover_filter: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class ClusterUpdate(BaseModel):
    """Schema for updating a cluster."""

    display_name: str | None = None
    description: str | None = None
    k8s_api_url: str | None = None
    k8s_token: str | None = None
    k8s_ca_cert: str | None = None
    k8s_client_cert: str | None = None
    k8s_client_key: str | None = None
    kubeconfig_path: str | None = None
    kubeconfig_context: str | None = None
    k8s_namespace: str | None = None
    docker_host: str | None = None
    docker_tls_verify: bool | None = None
    docker_cert_path: str | None = None
    containerd_socket: str | None = None
    is_active: bool | None = None
    auto_discover: bool | None = None
    discover_filter: dict | None = None
    tags: list[str] | None = None


class ClusterResponse(BaseModel):
    """Schema for cluster response."""

    id: int
    name: str
    display_name: str | None
    description: str | None
    cluster_type: str
    k8s_api_url: str | None
    kubeconfig_path: str | None
    kubeconfig_context: str | None
    k8s_namespace: str | None
    docker_host: str | None
    docker_tls_verify: bool
    containerd_socket: str | None
    status: str
    is_active: bool
    last_error: str | None
    auto_discover: bool
    discover_filter: dict
    cluster_version: str | None
    node_count: int | None
    pod_count: int | None
    namespace_count: int | None
    tags: list
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClusterTestResult(BaseModel):
    """Schema for cluster connection test result."""

    success: bool
    cluster_type: str
    message: str
    version: str | None = None
    node_count: int | None = None
    pod_count: int | None = None
    namespace_count: int | None = None
    container_count: int | None = None


class DiscoveryResult(BaseModel):
    """Schema for discovery result."""

    cluster_id: int
    cluster_name: str
    hosts_created: int
    hosts_updated: int
    hosts_total: int
    details: list[dict] = Field(default_factory=list)
