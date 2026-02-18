"""Image-oriented security checks -- without CVE scanning."""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

CRITICAL = "critical"
HIGH = "high"
MEDIUM = "medium"
LOW = "low"
INFO = "info"

# Known distroless base images
DISTROLESS_PATTERNS = (
    "gcr.io/distroless/",
    "cgr.dev/chainguard/",
    "docker.io/chainguard/",
    "mcr.microsoft.com/cbl-mariner/distroless/",
    "registry.access.redhat.com/ubi9-micro",
    "registry.access.redhat.com/ubi8-micro",
)

# Images known to run as root by default
ROOT_DEFAULT_IMAGES = (
    "nginx", "httpd", "apache", "mysql", "mariadb", "postgres",
    "redis", "mongo", "memcached", "elasticsearch", "kibana",
    "grafana/grafana", "prom/prometheus", "jenkins",
)

# Scratch / minimal base indicators
MINIMAL_BASES = (
    "scratch", "busybox", "alpine", "distroless", "static",
    "chainguard", "wolfi",
)


class ImageFinding:
    """Single image check finding."""

    __slots__ = ("rule_id", "severity", "status", "category",
                 "target", "detail", "remediation")

    def __init__(self, **kwargs):
        for slot in self.__slots__:
            setattr(self, slot, kwargs.get(slot, ""))

    def to_dict(self) -> dict:
        return {s: getattr(self, s) for s in self.__slots__}


