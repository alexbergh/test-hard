"""Scan ALL container images via trivy-server and generate .prom metric files.

Generates Prometheus metric files in reports/trivy/ that Telegraf picks up.
"""

import json
import os
import subprocess
import sys

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports", "trivy")

# All container images from docker-compose
IMAGES = [
    "ubuntu:22.04",
    "debian:12-slim",
    "registry.fedoraproject.org/fedora:40",
    "quay.io/centos/centos:stream9",
    "registry.altlinux.org/alt/alt:latest",
    "registry.altlinux.org/alt/alt:c10f2",
    "test-hard/dashboard-backend:latest",
    "test-hard/dashboard-frontend:latest",
    "grafana/grafana:12.3.3",
    "prom/prometheus:v2.52.0",
    "grafana/loki:2.9.0",
    "prom/alertmanager:v0.27.0",
    "grafana/promtail:3.3.0",
    "ghcr.io/alexbergh/test-hard:latest",  # telegraf
    "tecnativa/docker-socket-proxy:0.1.2",
    "aquasec/trivy:0.58.0",
    "falcosecurity/falcosidekick:2.29.0",
]


def safe_name(image: str) -> str:
    return image.replace("/", "-").replace(":", "-").replace(".", "-")


def scan_image(image: str) -> dict:
    """Scan image using trivy inside trivy-server container."""
    print(f"  Scanning {image}...", end=" ", flush=True)
    try:
        result = subprocess.run(
            [
                "docker", "exec", "trivy-server",
                "trivy", "image",
                "--server", "http://localhost:4954",
                "--format", "json",
                "--severity", "CRITICAL,HIGH,MEDIUM,LOW",
                "--ignore-unfixed",
                "--timeout", "5m",
                image,
            ],
            capture_output=True, text=True, timeout=360,
        )
        if result.returncode != 0 and not result.stdout:
            print(f"FAILED (exit {result.returncode})")
            # Try without --ignore-unfixed
            result = subprocess.run(
                [
                    "docker", "exec", "trivy-server",
                    "trivy", "image",
                    "--server", "http://localhost:4954",
                    "--format", "json",
                    "--severity", "CRITICAL,HIGH,MEDIUM,LOW",
                    "--timeout", "5m",
                    image,
                ],
                capture_output=True, text=True, timeout=360,
            )
        data = json.loads(result.stdout)
        return data
    except json.JSONDecodeError:
        print("FAILED (bad JSON)")
        return {}
    except subprocess.TimeoutExpired:
        print("TIMEOUT")
        return {}
    except Exception as e:
        print(f"ERROR: {e}")
        return {}


def generate_prom_metrics(image: str, data: dict) -> str:
    """Generate Prometheus metric file content from Trivy JSON output."""
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    total_packages = 0

    for result in data.get("Results", []):
        vulns = result.get("Vulnerabilities") or []
        total_packages += len(result.get("Packages") or [])
        for v in vulns:
            sev = v.get("Severity", "UNKNOWN").upper()
            counts[sev] = counts.get(sev, 0) + 1

    total_vulns = sum(counts.values())
    safe_image = image.replace('"', '\\"')

    lines = [
        "# HELP trivy_image_vulnerabilities Number of vulnerabilities in image",
        "# TYPE trivy_image_vulnerabilities gauge",
    ]
    for sev, count in counts.items():
        lines.append(f'trivy_image_vulnerabilities{{image="{safe_image}",severity="{sev.lower()}"}} {count}')

    lines.extend([
        "# HELP trivy_image_vulnerability_total Total vulnerabilities",
        "# TYPE trivy_image_vulnerability_total gauge",
        f'trivy_image_vulnerability_total{{image="{safe_image}"}} {total_vulns}',
        "# HELP trivy_image_packages_total Total packages",
        "# TYPE trivy_image_packages_total gauge",
        f'trivy_image_packages_total{{image="{safe_image}"}} {total_packages}',
    ])

    return "\n".join(lines) + "\n"


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)

    print(f"Scanning {len(IMAGES)} container images via trivy-server")
    print(f"Reports dir: {REPORTS_DIR}\n")

    total = 0
    for image in IMAGES:
        data = scan_image(image)
        if not data:
            continue

        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for result in data.get("Results", []):
            for v in (result.get("Vulnerabilities") or []):
                sev = v.get("Severity", "UNKNOWN").upper()
                if sev in counts:
                    counts[sev] += 1
        total_vulns = sum(counts.values())

        print(f"C={counts['CRITICAL']} H={counts['HIGH']} M={counts['MEDIUM']} L={counts['LOW']} total={total_vulns}")

        # Write .prom metrics file
        sn = safe_name(image)
        prom_content = generate_prom_metrics(image, data)
        prom_path = os.path.join(REPORTS_DIR, f"{sn}_metrics.prom")
        with open(prom_path, "w") as f:
            f.write(prom_content)

        # Write JSON report
        json_path = os.path.join(REPORTS_DIR, f"{sn}.vuln.json")
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)

        total += 1

    print(f"\nDone. Scanned {total}/{len(IMAGES)} images.")
    print("Telegraf will pick up metrics on next interval (60s).")


if __name__ == "__main__":
    main()
