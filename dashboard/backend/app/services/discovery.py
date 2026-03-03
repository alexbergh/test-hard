"""Discovery service -- discovers pods, nodes, and containers from clusters."""

import asyncio
import logging
from collections.abc import Sequence

# NOTE: 'docker' is the Python SDK package name (API-compatible with Podman)
import docker as podman
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Cluster, Host
from app.services.k8s_connector import K8sConnector

logger = logging.getLogger(__name__)


class DiscoveryService:
    """Discovers hosts from Kubernetes clusters and Podman endpoints."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ------------------------------------------------------------------
    # Cluster CRUD
    # ------------------------------------------------------------------

    async def get_all_clusters(self, include_inactive: bool = False) -> Sequence[Cluster]:
        """Get all clusters."""
        query = select(Cluster)
        if not include_inactive:
            query = query.where(Cluster.is_active == True)  # noqa: E712
        query = query.order_by(Cluster.name)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_cluster_by_id(self, cluster_id: int) -> Cluster | None:
        """Get cluster by ID."""
        result = await self.session.execute(select(Cluster).where(Cluster.id == cluster_id))
        return result.scalar_one_or_none()

    async def get_cluster_by_name(self, name: str) -> Cluster | None:
        """Get cluster by name."""
        result = await self.session.execute(select(Cluster).where(Cluster.name == name))
        return result.scalar_one_or_none()

    async def create_cluster(self, data) -> Cluster:
        """Create a new cluster entry."""
        cluster = Cluster(
            name=data.name,
            display_name=data.display_name or data.name,
            description=data.description,
            cluster_type=data.cluster_type,
            k8s_api_url=data.k8s_api_url,
            k8s_token=data.k8s_token,
            k8s_ca_cert=data.k8s_ca_cert,
            k8s_client_cert=data.k8s_client_cert,
            k8s_client_key=data.k8s_client_key,
            kubeconfig_path=data.kubeconfig_path,
            kubeconfig_context=data.kubeconfig_context,
            k8s_namespace=data.k8s_namespace,
            podman_host=data.podman_host,
            podman_tls_verify=data.podman_tls_verify,
            podman_cert_path=data.podman_cert_path,
            containerd_socket=getattr(data, "containerd_socket", None),
            auto_discover=data.auto_discover,
            discover_filter=data.discover_filter,
            tags=data.tags,
        )
        self.session.add(cluster)
        await self.session.flush()
        await self.session.refresh(cluster)
        return cluster

    async def update_cluster(self, cluster_id: int, data) -> Cluster | None:
        """Update a cluster entry."""
        cluster = await self.get_cluster_by_id(cluster_id)
        if not cluster:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(cluster, field, value)
        await self.session.flush()
        await self.session.refresh(cluster)
        return cluster

    async def delete_cluster(self, cluster_id: int) -> bool:
        """Delete a cluster and disassociate its hosts."""
        cluster = await self.get_cluster_by_id(cluster_id)
        if not cluster:
            return False
        # Disassociate hosts
        hosts = await self.session.execute(select(Host).where(Host.cluster_id == cluster_id))
        for host in hosts.scalars().all():
            host.cluster_id = None
        await self.session.delete(cluster)
        return True

    # ------------------------------------------------------------------
    # Connection test
    # ------------------------------------------------------------------

    async def test_connection(self, cluster: Cluster) -> dict:
        """Test cluster connection and return info."""
        if cluster.cluster_type == "kubernetes":
            return await asyncio.to_thread(self._test_k8s_connection, cluster)
        elif cluster.cluster_type == "podman":
            return await asyncio.to_thread(self._test_podman_connection, cluster)
        else:
            return {"success": False, "message": f"Unsupported cluster type: {cluster.cluster_type}"}

    @staticmethod
    def _test_k8s_connection(cluster: Cluster) -> dict:
        """Test Kubernetes connection (runs in thread)."""
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
            version_info = connector.get_version()
            nodes = connector.list_nodes()
            namespaces = connector.list_namespaces()
            pods = connector.list_pods(namespace=cluster.k8s_namespace)
            connector.close()
            return {
                "success": True,
                "cluster_type": "kubernetes",
                "message": f"Connected to K8s {version_info.get('git_version', '?')}",
                "version": version_info.get("git_version"),
                "node_count": len(nodes),
                "pod_count": len(pods),
                "namespace_count": len(namespaces),
            }
        except Exception as e:
            connector.close()
            logger.error("K8s connection test failed: %s", e)
            return {
                "success": False,
                "cluster_type": "kubernetes",
                "message": f"Connection failed: {e}",
            }

    @staticmethod
    def _get_podman_client(cluster: Cluster):
        """Build a Podman client from cluster settings."""
        if cluster.podman_host:
            if cluster.podman_tls_verify and cluster.podman_cert_path:
                tls_config = podman.tls.TLSConfig(
                    client_cert=(
                        f"{cluster.podman_cert_path}/cert.pem",
                        f"{cluster.podman_cert_path}/key.pem",
                    ),
                    ca_cert=f"{cluster.podman_cert_path}/ca.pem",
                    verify=True,
                )
                return podman.DockerClient(base_url=cluster.podman_host, tls=tls_config)
            return podman.DockerClient(base_url=cluster.podman_host)
        # No explicit host -- auto-detect (unix socket on Linux)
        return podman.from_env()

    @staticmethod
    def _test_podman_connection(cluster: Cluster) -> dict:
        """Test Podman connection (runs in thread)."""
        try:
            client = DiscoveryService._get_podman_client(cluster)

            client.info()  # verify connection is alive
            containers = client.containers.list()
            version = client.version()
            client.close()

            return {
                "success": True,
                "cluster_type": "podman",
                "message": f"Connected to Podman {version.get('Version', '?')}",
                "version": version.get("Version"),
                "container_count": len(containers),
                "node_count": 1,
            }
        except Exception as e:
            logger.error("Podman connection test failed: %s", e)
            return {
                "success": False,
                "cluster_type": "podman",
                "message": f"Connection failed: {e}",
            }

    # ------------------------------------------------------------------
    # Discovery: Kubernetes
    # ------------------------------------------------------------------

    async def discover_k8s(self, cluster: Cluster) -> dict:
        """Discover nodes and pods from a Kubernetes cluster, sync to hosts table."""
        return await asyncio.to_thread(self._discover_k8s_sync, cluster)

    def _discover_k8s_sync(self, cluster: Cluster) -> dict:
        """Synchronous K8s discovery (runs in thread). Returns result dict for async caller."""
        # This returns raw data; the async wrapper will persist it
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
            nodes = connector.list_nodes()
            pods = connector.list_pods(namespace=cluster.k8s_namespace)
            namespaces = connector.list_namespaces()
            version_info = connector.get_version()
            connector.close()
            return {
                "success": True,
                "nodes": nodes,
                "pods": pods,
                "namespaces": namespaces,
                "version": version_info.get("git_version"),
                "namespace_count": len(namespaces),
            }
        except Exception as e:
            connector.close()
            logger.error("K8s discovery failed for cluster %s: %s", cluster.name, e)
            return {"success": False, "error": str(e)}

    async def sync_k8s_hosts(self, cluster: Cluster) -> dict:
        """Discover K8s resources and sync hosts to DB."""
        raw = await self.discover_k8s(cluster)
        if not raw.get("success"):
            cluster.status = "error"
            cluster.last_error = raw.get("error", "Discovery failed")
            await self.session.flush()
            return {
                "cluster_id": cluster.id,
                "cluster_name": cluster.name,
                "hosts_created": 0,
                "hosts_updated": 0,
                "hosts_total": 0,
                "details": [{"error": raw.get("error")}],
            }

        # Update cluster info
        cluster.status = "connected"
        cluster.last_error = None
        cluster.cluster_version = raw.get("version")
        cluster.node_count = len(raw["nodes"])
        cluster.pod_count = len(raw["pods"])
        cluster.namespace_count = raw.get("namespace_count")

        created = 0
        updated = 0
        details = []

        # Sync nodes as hosts
        for node_data in raw["nodes"]:
            host_name = f"{cluster.name}/node/{node_data['name']}"
            existing = await self._get_host_by_name(host_name)
            if existing:
                self._update_node_host(existing, cluster, node_data)
                updated += 1
                details.append({"action": "updated", "type": "node", "name": host_name})
            else:
                host = self._create_node_host(cluster, node_data, host_name)
                self.session.add(host)
                created += 1
                details.append({"action": "created", "type": "node", "name": host_name})

        # Sync pods as hosts
        for pod_data in raw["pods"]:
            host_name = f"{cluster.name}/pod/{pod_data['namespace']}/{pod_data['name']}"
            existing = await self._get_host_by_name(host_name)
            if existing:
                self._update_pod_host(existing, cluster, pod_data)
                updated += 1
                details.append({"action": "updated", "type": "pod", "name": host_name})
            else:
                host = self._create_pod_host(cluster, pod_data, host_name)
                self.session.add(host)
                created += 1
                details.append({"action": "created", "type": "pod", "name": host_name})

        await self.session.flush()

        total = created + updated
        logger.info(
            "K8s discovery for %s: created=%d updated=%d total=%d",
            cluster.name,
            created,
            updated,
            total,
        )

        return {
            "cluster_id": cluster.id,
            "cluster_name": cluster.name,
            "hosts_created": created,
            "hosts_updated": updated,
            "hosts_total": total,
            "details": details,
        }

    # ------------------------------------------------------------------
    # Discovery: Podman
    # ------------------------------------------------------------------

    async def sync_podman_hosts(self, cluster: Cluster) -> dict:
        """Discover Podman containers and sync hosts to DB."""
        raw = await asyncio.to_thread(self._discover_podman_sync, cluster)
        if not raw.get("success"):
            cluster.status = "error"
            cluster.last_error = raw.get("error", "Discovery failed")
            await self.session.flush()
            return {
                "cluster_id": cluster.id,
                "cluster_name": cluster.name,
                "hosts_created": 0,
                "hosts_updated": 0,
                "hosts_total": 0,
                "details": [{"error": raw.get("error")}],
            }

        cluster.status = "connected"
        cluster.last_error = None
        cluster.cluster_version = raw.get("version")
        cluster.pod_count = len(raw["containers"])

        created = 0
        updated = 0
        details = []

        for cdata in raw["containers"]:
            host_name = f"{cluster.name}/container/{cdata['name']}"
            existing = await self._get_host_by_name(host_name)
            if existing:
                self._update_container_host(existing, cluster, cdata)
                updated += 1
                details.append({"action": "updated", "type": "container", "name": host_name})
            else:
                host = self._create_container_host(cluster, cdata, host_name)
                self.session.add(host)
                created += 1
                details.append({"action": "created", "type": "container", "name": host_name})

        await self.session.flush()
        total = created + updated
        logger.info(
            "Podman discovery for %s: created=%d updated=%d total=%d",
            cluster.name,
            created,
            updated,
            total,
        )
        return {
            "cluster_id": cluster.id,
            "cluster_name": cluster.name,
            "hosts_created": created,
            "hosts_updated": updated,
            "hosts_total": total,
            "details": details,
        }

    @staticmethod
    def _discover_podman_sync(cluster: Cluster) -> dict:
        """Synchronous Podman discovery."""
        try:
            client = DiscoveryService._get_podman_client(cluster)

            containers_list = client.containers.list(all=True)
            version = client.version()
            containers = []

            for c in containers_list:
                inspect = c.attrs
                config = inspect.get("Config", {})
                host_config = inspect.get("HostConfig", {})
                network_settings = inspect.get("NetworkSettings", {})

                # Extract security-relevant Podman inspect fields
                security_context = {
                    "privileged": host_config.get("Privileged", False),
                    "pid_mode": host_config.get("PidMode", ""),
                    "ipc_mode": host_config.get("IpcMode", ""),
                    "network_mode": host_config.get("NetworkMode", ""),
                    "cap_add": host_config.get("CapAdd") or [],
                    "cap_drop": host_config.get("CapDrop") or [],
                    "security_opt": host_config.get("SecurityOpt") or [],
                    "read_only_rootfs": host_config.get("ReadonlyRootfs", False),
                    "user": config.get("User", ""),
                }

                # Resources
                resources = {}
                if host_config.get("NanoCpus"):
                    resources["cpu_limit"] = host_config["NanoCpus"] / 1e9
                if host_config.get("Memory"):
                    resources["memory_limit"] = host_config["Memory"]

                containers.append(
                    {
                        "name": c.name,
                        "id": c.short_id,
                        "image": config.get("Image", ""),
                        "status": c.status,
                        "labels": config.get("Labels", {}),
                        "security_context": security_context,
                        "resources": resources,
                        "networks": list(network_settings.get("Networks", {}).keys()),
                        "ports": network_settings.get("Ports", {}),
                        "mounts": [
                            {
                                "source": m.get("Source", ""),
                                "destination": m.get("Destination", ""),
                                "mode": m.get("Mode", ""),
                                "rw": m.get("RW", True),
                            }
                            for m in inspect.get("Mounts", [])
                        ],
                    }
                )

            client.close()
            return {
                "success": True,
                "containers": containers,
                "version": version.get("Version"),
            }
        except Exception as e:
            logger.error("Podman discovery failed: %s", e)
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Host helper methods
    # ------------------------------------------------------------------

    async def _get_host_by_name(self, name: str) -> Host | None:
        """Get host by name."""
        result = await self.session.execute(select(Host).where(Host.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    def _create_node_host(cluster: Cluster, node_data: dict, host_name: str) -> Host:
        """Create a Host record for a K8s node."""
        os_image = node_data.get("os_image", "")
        os_family = _detect_os_from_image(os_image)
        return Host(
            name=host_name,
            display_name=f"Node: {node_data['name']}",
            host_type="k8s_node",
            address=node_data.get("addresses", {}).get("InternalIP"),
            os_family=os_family,
            architecture=node_data.get("architecture"),
            status="online" if node_data.get("is_ready") else "offline",
            cluster_id=cluster.id,
            k8s_node_name=node_data["name"],
            k8s_labels=node_data.get("labels", {}),
            k8s_annotations=node_data.get("annotations", {}),
            container_runtime=node_data.get("container_runtime"),
            security_context={},
            enabled_scanners={"openscap": True, "lynis": True},
        )

    @staticmethod
    def _update_node_host(host: Host, cluster: Cluster, node_data: dict) -> None:
        """Update existing node host."""
        host.status = "online" if node_data.get("is_ready") else "offline"
        host.cluster_id = cluster.id
        host.k8s_node_name = node_data["name"]
        host.k8s_labels = node_data.get("labels", {})
        host.address = node_data.get("addresses", {}).get("InternalIP") or host.address
        host.container_runtime = node_data.get("container_runtime")

    @staticmethod
    def _create_pod_host(cluster: Cluster, pod_data: dict, host_name: str) -> Host:
        """Create a Host record for a K8s pod."""
        # Use first container image for OS detection
        first_image = ""
        if pod_data.get("containers"):
            first_image = pod_data["containers"][0].get("image", "")
        os_family = _detect_os_from_image(first_image)

        # Merge pod-level + container-level security contexts
        merged_sc = dict(pod_data.get("security_context", {}))
        for c in pod_data.get("containers", []):
            csc = c.get("security_context", {})
            for k, v in csc.items():
                merged_sc[f"container.{c['name']}.{k}"] = v

        # Add host-level flags
        if pod_data.get("host_network"):
            merged_sc["host_network"] = True
        if pod_data.get("host_pid"):
            merged_sc["host_pid"] = True
        if pod_data.get("host_ipc"):
            merged_sc["host_ipc"] = True

        # Container ID from statuses
        container_id = None
        if pod_data.get("container_statuses"):
            cid = pod_data["container_statuses"][0].get("container_id", "")
            if cid:
                container_id = cid.split("//")[-1][:12] if "//" in cid else cid[:12]

        return Host(
            name=host_name,
            display_name=f"Pod: {pod_data['namespace']}/{pod_data['name']}",
            host_type="k8s_pod",
            address=pod_data.get("pod_ip"),
            os_family=os_family,
            status="online" if pod_data.get("phase") == "Running" else "offline",
            cluster_id=cluster.id,
            k8s_namespace=pod_data["namespace"],
            k8s_pod_name=pod_data["name"],
            k8s_node_name=pod_data.get("node_name"),
            k8s_labels=pod_data.get("labels", {}),
            k8s_annotations=pod_data.get("annotations", {}),
            container_id=container_id,
            container_image=first_image,
            security_context=merged_sc,
            enabled_scanners={"openscap": False, "lynis": False, "k8s_hardening": True},
        )

    @staticmethod
    def _update_pod_host(host: Host, cluster: Cluster, pod_data: dict) -> None:
        """Update existing pod host."""
        host.status = "online" if pod_data.get("phase") == "Running" else "offline"
        host.cluster_id = cluster.id
        host.k8s_namespace = pod_data["namespace"]
        host.k8s_pod_name = pod_data["name"]
        host.k8s_node_name = pod_data.get("node_name")
        host.k8s_labels = pod_data.get("labels", {})
        host.address = pod_data.get("pod_ip") or host.address
        if pod_data.get("containers"):
            host.container_image = pod_data["containers"][0].get("image", "")

    @staticmethod
    def _create_container_host(cluster: Cluster, cdata: dict, host_name: str) -> Host:
        """Create a Host record for a Podman container."""
        os_family = _detect_os_from_image(cdata.get("image", ""))
        return Host(
            name=host_name,
            display_name=f"Container: {cdata['name']}",
            host_type="container",
            address=cdata["name"],
            os_family=os_family,
            status="online" if cdata.get("status") == "running" else "offline",
            cluster_id=cluster.id,
            container_id=cdata.get("id"),
            container_image=cdata.get("image"),
            container_runtime="podman",
            security_context=cdata.get("security_context", {}),
            k8s_labels=cdata.get("labels", {}),
            enabled_scanners={"openscap": True, "lynis": True, "trivy": True},
        )

    @staticmethod
    def _update_container_host(host: Host, cluster: Cluster, cdata: dict) -> None:
        """Update existing Podman container host."""
        host.status = "online" if cdata.get("status") == "running" else "offline"
        host.cluster_id = cluster.id
        host.container_id = cdata.get("id")
        host.container_image = cdata.get("image")
        host.security_context = cdata.get("security_context", {})


def _detect_os_from_image(image: str) -> str:
    """Detect OS family from image name."""
    img = image.lower()
    if "debian" in img:
        return "debian"
    if "ubuntu" in img:
        return "ubuntu"
    if "fedora" in img:
        return "fedora"
    if "centos" in img or "cs9" in img:
        return "centos"
    if "alt" in img:
        return "alt"
    if "alpine" in img:
        return "alpine"
    if "rhel" in img or "redhat" in img:
        return "rhel"
    return "unknown"
