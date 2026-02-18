"""Host management service."""

import asyncio
import logging
from typing import Sequence

from app.config import get_settings
from app.models import Host
from app.schemas import HostCreate, HostUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import docker

settings = get_settings()
logger = logging.getLogger(__name__)


def _get_docker_client():
    """Get Docker client using configured DOCKER_HOST."""
    docker_host = settings.docker_host
    if docker_host.startswith("tcp://"):
        return docker.DockerClient(base_url=docker_host)
    return docker.from_env()


class HostService:
    """Service for host management operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_hosts(self, include_inactive: bool = False) -> Sequence[Host]:
        """Get all hosts."""
        query = select(Host)
        if not include_inactive:
            query = query.where(Host.is_active == True)  # noqa: E712
        query = query.order_by(Host.name)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_host_by_id(self, host_id: int) -> Host | None:
        """Get host by ID."""
        result = await self.session.execute(select(Host).where(Host.id == host_id))
        return result.scalar_one_or_none()

    async def get_host_by_name(self, name: str) -> Host | None:
        """Get host by name."""
        result = await self.session.execute(select(Host).where(Host.name == name))
        return result.scalar_one_or_none()

    async def create_host(self, host_data: HostCreate) -> Host:
        """Create a new host."""
        host = Host(
            name=host_data.name,
            display_name=host_data.display_name or host_data.name,
            description=host_data.description,
            host_type=host_data.host_type,
            address=host_data.address,
            port=host_data.port,
            ssh_user=host_data.ssh_user,
            ssh_key_path=host_data.ssh_key_path,
            os_family=host_data.os_family,
            os_version=host_data.os_version,
            enabled_scanners=host_data.enabled_scanners,
            scan_profile=host_data.scan_profile,
            tags=host_data.tags,
        )
        self.session.add(host)
        await self.session.flush()
        await self.session.refresh(host)
        return host

    async def update_host(self, host_id: int, host_data: HostUpdate) -> Host | None:
        """Update an existing host."""
        host = await self.get_host_by_id(host_id)
        if not host:
            return None

        update_data = host_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(host, field, value)

        await self.session.flush()
        await self.session.refresh(host)
        return host

    async def delete_host(self, host_id: int) -> bool:
        """Delete a host."""
        host = await self.get_host_by_id(host_id)
        if not host:
            return False
        await self.session.delete(host)
        return True

    async def check_host_status(self, host: Host) -> str:
        """Check if host is reachable and update status."""
        try:
            if host.host_type == "container":
                status = await self._check_container_status(host.name)
            elif host.host_type == "ssh":
                status = await self._check_ssh_status(host)
            elif host.host_type in ("k8s_node", "k8s_pod"):
                status = await self._check_k8s_status(host)
            else:
                status = "unknown"

            host.status = status
            await self.session.flush()
            return status
        except Exception:
            host.status = "offline"
            await self.session.flush()
            return "offline"

    async def _check_container_status(self, container_name: str) -> str:
        """Check Docker container status."""
        try:
            client = _get_docker_client()
            container = client.containers.get(container_name)
            if container.status == "running":
                return "online"
            return "offline"
        except docker.errors.NotFound:
            return "offline"
        except Exception:
            return "unknown"

    async def _check_ssh_status(self, host: Host) -> str:
        """Check SSH host status via ping."""
        if not host.address:
            return "unknown"

        try:
            # Simple TCP check on SSH port
            port = host.port or 22
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host.address, port),
                timeout=5.0,
            )
            writer.close()
            await writer.wait_closed()
            return "online"
        except (asyncio.TimeoutError, OSError):
            return "offline"

    async def _check_k8s_status(self, host: Host) -> str:
        """Check Kubernetes node/pod status via cluster connection."""
        if not host.cluster_id:
            return "unknown"
        try:
            from app.models import Cluster

            cluster = await self.session.get(Cluster, host.cluster_id)
            if not cluster:
                return "unknown"
            return await asyncio.to_thread(_check_k8s_status_sync, cluster, host)
        except Exception:
            return "unknown"

    async def sync_docker_containers(self) -> list[Host]:
        """Sync hosts from running Docker containers."""
        try:
            client = _get_docker_client()
            containers = client.containers.list()
            created_hosts = []
            logger.info("Found %d containers, syncing target-* hosts", len(containers))

            for container in containers:
                name = container.name
                if name.startswith("target-"):
                    existing = await self.get_host_by_name(name)
                    if not existing:
                        # Detect OS from image
                        image = container.image.tags[0] if container.image.tags else ""
                        os_family = self._detect_os_family(image)

                        host = Host(
                            name=name,
                            display_name=name.replace("target-", "").title(),
                            host_type="container",
                            address=name,
                            os_family=os_family,
                            status="online" if container.status == "running" else "offline",
                        )
                        self.session.add(host)
                        created_hosts.append(host)

            await self.session.flush()
            return created_hosts
        except Exception:
            return []

    @staticmethod
    def _detect_os_family(image: str) -> str:
        """Detect OS family from Docker image name."""
        image_lower = image.lower()
        if "debian" in image_lower:
            return "debian"
        if "ubuntu" in image_lower:
            return "ubuntu"
        if "fedora" in image_lower:
            return "fedora"
        if "centos" in image_lower:
            return "centos"
        if "alt" in image_lower:
            return "alt"
        return "unknown"


def _check_k8s_status_sync(cluster_obj, host_obj) -> str:
    """Synchronous K8s node/pod status check (runs in thread)."""
    from app.services.k8s_connector import K8sConnector
    from kubernetes import client as k8s_client

    connector = K8sConnector(
        api_url=cluster_obj.k8s_api_url,
        token=cluster_obj.k8s_token,
        ca_cert=cluster_obj.k8s_ca_cert,
        client_cert=cluster_obj.k8s_client_cert,
        client_key=cluster_obj.k8s_client_key,
        kubeconfig_path=cluster_obj.kubeconfig_path,
        kubeconfig_context=cluster_obj.kubeconfig_context,
    )
    try:
        v1 = k8s_client.CoreV1Api(connector.connect())
        if host_obj.host_type == "k8s_node":
            return _check_node_status(v1, host_obj.k8s_node_name)
        if host_obj.host_type == "k8s_pod":
            pod = v1.read_namespaced_pod(host_obj.k8s_pod_name, host_obj.k8s_namespace)
            return "online" if pod.status.phase == "Running" else "offline"
        return "unknown"
    except Exception:
        return "offline"
    finally:
        connector.close()


def _check_node_status(v1, node_name: str) -> str:
    """Check K8s node Ready condition."""
    node = v1.read_node(node_name)
    for condition in node.status.conditions or []:
        if condition.type == "Ready":
            return "online" if condition.status == "True" else "offline"
    return "unknown"