class ImageChecker:
    """Checks container images for security best practices.

    Checks performed (no CVE needed):
      - Latest / untagged image detection
      - Root user default detection
      - Distroless vs full OS image classification
      - Digest pinning verification
      - Base image age heuristic (tag version)
      - Known vulnerable base detection
      - Multi-stage / bloat detection (layer count)
    """

    def __init__(self):
        self.findings: list[ImageFinding] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_images(self, images: list[dict]) -> dict:
        """Run all image checks.

        Each image dict should have:
          - image: str (full image reference)
          - user: str (configured user, "" means root)
          - target: str (pod/container reference)
          - labels: dict (optional, image labels)
          - layer_count: int (optional)
        """
        self.findings = []

        for img in images:
            ref = img.get("target", img.get("image", "unknown"))
            image = img.get("image", "")
            if not image:
                continue

            self._check_tag(ref, image)
            self._check_digest_pinning(ref, image)
            self._check_root_user(ref, image, img.get("user", ""))
            self._check_distroless(ref, image)
            self._check_base_age(ref, image)
            self._check_known_risky_bases(ref, image)
            if img.get("layer_count"):
                self._check_layer_bloat(ref, image, img["layer_count"])

        return self._build_result(images)

    def check_from_hosts(self, hosts: list[dict]) -> dict:
        """Check images from Host records (as stored in DB).

        Each host dict should have: name, container_image, security_context.
        """
        images = []
        for h in hosts:
            sc = h.get("security_context", {})
            images.append({
                "image": h.get("container_image", ""),
                "user": sc.get("user", ""),
                "target": h.get("name", ""),
                "labels": h.get("k8s_labels", {}),
            })
        return self.check_images(images)

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------

    def _check_tag(self, ref: str, image: str) -> None:
        """IMG-001: Detect :latest or untagged images."""
        tag = _extract_tag(image)

        if tag is None or tag == "latest":
            self._add(
                rule_id="IMG-001",
                severity=MEDIUM,
                status="fail",
                category="image-tag",
                target=ref,
                detail=f"Image '{image}' uses {'no tag' if tag is None else ':latest'}. "
                "This makes builds non-reproducible and complicates rollback.",
                remediation="Pin to a specific version tag (e.g., nginx:1.25.3-alpine).",
            )
        else:
            self._add(
                rule_id="IMG-001",
                severity=MEDIUM,
                status="pass",
                category="image-tag",
                target=ref,
                detail=f"Image uses explicit tag: {tag}",
            )

    def _check_digest_pinning(self, ref: str, image: str) -> None:
        """IMG-002: Check if image uses digest pinning (@sha256:...)."""
        if "@sha256:" in image:
            self._add(
                rule_id="IMG-002",
                severity=LOW,
                status="pass",
                category="image-pinning",
                target=ref,
                detail="Image is pinned by digest.",
            )
        else:
            self._add(
                rule_id="IMG-002",
                severity=LOW,
                status="fail",
                category="image-pinning",
                target=ref,
                detail=f"Image '{image}' is not pinned by digest. "
                "Tags are mutable and can be overwritten.",
                remediation="Use digest pinning: image@sha256:<digest>",
            )

    def _check_root_user(self, ref: str, image: str, user: str) -> None:
        """IMG-003: Detect images running as root."""
        runs_as_root = user in ("", "0", "root")

        # Check if this is a known root-default image
        img_lower = image.lower()
        is_known_root = any(base in img_lower for base in ROOT_DEFAULT_IMAGES)

        if runs_as_root:
            severity = HIGH if is_known_root else MEDIUM
            detail = f"Container runs as root (user='{user or 'unset (root)'}')."
            if is_known_root:
                detail += f" '{_image_base(image)}' runs as root by default."
            self._add(
                rule_id="IMG-003",
                severity=severity,
                status="fail",
                category="image-user",
                target=ref,
                detail=detail,
                remediation="Set USER in Dockerfile or securityContext.runAsUser to non-root UID.",
            )
        else:
            self._add(
                rule_id="IMG-003",
                severity=MEDIUM,
                status="pass",
                category="image-user",
                target=ref,
                detail=f"Container runs as non-root user: {user}",
            )

    def _check_distroless(self, ref: str, image: str) -> None:
        """IMG-004: Classify image as distroless/minimal vs full OS."""
        img_lower = image.lower()

        is_distroless = any(p in img_lower for p in DISTROLESS_PATTERNS)
        is_minimal = any(b in img_lower for b in MINIMAL_BASES)

        if is_distroless:
            self._add(
                rule_id="IMG-004",
                severity=INFO,
                status="pass",
                category="image-base",
                target=ref,
                detail=f"Image uses distroless/minimal base: {image}",
            )
        elif is_minimal:
            self._add(
                rule_id="IMG-004",
                severity=LOW,
                status="pass",
                category="image-base",
                target=ref,
                detail=f"Image uses minimal base (alpine/busybox/scratch).",
            )
        else:
            # Full OS image -- larger attack surface
            self._add(
                rule_id="IMG-004",
                severity=LOW,
                status="fail",
                category="image-base",
                target=ref,
                detail=f"Image '{_image_base(image)}' appears to use a full OS base. "
                "Full OS images have larger attack surface (shell, package managers, etc.).",
                remediation="Consider migrating to distroless or alpine-based images.",
            )

    def _check_base_age(self, ref: str, image: str) -> None:
        """IMG-005: Heuristic check for outdated base versions from tag."""
        tag = _extract_tag(image)
        if not tag or tag == "latest":
            return

        # Try to parse major version from tag
        version_match = re.match(r"(\d+)(?:\.(\d+))?", tag)
        if not version_match:
            return

        major = int(version_match.group(1))
        img_lower = image.lower()

        # Known EOL version checks
        eol_checks = {
            "python": (3, 8, "Python 3.8 is EOL"),
            "node": (16, None, "Node.js 16 is EOL"),
            "golang": (1, 19, "Go 1.19 is EOL"),
            "ruby": (2, 7, "Ruby 2.7 is EOL"),
            "php": (7, None, "PHP 7.x is EOL"),
            "ubuntu": (20, None, "Ubuntu 20.04 LTS nearing EOL"),
            "debian": (10, None, "Debian 10 (buster) is EOL"),
            "centos": (7, None, "CentOS 7 is EOL"),
            "alpine": (3, 15, "Alpine 3.15 is EOL"),
        }

        for base, (eol_major, eol_minor, msg) in eol_checks.items():
            if base in img_lower:
                minor = int(version_match.group(2)) if version_match.group(2) else None
                is_old = False
                if major < eol_major:
                    is_old = True
                elif major == eol_major and eol_minor and minor is not None and minor <= eol_minor:
                    is_old = True

                if is_old:
                    self._add(
                        rule_id="IMG-005",
                        severity=MEDIUM,
                        status="fail",
                        category="image-age",
                        target=ref,
                        detail=f"{msg}. Image: {image}",
                        remediation=f"Upgrade to a supported {base} version.",
                    )
                break

    def _check_known_risky_bases(self, ref: str, image: str) -> None:
        """IMG-006: Flag images known for security issues."""
        img_lower = image.lower()

        risky = {
            "phpmyadmin": "phpMyAdmin images are frequent attack targets.",
            "wordpress": "WordPress images require careful hardening.",
            "jenkins/jenkins": "Jenkins images often run as root with broad permissions.",
            "mongo:": "MongoDB images run without auth by default.",
            "redis:": "Redis images have no auth by default.",
            "elasticsearch": "Elasticsearch images run as root on older versions.",
        }

        for pattern, msg in risky.items():
            if pattern in img_lower:
                self._add(
                    rule_id="IMG-006",
                    severity=LOW,
                    status="warning",
                    category="image-risk",
                    target=ref,
                    detail=f"{msg} Image: {image}",
                    remediation="Ensure proper network isolation and authentication configuration.",
                )
                break

    def _check_layer_bloat(self, ref: str, image: str, layer_count: int) -> None:
        """IMG-007: Detect bloated images (many layers)."""
        if layer_count > 30:
            self._add(
                rule_id="IMG-007",
                severity=LOW,
                status="fail",
                category="image-bloat",
                target=ref,
                detail=f"Image has {layer_count} layers, indicating possible bloat.",
                remediation="Use multi-stage builds and minimize RUN instructions.",
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _add(self, **kwargs) -> None:
        self.findings.append(ImageFinding(**kwargs))

    def _build_result(self, images: list[dict]) -> dict:
        findings = [f.to_dict() for f in self.findings]
        passed = sum(1 for f in findings if f["status"] == "pass")
        failed = sum(1 for f in findings if f["status"] == "fail")
        warnings = sum(1 for f in findings if f["status"] == "warning")
        return {
            "success": True,
            "images_checked": len(images),
            "total_checks": len(findings),
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "findings": findings,
        }


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------


def _extract_tag(image: str) -> str | None:
    """Extract tag from image reference. Returns None if no tag."""
    # Remove digest
    image = image.split("@")[0]
    # Find tag
    parts = image.rsplit(":", 1)
    if len(parts) == 2 and "/" not in parts[1]:
        return parts[1]
    return None


def _image_base(image: str) -> str:
    """Extract base name from image (no tag, no registry)."""
    image = image.split("@")[0].split(":")[0]
    # Remove registry prefix if present
    parts = image.split("/")
    if len(parts) >= 2 and ("." in parts[0] or ":" in parts[0]):
        return "/".join(parts[1:])
    return image
