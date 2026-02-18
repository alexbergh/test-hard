"""Kubernetes connector service -- connects to K8s API, discovers pods/nodes/containers."""

import logging
import tempfile
from pathlib import Path

from kubernetes import client as k8s_client
from kubernetes import config as k8s_config

logger = logging.getLogger(__name__)


class K8sConnector:
    """Connects to a Kubernetes cluster and provides discovery methods."""

    def __init__(
        self,
        api_url: str | None = None,
        token: str | None = None,
        ca_cert: str | None = None,
        client_cert: str | None = None,
        client_key: str | None = None,
        kubeconfig_path: str | None = None,
        kubeconfig_context: str | None = None,
    ):
        self._api_url = api_url
        self._token = token
        self._ca_cert = ca_cert
        self._client_cert = client_cert
        self._client_key = client_key
        self._kubeconfig_path = kubeconfig_path
        self._kubeconfig_context = kubeconfig_context
        self._api_client: k8s_client.ApiClient | None = None
        self._temp_files: list[Path] = []

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self) -> k8s_client.ApiClient:
        """Build and return an ApiClient for the configured cluster."""
        if self._api_client is not None:
            return self._api_client

        configuration = k8s_client.Configuration()

        if self._kubeconfig_path:
            k8s_config.load_kube_config(
                config_file=self._kubeconfig_path,
                context=self._kubeconfig_context,
                client_configuration=configuration,
            )
        elif self._api_url and self._token:
            configuration.host = self._api_url
            configuration.api_key = {"BearerToken": self._token}
            configuration.api_key_prefix = {"BearerToken": "Bearer"}
            if self._ca_cert:
                ca_path = self._write_temp("ca.crt", self._ca_cert)
                configuration.ssl_ca_cert = str(ca_path)
            else:
                configuration.verify_ssl = False
            if self._client_cert:
                cert_path = self._write_temp("client.crt", self._client_cert)
                configuration.cert_file = str(cert_path)
            if self._client_key:
                key_path = self._write_temp("client.key", self._client_key)
                configuration.key_file = str(key_path)
        else:
            # Try in-cluster config (ServiceAccount)
            try:
                k8s_config.load_incluster_config()
                self._api_client = k8s_client.ApiClient()
                return self._api_client
            except k8s_config.ConfigException:
                # Fallback to default kubeconfig
                k8s_config.load_kube_config(client_configuration=configuration)

        self._api_client = k8s_client.ApiClient(configuration)
        return self._api_client

    def close(self) -> None:
        """Close client and clean up temp files."""
        if self._api_client:
            self._api_client.close()
            self._api_client = None
        for tf in self._temp_files:
            try:
                tf.unlink(missing_ok=True)
            except Exception:
                pass
        self._temp_files.clear()

    def _write_temp(self, name: str, content: str) -> Path:
        """Write content to a temp file, return path."""
        tmp = Path(tempfile.mktemp(suffix=f"_{name}"))
        tmp.write_text(content)
        self._temp_files.append(tmp)
        return tmp

    # ------------------------------------------------------------------
    # Info
    # ------------------------------------------------------------------

    def get_version(self) -> dict:
        """Get cluster version info."""
        api = k8s_client.VersionApi(self.connect())
        info = api.get_code()
        return {
            "git_version": info.git_version,
            "platform": info.platform,
            "go_version": info.go_version,
            "major": info.major,
            "minor": info.minor,
        }

    # ------------------------------------------------------------------
    # Discovery: Nodes
    # ------------------------------------------------------------------

    def list_nodes(self) -> list[dict]:
        """List all cluster nodes with status and info."""
        v1 = k8s_client.CoreV1Api(self.connect())
        nodes = v1.list_node()
        result = []
        for node in nodes.items:
            addresses = {a.type: a.address for a in (node.status.addresses or [])}
            conditions = {c.type: c.status for c in (node.status.conditions or [])}
            info = node.status.node_info
            result.append(
                {
                    "name": node.metadata.name,
                    "labels": dict(node.metadata.labels or {}),
                    "annotations": dict(node.metadata.annotations or {}),
                    "addresses": addresses,
                    "conditions": conditions,
                    "os_image": info.os_image if info else None,
                    "kernel_version": info.kernel_version if info else None,
                    "container_runtime": info.container_runtime_version if info else None,
                    "architecture": info.architecture if info else None,
                    "kubelet_version": info.kubelet_version if info else None,
                    "allocatable_cpu": node.status.allocatable.get("cpu") if node.status.allocatable else None,
                    "allocatable_memory": node.status.allocatable.get("memory") if node.status.allocatable else None,
                    "is_ready": conditions.get("Ready") == "True",
                }
            )
        return result

    # ------------------------------------------------------------------
    # Discovery: Namespaces
    # ------------------------------------------------------------------

    def list_namespaces(self) -> list[str]:
        """List all namespaces."""
        v1 = k8s_client.CoreV1Api(self.connect())
        ns_list = v1.list_namespace()
        return [ns.metadata.name for ns in ns_list.items]

    # ------------------------------------------------------------------
    # Discovery: Pods
    # ------------------------------------------------------------------

    def list_pods(self, namespace: str | None = None) -> list[dict]:
        """List pods with security context extraction."""
        v1 = k8s_client.CoreV1Api(self.connect())
        if namespace:
            pods = v1.list_namespaced_pod(namespace)
        else:
            pods = v1.list_pod_for_all_namespaces()

        result = []
        for pod in pods.items:
            result.append(self._extract_pod_info(pod))
        return result

    def _extract_pod_info(self, pod) -> dict:
        """Extract pod info including security context."""
        spec = pod.spec
        metadata = pod.metadata
        status = pod.status

        # Pod-level security context
        pod_sc = self._extract_security_context(spec.security_context) if spec.security_context else {}

        # Container-level info
        containers = []
        for c in spec.containers or []:
            c_sc = self._extract_security_context(c.security_context) if c.security_context else {}
            containers.append(
                {
                    "name": c.name,
                    "image": c.image,
                    "ports": [{"container_port": p.container_port, "protocol": p.protocol} for p in (c.ports or [])],
                    "resources": self._extract_resources(c.resources),
                    "security_context": c_sc,
                    "volume_mounts": [
                        {"name": vm.name, "mount_path": vm.mount_path, "read_only": vm.read_only}
                        for vm in (c.volume_mounts or [])
                    ],
                    "command": c.command,
                    "args": c.args,
                }
            )

        # Container statuses (runtime info)
        container_statuses = []
        for cs in status.container_statuses or []:
            container_statuses.append(
                {
                    "name": cs.name,
                    "container_id": cs.container_id,
                    "image": cs.image,
                    "image_id": cs.image_id,
                    "ready": cs.ready,
                    "restart_count": cs.restart_count,
                    "started": cs.started,
                }
            )

        # Volumes -- check for sensitive mounts
        volumes = []
        for v in spec.volumes or []:
            vol_info = {"name": v.name}
            if v.host_path:
                vol_info["type"] = "hostPath"
                vol_info["path"] = v.host_path.path
            elif v.config_map:
                vol_info["type"] = "configMap"
                vol_info["config_map"] = v.config_map.name
            elif v.secret:
                vol_info["type"] = "secret"
                vol_info["secret"] = v.secret.secret_name
            elif v.persistent_volume_claim:
                vol_info["type"] = "pvc"
                vol_info["claim"] = v.persistent_volume_claim.claim_name
            elif v.empty_dir:
                vol_info["type"] = "emptyDir"
            else:
                vol_info["type"] = "other"
            volumes.append(vol_info)

        return {
            "name": metadata.name,
            "namespace": metadata.namespace,
            "labels": dict(metadata.labels or {}),
            "annotations": dict(metadata.annotations or {}),
            "node_name": spec.node_name,
            "service_account": spec.service_account_name,
            "host_network": spec.host_network or False,
            "host_pid": spec.host_pid or False,
            "host_ipc": spec.host_ipc or False,
            "phase": status.phase if status else None,
            "pod_ip": status.pod_ip if status else None,
            "security_context": pod_sc,
            "containers": containers,
            "container_statuses": container_statuses,
            "volumes": volumes,
            "created_at": metadata.creation_timestamp.isoformat() if metadata.creation_timestamp else None,
        }

    @staticmethod
    def _extract_security_context(sc) -> dict:
        """Extract security context fields from K8s SecurityContext object."""
        if sc is None:
            return {}
        result = {}
        if sc.run_as_user is not None:
            result["run_as_user"] = sc.run_as_user
        if sc.run_as_group is not None:
            result["run_as_group"] = sc.run_as_group
        if sc.run_as_non_root is not None:
            result["run_as_non_root"] = sc.run_as_non_root
        if hasattr(sc, "privileged") and sc.privileged is not None:
            result["privileged"] = sc.privileged
        if hasattr(sc, "read_only_root_filesystem") and sc.read_only_root_filesystem is not None:
            result["read_only_root_filesystem"] = sc.read_only_root_filesystem
        if hasattr(sc, "allow_privilege_escalation") and sc.allow_privilege_escalation is not None:
            result["allow_privilege_escalation"] = sc.allow_privilege_escalation
        if hasattr(sc, "capabilities") and sc.capabilities:
            caps = sc.capabilities
            if caps.add:
                result["capabilities_add"] = list(caps.add)
            if caps.drop:
                result["capabilities_drop"] = list(caps.drop)
        if sc.fs_group is not None:
            result["fs_group"] = sc.fs_group
        if hasattr(sc, "seccomp_profile") and sc.seccomp_profile:
            result["seccomp_profile"] = sc.seccomp_profile.type
        return result

    @staticmethod
    def _extract_resources(resources) -> dict:
        """Extract resource requests/limits."""
        if resources is None:
            return {}
        result = {}
        if resources.limits:
            result["limits"] = dict(resources.limits)
        if resources.requests:
            result["requests"] = dict(resources.requests)
        return result

    # ------------------------------------------------------------------
    # Discovery: Deployments
    # ------------------------------------------------------------------

    def list_deployments(self, namespace: str | None = None) -> list[dict]:
        """List deployments."""
        apps_v1 = k8s_client.AppsV1Api(self.connect())
        if namespace:
            deps = apps_v1.list_namespaced_deployment(namespace)
        else:
            deps = apps_v1.list_deployment_for_all_namespaces()

        result = []
        for d in deps.items:
            result.append(
                {
                    "name": d.metadata.name,
                    "namespace": d.metadata.namespace,
                    "replicas": d.spec.replicas,
                    "ready_replicas": d.status.ready_replicas or 0,
                    "labels": dict(d.metadata.labels or {}),
                }
            )
        return result

    # ------------------------------------------------------------------
    # Discovery: RBAC
    # ------------------------------------------------------------------

    def list_cluster_role_bindings(self) -> list[dict]:
        """List ClusterRoleBindings for RBAC analysis."""
        rbac_v1 = k8s_client.RbacAuthorizationV1Api(self.connect())
        bindings = rbac_v1.list_cluster_role_binding()
        result = []
        for b in bindings.items:
            subjects = []
            for s in b.subjects or []:
                subjects.append(
                    {
                        "kind": s.kind,
                        "name": s.name,
                        "namespace": s.namespace,
                    }
                )
            result.append(
                {
                    "name": b.metadata.name,
                    "role_ref": {
                        "kind": b.role_ref.kind,
                        "name": b.role_ref.name,
                    },
                    "subjects": subjects,
                }
            )
        return result

    # ------------------------------------------------------------------
    # Discovery: NetworkPolicies
    # ------------------------------------------------------------------

    def list_network_policies(self, namespace: str | None = None) -> list[dict]:
        """List NetworkPolicies."""
        net_v1 = k8s_client.NetworkingV1Api(self.connect())
        if namespace:
            policies = net_v1.list_namespaced_network_policy(namespace)
        else:
            policies = net_v1.list_network_policy_for_all_namespaces()

        result = []
        for p in policies.items:
            result.append(
                {
                    "name": p.metadata.name,
                    "namespace": p.metadata.namespace,
                    "pod_selector": dict(p.spec.pod_selector.match_labels or {}) if p.spec.pod_selector else {},
                    "policy_types": p.spec.policy_types or [],
                    "ingress_rules_count": len(p.spec.ingress or []),
                    "egress_rules_count": len(p.spec.egress or []),
                }
            )
        return result
