"""Kubernetes hardening scanner -- checks pod security, RBAC, NetworkPolicies."""

import logging
from typing import Any

from app.services.k8s_connector import K8sConnector

logger = logging.getLogger(__name__)

# Severity levels
CRITICAL = "critical"
HIGH = "high"
MEDIUM = "medium"
LOW = "low"
INFO = "info"


class K8sHardeningScanner:
    """Runs hardening checks against a Kubernetes cluster."""

    def __init__(self, connector: K8sConnector):
        self.connector = connector
        self.findings: list[dict] = []

    def run_all_checks(self, namespace: str | None = None) -> dict:
        """Run all hardening checks and return results."""
        self.findings = []

        pods = self.connector.list_pods(namespace=namespace)
        nodes = self.connector.list_nodes()
        network_policies = self.connector.list_network_policies(namespace=namespace)
        namespaces = self.connector.list_namespaces()
        rbac_bindings = self.connector.list_cluster_role_bindings()

        # Pod security checks
        for pod in pods:
            self._check_pod_security(pod)

        # Node checks
        for node in nodes:
            self._check_node_security(node)

        # Namespace-level checks
        self._check_network_policies(network_policies, namespaces, pods)

        # RBAC checks
        self._check_rbac(rbac_bindings)

        # Calculate score
        total = len(self.findings)
        passed = sum(1 for f in self.findings if f["status"] == "pass")
        failed = sum(1 for f in self.findings if f["status"] == "fail")
        warnings = sum(1 for f in self.findings if f["status"] == "warning")
        score = int((passed / total) * 100) if total > 0 else 100

        return {
            "success": True,
            "score": score,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "total_checks": total,
            "findings": self.findings,
            "summary": {
                "pods_checked": len(pods),
                "nodes_checked": len(nodes),
                "namespaces": len(namespaces),
                "network_policies": len(network_policies),
                "rbac_bindings": len(rbac_bindings),
            },
        }

    # ------------------------------------------------------------------
    # Pod Security Checks
    # ------------------------------------------------------------------

    def _check_pod_security(self, pod: dict) -> None:
        """Run all pod-level hardening checks."""
        pod_ref = f"{pod['namespace']}/{pod['name']}"
        pod_sc = pod.get("security_context", {})

        # Host namespace checks
        self._check_host_namespaces(pod, pod_ref)

        # Pod-level security context
        self._check_pod_security_context(pod_sc, pod_ref)

        # Container-level checks
        for container in pod.get("containers", []):
            c_ref = f"{pod_ref}/{container['name']}"
            self._check_container_security(container, c_ref, pod_ref)

        # Volume checks
        self._check_volumes(pod, pod_ref)

        # Service account checks
        self._check_service_account(pod, pod_ref)

    def _check_host_namespaces(self, pod: dict, pod_ref: str) -> None:
        """CIS 5.2.2-5.2.4: Check hostNetwork, hostPID, hostIPC."""
        # hostNetwork
        if pod.get("host_network"):
            self._add_finding(
                rule_id="K8S-POD-001",
                title="Pod uses host network namespace",
                severity=HIGH,
                status="fail",
                category="pod-security",
                target=pod_ref,
                detail="hostNetwork=true allows the pod to access the host network stack. "
                "This bypasses network policies and can expose host services.",
                remediation="Set spec.hostNetwork to false unless absolutely required.",
            )
        else:
            self._add_finding(
                rule_id="K8S-POD-001",
                title="Pod does not use host network namespace",
                severity=HIGH,
                status="pass",
                category="pod-security",
                target=pod_ref,
            )

        # hostPID
        if pod.get("host_pid"):
            self._add_finding(
                rule_id="K8S-POD-002",
                title="Pod uses host PID namespace",
                severity=HIGH,
                status="fail",
                category="pod-security",
                target=pod_ref,
                detail="hostPID=true allows the pod to see all processes on the host.",
                remediation="Set spec.hostPID to false.",
            )
        else:
            self._add_finding(
                rule_id="K8S-POD-002",
                title="Pod does not use host PID namespace",
                severity=HIGH,
                status="pass",
                category="pod-security",
                target=pod_ref,
            )

        # hostIPC
        if pod.get("host_ipc"):
            self._add_finding(
                rule_id="K8S-POD-003",
                title="Pod uses host IPC namespace",
                severity=MEDIUM,
                status="fail",
                category="pod-security",
                target=pod_ref,
                detail="hostIPC=true allows the pod to access host IPC resources.",
                remediation="Set spec.hostIPC to false.",
            )
        else:
            self._add_finding(
                rule_id="K8S-POD-003",
                title="Pod does not use host IPC namespace",
                severity=MEDIUM,
                status="pass",
                category="pod-security",
                target=pod_ref,
            )

    def _check_pod_security_context(self, pod_sc: dict, pod_ref: str) -> None:
        """Check pod-level securityContext fields."""
        # runAsNonRoot
        if not pod_sc.get("run_as_non_root"):
            self._add_finding(
                rule_id="K8S-POD-004",
                title="Pod does not enforce runAsNonRoot",
                severity=MEDIUM,
                status="fail",
                category="pod-security",
                target=pod_ref,
                detail="Pod-level securityContext.runAsNonRoot is not set to true.",
                remediation="Set spec.securityContext.runAsNonRoot to true.",
            )
        else:
            self._add_finding(
                rule_id="K8S-POD-004",
                title="Pod enforces runAsNonRoot",
                severity=MEDIUM,
                status="pass",
                category="pod-security",
                target=pod_ref,
            )

    def _check_container_security(self, container: dict, c_ref: str, pod_ref: str) -> None:
        """Run container-level hardening checks."""
        sc = container.get("security_context", {})
        resources = container.get("resources", {})

        # CIS 5.2.1: Privileged containers
        if sc.get("privileged"):
            self._add_finding(
                rule_id="K8S-CTR-001",
                title="Container runs in privileged mode",
                severity=CRITICAL,
                status="fail",
                category="container-security",
                target=c_ref,
                detail="Privileged containers have full access to the host.",
                remediation="Set securityContext.privileged to false.",
            )
        else:
            self._add_finding(
                rule_id="K8S-CTR-001",
                title="Container is not privileged",
                severity=CRITICAL,
                status="pass",
                category="container-security",
                target=c_ref,
            )

        # CIS 5.2.5: allowPrivilegeEscalation
        if sc.get("allow_privilege_escalation") is not False:
            self._add_finding(
                rule_id="K8S-CTR-002",
                title="Container allows privilege escalation",
                severity=HIGH,
                status="fail",
                category="container-security",
                target=c_ref,
                detail="allowPrivilegeEscalation is not explicitly set to false.",
                remediation="Set securityContext.allowPrivilegeEscalation to false.",
            )
        else:
            self._add_finding(
                rule_id="K8S-CTR-002",
                title="Container disallows privilege escalation",
                severity=HIGH,
                status="pass",
                category="container-security",
                target=c_ref,
            )

        # readOnlyRootFilesystem
        if not sc.get("read_only_root_filesystem"):
            self._add_finding(
                rule_id="K8S-CTR-003",
                title="Container root filesystem is writable",
                severity=MEDIUM,
                status="fail",
                category="container-security",
                target=c_ref,
                detail="readOnlyRootFilesystem is not set to true.",
                remediation="Set securityContext.readOnlyRootFilesystem to true.",
            )
        else:
            self._add_finding(
                rule_id="K8S-CTR-003",
                title="Container root filesystem is read-only",
                severity=MEDIUM,
                status="pass",
                category="container-security",
                target=c_ref,
            )

        # Capabilities: should drop ALL
        caps_drop = sc.get("capabilities_drop", [])
        if "ALL" not in caps_drop:
            self._add_finding(
                rule_id="K8S-CTR-004",
                title="Container does not drop ALL capabilities",
                severity=HIGH,
                status="fail",
                category="container-security",
                target=c_ref,
                detail=f"capabilities.drop={caps_drop}. Should include 'ALL'.",
                remediation="Set securityContext.capabilities.drop to ['ALL'].",
            )
        else:
            self._add_finding(
                rule_id="K8S-CTR-004",
                title="Container drops ALL capabilities",
                severity=HIGH,
                status="pass",
                category="container-security",
                target=c_ref,
            )

        # Dangerous capabilities added
        caps_add = sc.get("capabilities_add", [])
        dangerous_caps = {"SYS_ADMIN", "NET_ADMIN", "SYS_PTRACE", "NET_RAW", "SYS_MODULE"}
        added_dangerous = set(caps_add) & dangerous_caps
        if added_dangerous:
            self._add_finding(
                rule_id="K8S-CTR-005",
                title="Container adds dangerous capabilities",
                severity=HIGH,
                status="fail",
                category="container-security",
                target=c_ref,
                detail=f"Dangerous capabilities added: {sorted(added_dangerous)}",
                remediation="Remove dangerous capabilities unless absolutely required.",
            )
        else:
            self._add_finding(
                rule_id="K8S-CTR-005",
                title="No dangerous capabilities added",
                severity=HIGH,
                status="pass",
                category="container-security",
                target=c_ref,
            )

        # Resource limits
        if not resources.get("limits"):
            self._add_finding(
                rule_id="K8S-CTR-006",
                title="Container has no resource limits",
                severity=MEDIUM,
                status="fail",
                category="resource-management",
                target=c_ref,
                detail="No CPU/memory limits set. Container can consume unlimited resources.",
                remediation="Set resources.limits for CPU and memory.",
            )
        else:
            self._add_finding(
                rule_id="K8S-CTR-006",
                title="Container has resource limits",
                severity=MEDIUM,
                status="pass",
                category="resource-management",
                target=c_ref,
            )

        # Resource requests
        if not resources.get("requests"):
            self._add_finding(
                rule_id="K8S-CTR-007",
                title="Container has no resource requests",
                severity=LOW,
                status="fail",
                category="resource-management",
                target=c_ref,
                detail="No CPU/memory requests set.",
                remediation="Set resources.requests for CPU and memory.",
            )
        else:
            self._add_finding(
                rule_id="K8S-CTR-007",
                title="Container has resource requests",
                severity=LOW,
                status="pass",
                category="resource-management",
                target=c_ref,
            )

        # Image tag: should not use :latest
        image = container.get("image", "")
        if image and (":latest" in image or ":" not in image.split("/")[-1]):
            self._add_finding(
                rule_id="K8S-CTR-008",
                title="Container uses latest or untagged image",
                severity=MEDIUM,
                status="fail",
                category="image-security",
                target=c_ref,
                detail=f"Image '{image}' uses :latest or has no explicit tag.",
                remediation="Use a specific image tag (e.g., image:v1.2.3).",
            )
        else:
            self._add_finding(
                rule_id="K8S-CTR-008",
                title="Container uses explicit image tag",
                severity=MEDIUM,
                status="pass",
                category="image-security",
                target=c_ref,
            )

        # runAsUser: should not be 0 (root)
        run_as_user = sc.get("run_as_user")
        if run_as_user == 0:
            self._add_finding(
                rule_id="K8S-CTR-009",
                title="Container runs as root (UID 0)",
                severity=HIGH,
                status="fail",
                category="container-security",
                target=c_ref,
                detail="Container securityContext.runAsUser is set to 0.",
                remediation="Set runAsUser to a non-root UID (>= 1000).",
            )
        elif run_as_user is not None and run_as_user > 0:
            self._add_finding(
                rule_id="K8S-CTR-009",
                title="Container runs as non-root user",
                severity=HIGH,
                status="pass",
                category="container-security",
                target=c_ref,
            )

    def _check_volumes(self, pod: dict, pod_ref: str) -> None:
        """Check for sensitive volume mounts."""
        for vol in pod.get("volumes", []):
            if vol.get("type") == "hostPath":
                path = vol.get("path", "")
                sensitive_paths = [
                    "/",
                    "/etc",
                    "/var/run/docker.sock",
                    "/proc",
                    "/sys",
                    "/var/lib/kubelet",
                    "/etc/kubernetes",
                ]
                severity = CRITICAL if path in sensitive_paths else MEDIUM
                self._add_finding(
                    rule_id="K8S-VOL-001",
                    title=f"Pod mounts hostPath: {path}",
                    severity=severity,
                    status="fail",
                    category="volume-security",
                    target=pod_ref,
                    detail=f"Volume '{vol['name']}' mounts hostPath '{path}'.",
                    remediation="Avoid hostPath mounts. Use PVC or emptyDir instead.",
                )

        # Check for docker.sock mount specifically
        for container in pod.get("containers", []):
            for vm in container.get("volume_mounts", []):
                if "docker.sock" in vm.get("mount_path", ""):
                    self._add_finding(
                        rule_id="K8S-VOL-002",
                        title="Container mounts Docker socket",
                        severity=CRITICAL,
                        status="fail",
                        category="volume-security",
                        target=f"{pod_ref}/{container['name']}",
                        detail="Docker socket mount allows container escape.",
                        remediation="Remove docker.sock mount. Use Docker Socket Proxy.",
                    )

    def _check_service_account(self, pod: dict, pod_ref: str) -> None:
        """Check service account usage."""
        sa = pod.get("service_account")
        if sa == "default":
            self._add_finding(
                rule_id="K8S-SA-001",
                title="Pod uses default service account",
                severity=MEDIUM,
                status="fail",
                category="rbac",
                target=pod_ref,
                detail="Using the 'default' service account may grant unnecessary permissions.",
                remediation="Create a dedicated service account with minimal permissions.",
            )
        elif sa:
            self._add_finding(
                rule_id="K8S-SA-001",
                title="Pod uses dedicated service account",
                severity=MEDIUM,
                status="pass",
                category="rbac",
                target=pod_ref,
            )

    # ------------------------------------------------------------------
    # Node Security Checks
    # ------------------------------------------------------------------

    def _check_node_security(self, node: dict) -> None:
        """Run node-level hardening checks."""
        node_ref = f"node/{node['name']}"

        # Node readiness
        if not node.get("is_ready"):
            self._add_finding(
                rule_id="K8S-NODE-001",
                title="Node is not ready",
                severity=HIGH,
                status="warning",
                category="node-health",
                target=node_ref,
                detail=f"Node {node['name']} conditions: {node.get('conditions', {})}",
            )

        # Container runtime version check
        runtime = node.get("container_runtime", "")
        if runtime:
            # Check for very old versions
            if "docker://" in runtime:
                version_str = runtime.replace("docker://", "")
                try:
                    major = int(version_str.split(".")[0])
                    if major < 20:
                        self._add_finding(
                            rule_id="K8S-NODE-002",
                            title="Node uses outdated Docker version",
                            severity=MEDIUM,
                            status="fail",
                            category="node-security",
                            target=node_ref,
                            detail=f"Docker version {version_str} is outdated.",
                            remediation="Upgrade to Docker 24.0+ or migrate to containerd.",
                        )
                except (ValueError, IndexError):
                    pass

    # ------------------------------------------------------------------
    # NetworkPolicy Checks
    # ------------------------------------------------------------------

    def _check_network_policies(self, policies: list[dict], namespaces: list[str], pods: list[dict]) -> None:
        """Check NetworkPolicy coverage."""
        # Namespaces with pods but no NetworkPolicy
        ns_with_pods = {p["namespace"] for p in pods}
        ns_with_policies = {p["namespace"] for p in policies}
        system_namespaces = {"kube-system", "kube-public", "kube-node-lease"}

        for ns in ns_with_pods - ns_with_policies - system_namespaces:
            self._add_finding(
                rule_id="K8S-NET-001",
                title=f"Namespace '{ns}' has no NetworkPolicy",
                severity=HIGH,
                status="fail",
                category="network-security",
                target=f"namespace/{ns}",
                detail="Pods in this namespace have unrestricted network access.",
                remediation="Create a default-deny NetworkPolicy for this namespace.",
            )

        for ns in ns_with_pods & ns_with_policies - system_namespaces:
            self._add_finding(
                rule_id="K8S-NET-001",
                title=f"Namespace '{ns}' has NetworkPolicy",
                severity=HIGH,
                status="pass",
                category="network-security",
                target=f"namespace/{ns}",
            )

        # Check for default-deny policies
        for policy in policies:
            if policy.get("pod_selector") == {} and "Ingress" in policy.get("policy_types", []):
                # This is a default-deny ingress policy
                self._add_finding(
                    rule_id="K8S-NET-002",
                    title=f"Default-deny ingress policy in '{policy['namespace']}'",
                    severity=HIGH,
                    status="pass",
                    category="network-security",
                    target=f"namespace/{policy['namespace']}",
                )

    # ------------------------------------------------------------------
    # RBAC Checks
    # ------------------------------------------------------------------

    def _check_rbac(self, bindings: list[dict]) -> None:
        """Check RBAC for overly permissive bindings."""
        dangerous_roles = {"cluster-admin"}

        for binding in bindings:
            role_name = binding.get("role_ref", {}).get("name", "")
            if role_name in dangerous_roles:
                for subject in binding.get("subjects", []):
                    if subject["kind"] == "ServiceAccount":
                        self._add_finding(
                            rule_id="K8S-RBAC-001",
                            title=f"ServiceAccount bound to {role_name}",
                            severity=CRITICAL,
                            status="fail",
                            category="rbac",
                            target=f"sa/{subject.get('namespace', 'cluster')}/{subject['name']}",
                            detail=f"ClusterRoleBinding '{binding['name']}' grants {role_name} to SA '{subject['name']}'.",
                            remediation="Use a more restrictive ClusterRole.",
                        )
                    elif subject["kind"] == "Group" and subject["name"] == "system:authenticated":
                        self._add_finding(
                            rule_id="K8S-RBAC-002",
                            title=f"All authenticated users bound to {role_name}",
                            severity=CRITICAL,
                            status="fail",
                            category="rbac",
                            target=f"group/{subject['name']}",
                            detail=f"ClusterRoleBinding '{binding['name']}' grants {role_name} to all authenticated users.",
                            remediation="Remove this binding. Use specific user/group bindings.",
                        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _add_finding(
        self,
        rule_id: str,
        title: str,
        severity: str,
        status: str,
        category: str,
        target: str,
        detail: str = "",
        remediation: str = "",
    ) -> None:
        """Add a finding to the results list."""
        self.findings.append(
            {
                "rule_id": rule_id,
                "title": title,
                "severity": severity,
                "status": status,
                "category": category,
                "target": target,
                "detail": detail,
                "remediation": remediation,
            }
        )
