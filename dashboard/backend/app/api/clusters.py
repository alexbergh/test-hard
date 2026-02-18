"""Cluster management and discovery API endpoints."""

import asyncio
import logging

from app.api.deps import AdminUser, CurrentUser, DbSession, OperatorUser
from app.models import Cluster
from app.schemas.cluster import ClusterCreate, ClusterResponse, ClusterTestResult, ClusterUpdate, DiscoveryResult
from app.services.discovery import DiscoveryService
from app.services.k8s_connector import K8sConnector
from app.services.k8s_hardening import K8sHardeningScanner
from fastapi import APIRouter, HTTPException, status

logger = logging.getLogger(__name__)

router = APIRouter()


# ------------------------------------------------------------------
# Cluster CRUD
# ------------------------------------------------------------------


@router.get("", response_model=list[ClusterResponse])
async def list_clusters(
    session: DbSession,
    current_user: CurrentUser,
    include_inactive: bool = False,
) -> list[ClusterResponse]:
    """List all clusters."""
    svc = DiscoveryService(session)
    clusters = await svc.get_all_clusters(include_inactive=include_inactive)
    return [ClusterResponse.model_validate(c) for c in clusters]


@router.get("/{cluster_id}", response_model=ClusterResponse)
async def get_cluster(
    cluster_id: int,
    session: DbSession,
    current_user: CurrentUser,
) -> ClusterResponse:
    """Get cluster by ID."""
    svc = DiscoveryService(session)
    cluster = await svc.get_cluster_by_id(cluster_id)
    if not cluster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")
    return ClusterResponse.model_validate(cluster)


@router.post("", response_model=ClusterResponse, status_code=status.HTTP_201_CREATED)
async def create_cluster(
    data: ClusterCreate,
    session: DbSession,
    current_user: AdminUser,
) -> ClusterResponse:
    """Create a new cluster connection."""
    svc = DiscoveryService(session)

    existing = await svc.get_cluster_by_name(data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cluster with this name already exists",
        )

    cluster = await svc.create_cluster(data)
    return ClusterResponse.model_validate(cluster)


@router.patch("/{cluster_id}", response_model=ClusterResponse)
async def update_cluster(
    cluster_id: int,
    data: ClusterUpdate,
    session: DbSession,
    current_user: AdminUser,
) -> ClusterResponse:
    """Update a cluster connection."""
    svc = DiscoveryService(session)
    cluster = await svc.update_cluster(cluster_id, data)
    if not cluster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")
    return ClusterResponse.model_validate(cluster)


@router.delete("/{cluster_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cluster(
    cluster_id: int,
    session: DbSession,
    current_user: AdminUser,
) -> None:
    """Delete a cluster and disassociate its hosts."""
    svc = DiscoveryService(session)
    deleted = await svc.delete_cluster(cluster_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")


# ------------------------------------------------------------------
# Connection test
# ------------------------------------------------------------------


@router.post("/{cluster_id}/test", response_model=ClusterTestResult)
async def test_cluster_connection(
    cluster_id: int,
    session: DbSession,
    current_user: OperatorUser,
) -> ClusterTestResult:
    """Test cluster connection and return info."""
    svc = DiscoveryService(session)
    cluster = await svc.get_cluster_by_id(cluster_id)
    if not cluster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")

    result = await svc.test_connection(cluster)

    # Update cluster status based on test
    if result.get("success"):
        cluster.status = "connected"
        cluster.last_error = None
        if result.get("version"):
            cluster.cluster_version = result["version"]
        if result.get("node_count") is not None:
            cluster.node_count = result["node_count"]
        if result.get("pod_count") is not None:
            cluster.pod_count = result["pod_count"]
        if result.get("namespace_count") is not None:
            cluster.namespace_count = result["namespace_count"]
    else:
        cluster.status = "error"
        cluster.last_error = result.get("message", "Connection test failed")

    await session.flush()
    return ClusterTestResult(**result)


# ------------------------------------------------------------------
# Discovery
# ------------------------------------------------------------------


@router.post("/{cluster_id}/discover", response_model=DiscoveryResult)
async def discover_cluster(
    cluster_id: int,
    session: DbSession,
    current_user: OperatorUser,
) -> DiscoveryResult:
    """Discover hosts from cluster (pods, nodes, containers) and sync to DB."""
    svc = DiscoveryService(session)
    cluster = await svc.get_cluster_by_id(cluster_id)
    if not cluster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")
    if not cluster.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cluster is inactive")

    if cluster.cluster_type == "kubernetes":
        result = await svc.sync_k8s_hosts(cluster)
    elif cluster.cluster_type == "docker":
        result = await svc.sync_docker_hosts(cluster)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported cluster type: {cluster.cluster_type}",
        )

    return DiscoveryResult(**result)


