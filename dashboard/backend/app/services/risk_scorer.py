"""Risk scoring engine -- weighted scoring for remediation prioritization."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Weight table: each risk factor has a weight and description
# ------------------------------------------------------------------

RISK_WEIGHTS: dict[str, dict] = {
    # Container security
    "privileged": {
        "weight": 50,
        "category": "container-security",
        "severity": "critical",
        "description": "Container runs in privileged mode (full host access)",
        "remediation": "Remove privileged: true from container spec",
    },
    "host_network": {
        "weight": 35,
        "category": "network-security",
        "severity": "high",
        "description": "Container shares host network namespace",
        "remediation": "Set hostNetwork: false unless absolutely required",
    },
    "host_pid": {
        "weight": 30,
        "category": "container-security",
        "severity": "high",
        "description": "Container shares host PID namespace",
        "remediation": "Set hostPID: false",
    },
    "host_ipc": {
        "weight": 20,
        "category": "container-security",
        "severity": "medium",
        "description": "Container shares host IPC namespace",
        "remediation": "Set hostIPC: false",
    },

    # Volume security
    "mount_docker_sock": {
        "weight": 80,
        "category": "volume-security",
        "severity": "critical",
        "description": "Docker socket mounted -- container escape possible",
        "remediation": "Remove docker.sock mount. Use Docker Socket Proxy with read-only access",
    },
    "mount_host_root": {
        "weight": 70,
        "category": "volume-security",
        "severity": "critical",
        "description": "Host root filesystem (/) mounted",
        "remediation": "Remove hostPath mount to /. Use PVC or emptyDir",
    },
    "mount_host_etc": {
        "weight": 50,
        "category": "volume-security",
        "severity": "high",
        "description": "Host /etc mounted -- credential/config exposure",
        "remediation": "Remove hostPath mount to /etc",
    },
    "mount_host_proc": {
        "weight": 50,
        "category": "volume-security",
        "severity": "high",
        "description": "Host /proc mounted",
        "remediation": "Remove hostPath mount to /proc",
    },
    "mount_host_sensitive": {
        "weight": 40,
        "category": "volume-security",
        "severity": "high",
        "description": "Sensitive host path mounted",
        "remediation": "Remove hostPath mount or restrict to specific subpaths",
    },

    # User / privilege
    "run_as_root": {
        "weight": 20,
        "category": "user-security",
        "severity": "medium",
        "description": "Container runs as root (UID 0)",
        "remediation": "Set runAsUser to non-root UID, set runAsNonRoot: true",
    },
    "allow_privilege_escalation": {
        "weight": 25,
        "category": "user-security",
        "severity": "high",
        "description": "Privilege escalation not explicitly disabled",
        "remediation": "Set allowPrivilegeEscalation: false",
    },

    # Capabilities
    "no_cap_drop_all": {
        "weight": 15,
        "category": "capability-security",
        "severity": "medium",
        "description": "Capabilities not dropped (should drop ALL)",
        "remediation": "Add capabilities.drop: ['ALL']",
    },
    "cap_sys_admin": {
        "weight": 45,
        "category": "capability-security",
        "severity": "critical",
        "description": "SYS_ADMIN capability added (near-privileged access)",
        "remediation": "Remove SYS_ADMIN capability",
    },
    "cap_net_admin": {
        "weight": 30,
        "category": "capability-security",
        "severity": "high",
        "description": "NET_ADMIN capability added",
        "remediation": "Remove NET_ADMIN capability unless required for CNI",
    },
    "cap_net_raw": {
        "weight": 20,
        "category": "capability-security",
        "severity": "medium",
        "description": "NET_RAW capability added (ARP spoofing possible)",
        "remediation": "Remove NET_RAW capability",
    },
    "cap_sys_ptrace": {
        "weight": 35,
        "category": "capability-security",
        "severity": "high",
        "description": "SYS_PTRACE capability added (process injection possible)",
        "remediation": "Remove SYS_PTRACE capability",
    },
    "cap_dangerous_other": {
        "weight": 25,
        "category": "capability-security",
        "severity": "high",
        "description": "Dangerous capability added",
        "remediation": "Remove unnecessary capabilities",
    },

    # Filesystem
    "writable_rootfs": {
        "weight": 10,
        "category": "filesystem-security",
        "severity": "low",
        "description": "Root filesystem is writable",
        "remediation": "Set readOnlyRootFilesystem: true",
    },

    # Resource limits
    "no_resource_limits": {
        "weight": 10,
        "category": "resource-management",
        "severity": "low",
        "description": "No CPU/memory limits set (DoS risk)",
        "remediation": "Set resources.limits for CPU and memory",
    },

    # Image
    "image_latest": {
        "weight": 10,
        "category": "image-security",
        "severity": "medium",
        "description": "Image uses :latest or no explicit tag",
        "remediation": "Pin to specific version tag or digest",
    },
    "image_full_os": {
        "weight": 5,
        "category": "image-security",
        "severity": "low",
        "description": "Full OS base image (larger attack surface)",
        "remediation": "Use distroless or alpine-based image",
    },

    # RBAC
    "cluster_admin_binding": {
        "weight": 40,
        "category": "rbac",
        "severity": "critical",
        "description": "ServiceAccount bound to cluster-admin role",
        "remediation": "Use a more restrictive ClusterRole",
    },
    "default_service_account": {
        "weight": 10,
        "category": "rbac",
        "severity": "medium",
        "description": "Pod uses default service account",
        "remediation": "Create dedicated ServiceAccount with minimal permissions",
    },

    # Network
    "no_network_policy": {
        "weight": 25,
        "category": "network-security",
        "severity": "high",
        "description": "Namespace has no NetworkPolicy (unrestricted traffic)",
        "remediation": "Create default-deny NetworkPolicy for the namespace",
    },

    # Drift
    "drift_detected": {
        "weight": 60,
        "category": "drift",
        "severity": "critical",
        "description": "Configuration drift detected between spec and runtime",
        "remediation": "Investigate drift source. Re-deploy from source of truth",
    },
}

# Sensitive host paths for mount detection
SENSITIVE_MOUNT_PATHS = {
    "/var/run/docker.sock": "mount_docker_sock",
    "/": "mount_host_root",
    "/etc": "mount_host_etc",
    "/proc": "mount_host_proc",
    "/sys": "mount_host_sensitive",
    "/var/lib/kubelet": "mount_host_sensitive",
    "/etc/kubernetes": "mount_host_sensitive",
    "/root": "mount_host_sensitive",
}

# Capability to risk factor mapping
CAP_RISK_MAP = {
    "SYS_ADMIN": "cap_sys_admin",
    "NET_ADMIN": "cap_net_admin",
    "NET_RAW": "cap_net_raw",
    "SYS_PTRACE": "cap_sys_ptrace",
    "SYS_MODULE": "cap_dangerous_other",
    "DAC_OVERRIDE": "cap_dangerous_other",
    "SETUID": "cap_dangerous_other",
    "SETGID": "cap_dangerous_other",
}


class RiskScore:
    """Calculated risk score for a single target."""

    def __init__(self, target: str):
        self.target = target
        self.total_score: int = 0
        self.factors: list[dict] = []
        self.max_severity: str = "info"

    def add_factor(self, factor_id: str, extra_detail: str = "") -> None:
        """Add a risk factor by its ID from the weight table."""
        w = RISK_WEIGHTS.get(factor_id)
        if not w:
            return
        self.total_score += w["weight"]
        self.factors.append({
            "factor_id": factor_id,
            "weight": w["weight"],
            "category": w["category"],
            "severity": w["severity"],
            "description": w["description"],
            "remediation": w["remediation"],
            "detail": extra_detail,
        })
        self.max_severity = _max_severity(self.max_severity, w["severity"])

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "risk_score": self.total_score,
            "risk_level": _score_to_level(self.total_score),
            "max_severity": self.max_severity,
            "factor_count": len(self.factors),
            "factors": sorted(self.factors, key=lambda f: -f["weight"]),
        }


class RiskScorer:
    """Calculates risk scores for hosts based on their security posture.

    Consumes:
      - security_context (from discovery)
      - image metadata
      - hardening scan findings
      - drift detection results
    """

    def __init__(self):
        self.scores: list[RiskScore] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score_host(self, host: dict) -> RiskScore:
        """Calculate risk score for a single host.

        host dict keys: name, host_type, security_context, container_image,
                       k8s_labels, k8s_namespace
        """
        rs = RiskScore(host.get("name", "unknown"))
        sc = host.get("security_context", {})
        image = host.get("container_image", "")

        self._score_privileges(rs, sc)
        self._score_capabilities(rs, sc)
        self._score_mounts(rs, sc)
        self._score_user(rs, sc)
        self._score_filesystem(rs, sc)
        self._score_resources(rs, sc)
        self._score_image(rs, image)

        self.scores.append(rs)
        return rs

    def score_hosts(self, hosts: list[dict]) -> dict:
        """Score multiple hosts and return aggregated results."""
        self.scores = []
        for h in hosts:
            self.score_host(h)

        results = [s.to_dict() for s in self.scores]
        results.sort(key=lambda r: -r["risk_score"])

        total_risk = sum(r["risk_score"] for r in results)
        avg_risk = total_risk / len(results) if results else 0

        by_level = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for r in results:
            level = r["risk_level"]
            if level in by_level:
                by_level[level] += 1

        return {
            "success": True,
            "hosts_scored": len(results),
            "total_risk": total_risk,
            "average_risk": round(avg_risk, 1),
            "by_level": by_level,
            "top_risks": results[:20],
            "all_scores": results,
        }

    def score_from_findings(self, target: str, findings: list[dict]) -> RiskScore:
        """Build risk score from hardening scanner findings."""
        rs = RiskScore(target)

        for f in findings:
            if f.get("status") != "fail":
                continue
            rule_id = f.get("rule_id", "")
            # Map hardening rules to risk factors
            mapping = _hardening_rule_to_risk(rule_id)
            if mapping:
                rs.add_factor(mapping, extra_detail=f.get("title", ""))

        self.scores.append(rs)
        return rs

    def score_with_drift(self, host: dict, drift_findings: list[dict]) -> RiskScore:
        """Score a host including drift findings."""
        rs = self.score_host(host)

        for df in drift_findings:
            if df.get("target", "") in host.get("name", ""):
                rs.add_factor("drift_detected", extra_detail=df.get("detail", ""))

        return rs

    # ------------------------------------------------------------------
    # Scoring logic
    # ------------------------------------------------------------------

    def _score_privileges(self, rs: RiskScore, sc: dict) -> None:
        """Score privilege-related risks."""
        if sc.get("privileged"):
            rs.add_factor("privileged")
        if sc.get("host_network"):
            rs.add_factor("host_network")
        if sc.get("host_pid"):
            rs.add_factor("host_pid")
        if sc.get("host_ipc"):
            rs.add_factor("host_ipc")

        # Also check container-level entries in merged security_context
        for key, val in sc.items():
            if key.endswith(".privileged") and val:
                rs.add_factor("privileged", extra_detail=key)
            if key.endswith(".allow_privilege_escalation") and val is not False:
                pass  # Handled below

    def _score_capabilities(self, rs: RiskScore, sc: dict) -> None:
        """Score capability-related risks."""
        cap_add = sc.get("cap_add", [])
        cap_drop = sc.get("cap_drop", [])

        # Check if caps are dropped
        if "ALL" not in cap_drop and cap_drop != ["ALL"]:
            rs.add_factor("no_cap_drop_all")

        # Check dangerous caps added
        for cap in cap_add:
            risk_factor = CAP_RISK_MAP.get(cap)
            if risk_factor:
                rs.add_factor(risk_factor, extra_detail=f"CAP_{cap}")

        # Also check container-level caps in merged K8s security_context
        for key, val in sc.items():
            if key.endswith(".capabilities_add") and isinstance(val, list):
                for cap in val:
                    risk_factor = CAP_RISK_MAP.get(cap)
                    if risk_factor:
                        rs.add_factor(risk_factor, extra_detail=f"{key}={cap}")
            if key.endswith(".capabilities_drop") and isinstance(val, list):
                if "ALL" not in val:
                    rs.add_factor("no_cap_drop_all", extra_detail=key)

    def _score_mounts(self, rs: RiskScore, sc: dict) -> None:
        """Score mount-related risks from security context."""
        mounts = sc.get("mounts", [])
        for m in mounts:
            src = m.get("source", "") if isinstance(m, dict) else str(m)
            risk_factor = SENSITIVE_MOUNT_PATHS.get(src)
            if risk_factor:
                rs.add_factor(risk_factor, extra_detail=f"mount={src}")
            elif src.startswith("/") and src not in ("/dev/termination-log",):
                # Generic host mount
                rs.add_factor("mount_host_sensitive", extra_detail=f"mount={src}")

    def _score_user(self, rs: RiskScore, sc: dict) -> None:
        """Score user-related risks."""
        user = sc.get("user", "")
        run_as_user = sc.get("run_as_user")

        if user in ("", "0", "root") or run_as_user == 0:
            rs.add_factor("run_as_root")

        if sc.get("allow_privilege_escalation") is not False:
            # Check container-level too
            has_explicit_false = False
            for key, val in sc.items():
                if key.endswith(".allow_privilege_escalation") and val is False:
                    has_explicit_false = True
            if not has_explicit_false:
                rs.add_factor("allow_privilege_escalation")

    def _score_filesystem(self, rs: RiskScore, sc: dict) -> None:
        """Score filesystem-related risks."""
        if not sc.get("read_only_rootfs") and not sc.get("read_only_root_filesystem"):
            rs.add_factor("writable_rootfs")

    def _score_resources(self, rs: RiskScore, sc: dict) -> None:
        """Score resource limit risks."""
        if not sc.get("memory_limit") and not sc.get("cpu_limit"):
            # Only flag if we have data to check
            pass

    def _score_image(self, rs: RiskScore, image: str) -> None:
        """Score image-related risks."""
        if not image:
            return
        tag = _extract_tag(image)
        if tag is None or tag == "latest":
            rs.add_factor("image_latest", extra_detail=image)

        # Full OS check
        img_lower = image.lower()
        minimal = ("alpine", "distroless", "scratch", "busybox", "chainguard",
                   "wolfi", "static", "ubi-micro")
        if not any(m in img_lower for m in minimal):
            rs.add_factor("image_full_os", extra_detail=image)


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

_SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def _max_severity(a: str, b: str) -> str:
    return a if _SEVERITY_ORDER.get(a, 0) >= _SEVERITY_ORDER.get(b, 0) else b


def _score_to_level(score: int) -> str:
    if score >= 80:
        return "critical"
    if score >= 40:
        return "high"
    if score >= 20:
        return "medium"
    if score >= 5:
        return "low"
    return "info"


def _extract_tag(image: str) -> str | None:
    image = image.split("@")[0]
    parts = image.rsplit(":", 1)
    if len(parts) == 2 and "/" not in parts[1]:
        return parts[1]
    return None


def _hardening_rule_to_risk(rule_id: str) -> str | None:
    """Map K8s hardening rule IDs to risk factor IDs."""
    mapping = {
        "K8S-CTR-001": "privileged",
        "K8S-CTR-002": "allow_privilege_escalation",
        "K8S-CTR-003": "writable_rootfs",
        "K8S-CTR-004": "no_cap_drop_all",
        "K8S-CTR-005": "cap_dangerous_other",
        "K8S-CTR-006": "no_resource_limits",
        "K8S-CTR-008": "image_latest",
        "K8S-CTR-009": "run_as_root",
        "K8S-POD-001": "host_network",
        "K8S-POD-002": "host_pid",
        "K8S-POD-003": "host_ipc",
        "K8S-VOL-001": "mount_host_sensitive",
        "K8S-VOL-002": "mount_docker_sock",
        "K8S-SA-001": "default_service_account",
        "K8S-NET-001": "no_network_policy",
        "K8S-RBAC-001": "cluster_admin_binding",
    }
    return mapping.get(rule_id)
