#!/usr/bin/env python3
"""Симуляция kind-кластера для генерации логов и сводки ресурсов."""
from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
FSTEC_CONTENT_DIR = BASE_DIR.parent / "docker" / "openscap" / "content" / "fstec"
FALLBACK_OVAL_FILE = BASE_DIR.parent / "docker" / "openscap" / "content" / "sample-oval.xml"
RNG = random.Random(314)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_resource_block(block: str) -> dict | None:
    kind = None
    name = None
    namespace = None
    images: list[str] = []
    in_metadata = False
    for raw_line in block.splitlines():
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue
        if raw_line.strip() == "---":
            continue
        if raw_line.strip().startswith("kind:"):
            kind = raw_line.split(":", 1)[1].strip()
            continue
        if raw_line.strip().startswith("metadata:"):
            in_metadata = True
            continue
        if in_metadata:
            if raw_line.startswith("  "):
                stripped = raw_line.strip()
                if stripped.startswith("name:") and name is None:
                    name = stripped.split(":", 1)[1].strip()
                elif stripped.startswith("namespace:") and namespace is None:
                    namespace = stripped.split(":", 1)[1].strip()
            else:
                in_metadata = False
        if raw_line.strip().startswith("image:"):
            images.append(raw_line.split(":", 1)[1].strip())
    if not kind and not name:
        return None
    return {"kind": kind, "name": name, "namespace": namespace, "images": images}


def collect_manifests() -> list[dict]:
    resources: list[dict] = []
    for manifest in [
        BASE_DIR / "namespace.yaml",
        BASE_DIR / "openscap-job.yaml",
        BASE_DIR / "telemetry.yaml",
        BASE_DIR / "wazuh.yaml",
    ]:
        if not manifest.exists():
            continue
        content = manifest.read_text(encoding="utf-8")
        for block in content.split("---"):
            resource = parse_resource_block(block)
            if resource:
                resource["source"] = manifest.name
                resources.append(resource)
    return resources


def parse_definitions_from_file(path: Path) -> list[dict]:
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {"def": "http://oval.mitre.org/XMLSchema/oval-definitions-5", "oval": "http://oval.mitre.org/XMLSchema/oval-common-5"}
    parsed: list[dict] = []
    for definition in root.findall("def:definitions/def:definition", ns):
        parsed.append(
            {
                "id": definition.get("id", "unknown"),
                "title": definition.findtext("def:metadata/def:title", default="", namespaces=ns),
                "severity": definition.findtext("def:metadata/oval:advisory/oval:severity", default="", namespaces=ns),
                "platforms": [
                    platform.text.strip()
                    for platform in definition.findall("def:metadata/def:affected/def:platform", ns)
                    if platform.text
                ],
            }
        )
    return parsed


def load_fstec_definitions() -> list[dict]:
    manifest_path = FSTEC_CONTENT_DIR / "manifest.json"
    definitions: list[dict] = []
    if manifest_path.exists():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        for file_entry in data.get("files", []):
            for definition in file_entry.get("definitions", []):
                definitions.append(
                    {
                        "id": definition.get("id", "unknown"),
                        "title": definition.get("title", ""),
                        "severity": definition.get("severity") or "",
                        "platforms": definition.get("platforms", []),
                    }
                )
    else:
        xml_files = sorted(FSTEC_CONTENT_DIR.rglob("*.xml")) if FSTEC_CONTENT_DIR.exists() else []
        for xml_file in xml_files:
            definitions.extend(parse_definitions_from_file(xml_file))
    if not definitions and FALLBACK_OVAL_FILE.exists():
        definitions = parse_definitions_from_file(FALLBACK_OVAL_FILE)
    return definitions


def simulate_openscap() -> dict:
    ensure_dir(ARTIFACTS_DIR)
    items = []
    for idx, definition in enumerate(load_fstec_definitions(), start=1):
        status = "passed" if idx % 2 == 1 else "failed"
        message = (
            f"Определение {definition.get('id')} для платформ {', '.join(definition.get('platforms', [])) or 'n/a'}"
            if status == "passed"
            else f"Несоответствие {definition.get('title')} (severity={definition.get('severity') or 'n/a'})"
        )
        items.append(
            {
                "title": definition.get("title", ""),
                "status": status,
                "message": message,
            }
        )

    log_lines = [
        "OpenSCAP Kubernetes Job (симуляция)",
        f"Timestamp: {timestamp()}",
        "Results:",
    ]
    for item in items:
        log_lines.append(f"- {item['title']}: {item['status']} ({item['message']})")

    log_path = ARTIFACTS_DIR / "openscap-job.log"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")

    return {"results": items, "log": str(log_path)}


def simulate_telemetry() -> dict:
    lines = []
    for seq in range(1, 6):
        lines.append(
            f"[{timestamp()}] telegraf-collector sequence={seq} host=simulated-k8s-osquery severity="
            f"{RNG.choice(['low', 'medium', 'high'])} cve={RNG.choice(['CVE-2023-2650', 'CVE-2024-2511', 'CVE-2022-0778'])}"
        )
        lines.append(
            f"[{timestamp()}] osquery-inventory host=simulated-k8s-osquery kernel=5.15.{RNG.randint(0, 30)}"
        )
    log_path = ARTIFACTS_DIR / "telemetry-pod.log"
    log_path.write_text("\n".join(lines), encoding="utf-8")
    return {"entries": len(lines), "log": str(log_path)}


def simulate_wazuh() -> dict:
    lines = []
    for idx in range(1, 4):
        lines.append(
            f"{timestamp()} wazuh-manager alert_id=sim-k8s-{idx} level={RNG.randint(3, 9)} message=Integrity check"
        )
    for path in ["/etc/passwd", "/etc/ssh/sshd_config", "/var/log/auth.log"]:
        lines.append(
            f"{timestamp()} wazuh-fim path={path} action={RNG.choice(['modified', 'added', 'accessed'])}"
        )
    log_path = ARTIFACTS_DIR / "wazuh-pod.log"
    log_path.write_text("\n".join(lines), encoding="utf-8")
    return {"entries": len(lines), "log": str(log_path)}


def main() -> None:
    ensure_dir(ARTIFACTS_DIR)
    resources = collect_manifests()
    (ARTIFACTS_DIR / "cluster-resources.json").write_text(
        json.dumps(resources, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    overview_lines = [
        "Kubernetes manifests summary (симуляция)",
        f"Timestamp: {timestamp()}",
        "",
    ]
    for resource in resources:
        overview_lines.append(
            f"- {resource.get('kind', 'Unknown')} / {resource.get('name', 'noname')} (ns={resource.get('namespace', 'default')})"
            f" <- {resource.get('source')}"
        )
        for image in resource.get("images", []):
            overview_lines.append(f"    image: {image}")

    (ARTIFACTS_DIR / "cluster-overview.txt").write_text("\n".join(overview_lines), encoding="utf-8")

    summary = {
        "generated_at": timestamp(),
        "resources": len(resources),
        "openscap": simulate_openscap(),
        "telemetry": simulate_telemetry(),
        "wazuh": simulate_wazuh(),
    }
    summary_path = ARTIFACTS_DIR / "simulation-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Симуляция kind-кластера завершена. Сводка:", summary_path)


if __name__ == "__main__":
    main()