# ------------------------------------------------------------------
# K8s Hardening Scan
# ------------------------------------------------------------------


@router.post("/{cluster_id}/hardening-scan", response_model=dict)
async def run_hardening_scan(
    cluster_id: int,
    session: DbSession,
    current_user: OperatorUser,
    namespace: str | None = None,
) -> dict:
    """Run Kubernetes hardening checks against the cluster."""
    svc = DiscoveryService(session)
    cluster = await svc.get_cluster_by_id(cluster_id)
    if not cluster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")
    if cluster.cluster_type != "kubernetes":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hardening scan is only supported for Kubernetes clusters",
        )

    scan_ns = namespace or cluster.k8s_namespace
    result = await asyncio.to_thread(_run_k8s_hardening, cluster, scan_ns)
    return result


def _run_k8s_hardening(cluster: Cluster, namespace: str | None) -> dict:
    """Run K8s hardening scan synchronously (called from thread)."""
    connector = K8sConnector(
        api_url=cluster.k8s_api_url,
        token=cluster.k8s_token,
        ca_cert=cluster.k8s_ca_cert,
        client_cert=cluster.k8s_client_cert,
        client_key=cluster.k8s_client_key,
        kubeconfig_path=cluster.kubeconfig_path,
        kubeconfig_context=cluster.kubeconfig_context,
    )
    try:
        scanner = K8sHardeningScanner(connector)
        result = scanner.run_all_checks(namespace=namespace)
        connector.close()
        return result
    except Exception as e:
        connector.close()
        logger.error("K8s hardening scan failed for cluster %s: %s", cluster.name, e)
        return {"success": False, "error": str(e)}


# ------------------------------------------------------------------
# Cluster hosts listing
# ------------------------------------------------------------------


@router.get("/{cluster_id}/hosts", response_model=list[dict])
async def list_cluster_hosts(
    cluster_id: int,
    session: DbSession,
    current_user: CurrentUser,
) -> list[dict]:
    """List all hosts belonging to a cluster."""
    from app.models import Host
    from sqlalchemy import select

    svc = DiscoveryService(session)
    cluster = await svc.get_cluster_by_id(cluster_id)
    if not cluster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")

    result = await session.execute(select(Host).where(Host.cluster_id == cluster_id).order_by(Host.name))
    hosts = result.scalars().all()
    return [
        {
            "id": h.id,
            "name": h.name,
            "display_name": h.display_name,
            "host_type": h.host_type,
            "status": h.status,
            "os_family": h.os_family,
            "k8s_namespace": h.k8s_namespace,
            "k8s_pod_name": h.k8s_pod_name,
            "k8s_node_name": h.k8s_node_name,
            "container_image": h.container_image,
            "container_runtime": h.container_runtime,
            "security_context": h.security_context,
            "last_scan_score": h.last_scan_score,
        }
        for h in hosts
    ]


# ------------------------------------------------------------------
# Drift detection
# ------------------------------------------------------------------


@router.post("/{cluster_id}/drift", response_model=dict)
async def detect_drift(
    cluster_id: int,
    session: DbSession,
    current_user: OperatorUser,
) -> dict:
    """Detect configuration drift for cluster hosts.

    For Docker clusters: compares stored security_context (from last discovery)
    against live Docker inspect.
    For K8s clusters: compares pod spec against container runtime state.
    """
    from app.models import Host
    from sqlalchemy import select

    svc = DiscoveryService(session)
    cluster = await svc.get_cluster_by_id(cluster_id)
    if not cluster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")

    result = await session.execute(select(Host).where(Host.cluster_id == cluster_id))
    hosts = result.scalars().all()

    if cluster.cluster_type == "docker":
        host_data = [
            {
                "name": h.name,
                "container_name": h.address or h.name.split("/")[-1],
                "security_context": h.security_context,
            }
            for h in hosts
        ]
        drift_result = await asyncio.to_thread(_run_docker_drift, cluster, host_data)
    elif cluster.cluster_type == "kubernetes":
        drift_result = await asyncio.to_thread(_run_k8s_drift, cluster, cluster.k8s_namespace)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported cluster type: {cluster.cluster_type}",
        )

    return drift_result


