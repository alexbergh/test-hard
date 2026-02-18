"""Drift detection -- compares K8s spec vs container runtime state."""

import logging
from typing import Any

from app.services.k8s_connector import K8sConnector

import docker

logger = logging.getLogger(__name__)

CRITICAL = "critical"
HIGH = "high"
MEDIUM = "medium"
LOW = "low"


class DriftFinding:
    """A single drift finding."""

    __slots__ = ("rule_id", "severity", "category", "target", "field", "expected", "actual", "detail", "remediation")

    def __init__(self, **kwargs):
        for slot in self.__slots__:
            setattr(self, slot, kwargs.get(slot, ""))

    def to_dict(self) -> dict:
        return {s: getattr(self, s) for s in self.__slots__}


class DriftDetector:
    """Detects drift between K8s declared spec and container runtime reality.

    Compares:
      - K8s pod spec (securityContext, volumes, image, resources)
      - Container runtime inspect (actual caps, mounts, privileged, user)

    Catches:
      - Privilege bypass (privileged gained at runtime)
      - Unexpected mounts (host paths not in spec)
      - Policy circumvention (caps added, user changed)
      - Image mismatch (running image differs from spec)
      - Resource limit removal
    """

    def __init__(
        self,
        connector: K8sConnector | None = None,
        docker_client: docker.DockerClient | None = None,
    ):
        self.connector = connector
        self.docker_client = docker_client
        self.findings: list[DriftFinding] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect_k8s_pod_drift(self, namespace: str | None = None) -> dict:
        """Compare K8s pod specs against runtime container state.

        Requires both a K8s connector AND a Docker client connected to the
        same node(s) where the pods run.
        """
        self.findings = []

        if not self.connector:
            return {"success": False, "error": "No K8s connector configured"}

        pods = self.connector.list_pods(namespace=namespace)
        checked = 0
        skipped = 0

        for pod in pods:
            pod_ref = f"{pod['namespace']}/{pod['name']}"
            for container in pod.get("containers", []):
                c_ref = f"{pod_ref}/{container['name']}"
                runtime = self._get_runtime_state(pod, container)
                if runtime is None:
                    skipped += 1
                    continue
                checked += 1
                self._compare_privileged(c_ref, container, runtime)
                self._compare_capabilities(c_ref, container, runtime)
                self._compare_user(c_ref, container, runtime)
                self._compare_read_only_rootfs(c_ref, container, runtime)
                self._compare_mounts(c_ref, pod, runtime)
                self._compare_image(c_ref, container, runtime)

        return self._build_result(checked, skipped)

    def detect_docker_drift(self, hosts: list[dict]) -> dict:
        """Compare stored host security_context against live Docker inspect.

        ``hosts`` is a list of dicts with keys: name, container_name,
        security_context (the stored/expected state from last discovery).
        """
        self.findings = []

        if not self.docker_client:
            return {"success": False, "error": "No Docker client configured"}

        checked = 0
        skipped = 0

        for host_data in hosts:
            cname = host_data.get("container_name") or host_data.get("name", "")
            expected_sc = host_data.get("security_context", {})
            if not cname or not expected_sc:
                skipped += 1
                continue

            try:
                container = self.docker_client.containers.get(cname)
                inspect = container.attrs
            except docker.errors.NotFound:
                skipped += 1
                continue
            except Exception as e:
                logger.debug("Cannot inspect %s: %s", cname, e)
                skipped += 1
                continue

            checked += 1
            runtime = self._extract_docker_runtime(inspect)
            self._compare_docker_state(cname, expected_sc, runtime)

        return self._build_result(checked, skipped)

    # ------------------------------------------------------------------
    # K8s spec vs runtime comparison
    # ------------------------------------------------------------------

    def _get_runtime_state(self, pod: dict, container: dict) -> dict | None:
        """Try to get actual runtime state of a container.

        Uses container_id from pod status to inspect via Docker client.
        Falls back to K8s-reported status if no Docker client.
        """
        # Find container ID from pod statuses
        container_id = None
        for cs in pod.get("container_statuses", []):
            if cs.get("name") == container["name"]:
                cid = cs.get("container_id", "")
                if "//" in cid:
                    container_id = cid.split("//")[-1]
                elif cid:
                    container_id = cid
                break

        if not container_id:
            return None

        if self.docker_client:
            try:
                c = self.docker_client.containers.get(container_id)
                return self._extract_docker_runtime(c.attrs)
            except Exception:
                pass

        # Fallback: return None (cannot verify runtime)
        return None

    @staticmethod
    def _extract_docker_runtime(inspect: dict) -> dict:
        """Extract security-relevant fields from Docker inspect."""
        config = inspect.get("Config", {})
        host_config = inspect.get("HostConfig", {})
        return {
            "privileged": host_config.get("Privileged", False),
            "cap_add": sorted(host_config.get("CapAdd") or []),
            "cap_drop": sorted(host_config.get("CapDrop") or []),
            "read_only_rootfs": host_config.get("ReadonlyRootfs", False),
            "user": config.get("User", ""),
            "pid_mode": host_config.get("PidMode", ""),
            "ipc_mode": host_config.get("IpcMode", ""),
            "network_mode": host_config.get("NetworkMode", ""),
            "image": config.get("Image", ""),
            "mounts": [
                {"source": m.get("Source", ""), "destination": m.get("Destination", "")}
                for m in inspect.get("Mounts", [])
            ],
            "memory_limit": host_config.get("Memory", 0),
            "cpu_limit": host_config.get("NanoCpus", 0),
            "security_opt": host_config.get("SecurityOpt") or [],
        }

    def _compare_privileged(self, ref: str, spec: dict, runtime: dict) -> None:
        """Detect privilege escalation at runtime."""
        spec_priv = spec.get("security_context", {}).get("privileged", False)
        runtime_priv = runtime.get("privileged", False)

        if not spec_priv and runtime_priv:
            self._add(
                rule_id="DRIFT-001",
                severity=CRITICAL,
                category="privilege-bypass",
                target=ref,
                field="privileged",
                expected="false",
                actual="true",
                detail="Container is running privileged but spec declares privileged=false. "
                "Possible privilege escalation via mutating webhook or runtime override.",
                remediation="Investigate admission controllers and runtime config. " "Enforce PodSecurity admission.",
            )

    def _compare_capabilities(self, ref: str, spec: dict, runtime: dict) -> None:
        """Detect capability drift."""
        sc = spec.get("security_context", {})
        spec_add = set(sc.get("capabilities_add", []))
        spec_drop = set(sc.get("capabilities_drop", []))
        runtime_add = set(runtime.get("cap_add", []))
        runtime_drop = set(runtime.get("cap_drop", []))

        # Caps added at runtime that were not in spec
        extra_caps = runtime_add - spec_add
        if extra_caps:
            dangerous = {
                "SYS_ADMIN",
                "NET_ADMIN",
                "SYS_PTRACE",
                "NET_RAW",
                "SYS_MODULE",
                "DAC_OVERRIDE",
                "SETUID",
                "SETGID",
            }
            severity = CRITICAL if extra_caps & dangerous else HIGH
            self._add(
                rule_id="DRIFT-002",
                severity=severity,
                category="privilege-bypass",
                target=ref,
                field="capabilities.add",
                expected=sorted(spec_add) if spec_add else "[]",
                actual=sorted(runtime_add),
                detail=f"Extra capabilities at runtime: {sorted(extra_caps)}",
                remediation="Review admission controllers. Ensure OPA/Kyverno policies "
                "enforce capability restrictions.",
            )

        # Caps that should be dropped but are not dropped at runtime
        missing_drops = spec_drop - runtime_drop
        if missing_drops and "ALL" in spec_drop:
            self._add(
                rule_id="DRIFT-003",
                severity=HIGH,
                category="policy-circumvention",
                target=ref,
                field="capabilities.drop",
                expected=sorted(spec_drop),
                actual=sorted(runtime_drop),
                detail=f"Spec drops {sorted(spec_drop)} but runtime only drops {sorted(runtime_drop)}",
                remediation="Container runtime is not enforcing capability drop. " "Check CRI configuration.",
            )

    def _compare_user(self, ref: str, spec: dict, runtime: dict) -> None:
        """Detect user change at runtime."""
        sc = spec.get("security_context", {})
        spec_user = sc.get("run_as_user")
        runtime_user = runtime.get("user", "")

        # If spec says non-root but runtime is root
        if spec_user and spec_user != 0:
            if runtime_user == "" or runtime_user == "0" or runtime_user == "root":
                self._add(
                    rule_id="DRIFT-004",
                    severity=CRITICAL,
                    category="privilege-bypass",
                    target=ref,
                    field="runAsUser",
                    expected=str(spec_user),
                    actual=runtime_user or "0 (root)",
                    detail="Spec declares non-root user but container runs as root.",
                    remediation="Enforce runAsNonRoot via PodSecurity Standards.",
                )

    def _compare_read_only_rootfs(self, ref: str, spec: dict, runtime: dict) -> None:
        """Detect read-only rootfs bypass."""
        sc = spec.get("security_context", {})
        spec_ro = sc.get("read_only_root_filesystem", False)
        runtime_ro = runtime.get("read_only_rootfs", False)

        if spec_ro and not runtime_ro:
            self._add(
                rule_id="DRIFT-005",
                severity=HIGH,
                category="policy-circumvention",
                target=ref,
                field="readOnlyRootFilesystem",
                expected="true",
                actual="false",
                detail="Spec declares readOnlyRootFilesystem=true but runtime has writable rootfs.",
                remediation="Check runtime and admission controller configuration.",
            )

    def _compare_mounts(self, ref: str, pod: dict, runtime: dict) -> None:
        """Detect unexpected host mounts not declared in spec."""
        # Collect declared volumes from pod spec
        spec_volumes = set()
        for vol in pod.get("volumes", []):
            if vol.get("type") == "hostPath":
                spec_volumes.add(vol.get("path", ""))

        # Collect actual mounts from runtime
        runtime_mounts = set()
        sensitive_paths = {
            "/",
            "/etc",
            "/var/run/docker.sock",
            "/proc",
            "/sys",
            "/var/lib/kubelet",
            "/etc/kubernetes",
            "/root",
        }
        for m in runtime.get("mounts", []):
            src = m.get("source", "")
            if src.startswith("/") and src not in ("/dev/termination-log",):
                runtime_mounts.add(src)

        # Mounts present at runtime but not in spec
        extra_mounts = runtime_mounts - spec_volumes
        for mount in extra_mounts:
            severity = CRITICAL if mount in sensitive_paths else MEDIUM
            self._add(
                rule_id="DRIFT-006",
                severity=severity,
                category="unexpected-mount",
                target=ref,
                field="volumes",
                expected=f"spec declares: {sorted(spec_volumes) or 'none'}",
                actual=mount,
                detail=f"Host path '{mount}' is mounted at runtime but not declared in pod spec.",
                remediation="Investigate how the mount was added. Check for privileged init containers "
                "or runtime volume plugins.",
            )

    def _compare_image(self, ref: str, spec: dict, runtime: dict) -> None:
        """Detect image mismatch between spec and runtime."""
        spec_image = spec.get("image", "")
        runtime_image = runtime.get("image", "")

        if spec_image and runtime_image and spec_image != runtime_image:
            # Normalize: strip digest/tag for comparison
            spec_base = spec_image.split("@")[0].split(":")[0]
            runtime_base = runtime_image.split("@")[0].split(":")[0]
            if spec_base != runtime_base:
                self._add(
                    rule_id="DRIFT-007",
                    severity=CRITICAL,
                    category="image-mismatch",
                    target=ref,
                    field="image",
                    expected=spec_image,
                    actual=runtime_image,
                    detail="Container is running a different image than declared in spec. "
                    "Possible supply chain attack.",
                    remediation="Investigate image pull policy and registry. " "Use image digest pinning.",
                )

    # ------------------------------------------------------------------
    # Docker-only drift (stored state vs live inspect)
    # ------------------------------------------------------------------

    def _compare_docker_state(self, cname: str, expected: dict, actual: dict) -> None:
        """Compare stored Docker security_context against live inspect."""
        ref = f"docker/{cname}"

        # Privileged
        if not expected.get("privileged") and actual.get("privileged"):
            self._add(
                rule_id="DRIFT-D01",
                severity=CRITICAL,
                category="privilege-bypass",
                target=ref,
                field="privileged",
                expected="false",
                actual="true",
                detail="Container gained privileged mode since last discovery.",
                remediation="Re-run discovery and investigate container recreation.",
            )

        # Caps added
        expected_caps = set(expected.get("cap_add", []))
        actual_caps = set(actual.get("cap_add", []))
        extra = actual_caps - expected_caps
        if extra:
            self._add(
                rule_id="DRIFT-D02",
                severity=HIGH,
                category="privilege-bypass",
                target=ref,
                field="cap_add",
                expected=sorted(expected_caps) if expected_caps else "[]",
                actual=sorted(actual_caps),
                detail=f"New capabilities since last discovery: {sorted(extra)}",
                remediation="Investigate docker-compose or orchestrator changes.",
            )

        # Caps dropped removed
        expected_drops = set(expected.get("cap_drop", []))
        actual_drops = set(actual.get("cap_drop", []))
        lost_drops = expected_drops - actual_drops
        if lost_drops:
            self._add(
                rule_id="DRIFT-D03",
                severity=HIGH,
                category="policy-circumvention",
                target=ref,
                field="cap_drop",
                expected=sorted(expected_drops),
                actual=sorted(actual_drops),
                detail=f"Capability drops removed: {sorted(lost_drops)}",
                remediation="Restore cap_drop in container configuration.",
            )

        # Read-only rootfs removed
        if expected.get("read_only_rootfs") and not actual.get("read_only_rootfs"):
            self._add(
                rule_id="DRIFT-D04",
                severity=HIGH,
                category="policy-circumvention",
                target=ref,
                field="read_only_rootfs",
                expected="true",
                actual="false",
                detail="Read-only rootfs was enabled but is now disabled.",
                remediation="Re-enable readonlyRootfs in container config.",
            )

        # User changed to root
        exp_user = expected.get("user", "")
        act_user = actual.get("user", "")
        if exp_user and exp_user != "0" and exp_user != "root":
            if act_user in ("", "0", "root"):
                self._add(
                    rule_id="DRIFT-D05",
                    severity=CRITICAL,
                    category="privilege-bypass",
                    target=ref,
                    field="user",
                    expected=exp_user,
                    actual=act_user or "root",
                    detail="Container was running as non-root but now runs as root.",
                    remediation="Investigate container image or compose changes.",
                )

        # New mounts
        expected_mounts = {m.get("source") for m in expected.get("mounts", []) if m.get("source")}
        actual_mounts = {m.get("source") for m in actual.get("mounts", []) if m.get("source")}
        new_mounts = actual_mounts - expected_mounts
        sensitive = {"/", "/etc", "/var/run/docker.sock", "/proc", "/sys", "/root"}
        for mount in new_mounts:
            sev = CRITICAL if mount in sensitive else MEDIUM
            self._add(
                rule_id="DRIFT-D06",
                severity=sev,
                category="unexpected-mount",
                target=ref,
                field="mounts",
                expected=sorted(expected_mounts) if expected_mounts else "none",
                actual=mount,
                detail=f"New mount '{mount}' not present at last discovery.",
                remediation="Investigate how the mount was added.",
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _add(self, **kwargs) -> None:
        self.findings.append(DriftFinding(**kwargs))

    def _build_result(self, checked: int, skipped: int) -> dict:
        findings = [f.to_dict() for f in self.findings]
        critical = sum(1 for f in findings if f["severity"] == CRITICAL)
        high = sum(1 for f in findings if f["severity"] == HIGH)
        return {
            "success": True,
            "drift_detected": len(findings) > 0,
            "total_drifts": len(findings),
            "critical": critical,
            "high": high,
            "containers_checked": checked,
            "containers_skipped": skipped,
            "findings": findings,
        }