def _run_docker_drift(cluster: Cluster, host_data: list[dict]) -> dict:
    """Run Docker drift detection in thread."""
    from app.services.drift_detector import DriftDetector

    try:
        docker_client = DiscoveryService._get_docker_client(cluster)
        detector = DriftDetector(docker_client=docker_client)
        result = detector.detect_docker_drift(host_data)
        docker_client.close()
        return result
    except Exception as e:
        logger.error("Docker drift detection failed: %s", e)
        return {"success": False, "error": str(e)}


def _run_k8s_drift(cluster: Cluster, namespace: str | None) -> dict:
    """Run K8s drift detection in thread."""
    from app.services.drift_detector import DriftDetector

    connector = K8sConnector(
        api_url=cluster.k8s_api_url,
        token=cluster.k8s_token,
        ca_cert=cluster.k8s_ca_cert,
        client_cert=cluster.k8s_client_cert,
        client_key=cluster.k8s_client_key,
        kubeconfig_path=cluster.kubeconfig_path,
        kubeconfig_context=cluster.kubeconfig_context,
    )
    try:
        # Try to get docker client on same node for runtime inspect
        docker_client = None
        if cluster.docker_host:
            docker_client = DiscoveryService._get_docker_client(cluster)

        detector = DriftDetector(connector=connector, docker_client=docker_client)
        result = detector.detect_k8s_pod_drift(namespace=namespace)
        connector.close()
        if docker_client:
            docker_client.close()
        return result
    except Exception as e:
        connector.close()
        logger.error("K8s drift detection failed: %s", e)
        return {"success": False, "error": str(e)}


# ------------------------------------------------------------------
# Image security checks
# ------------------------------------------------------------------


@router.post("/{cluster_id}/image-check", response_model=dict)
async def check_images(
    cluster_id: int,
    session: DbSession,
    current_user: OperatorUser,
) -> dict:
    """Run image security checks on all hosts in a cluster."""
    from app.models import Host
    from app.services.image_checker import ImageChecker
    from sqlalchemy import select

    svc = DiscoveryService(session)
    cluster = await svc.get_cluster_by_id(cluster_id)
    if not cluster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")

    result = await session.execute(select(Host).where(Host.cluster_id == cluster_id))
    hosts = result.scalars().all()

    host_data = [
        {
            "name": h.name,
            "container_image": h.container_image,
            "security_context": h.security_context,
            "k8s_labels": h.k8s_labels,
        }
        for h in hosts
        if h.container_image
    ]

    checker = ImageChecker()
    return checker.check_from_hosts(host_data)


# ------------------------------------------------------------------
# Risk scoring
# ------------------------------------------------------------------


@router.post("/{cluster_id}/risk-score", response_model=dict)
async def calculate_risk_scores(
    cluster_id: int,
    session: DbSession,
    current_user: OperatorUser,
) -> dict:
    """Calculate risk scores for all hosts in a cluster."""
    from app.models import Host
    from app.services.risk_scorer import RiskScorer
    from sqlalchemy import select

    svc = DiscoveryService(session)
    cluster = await svc.get_cluster_by_id(cluster_id)
    if not cluster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")

    result = await session.execute(select(Host).where(Host.cluster_id == cluster_id))
    hosts = result.scalars().all()

    host_data = [
        {
            "name": h.name,
            "host_type": h.host_type,
            "container_image": h.container_image or "",
            "security_context": h.security_context,
            "k8s_namespace": h.k8s_namespace,
            "k8s_labels": h.k8s_labels,
        }
        for h in hosts
    ]

    scorer = RiskScorer()
    return scorer.score_hosts(host_data)
