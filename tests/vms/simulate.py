#!/usr/bin/env python3
"""Симуляция подготовки виртуальных машин и сбора hardening-метрик."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

sys.path.append(str(Path(__file__).resolve().parent.parent / "shared"))
from hardening_metrics import HardeningMetricsVisualizer  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_DIR = REPO_ROOT / "hardening-scenarios" / "secaudit" / "profiles"
ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"

VM_DEFINITIONS = [
    {
        "id": "redos-7.3",
        "display_name": "РедОС 7.3",
        "profile": "redos-7.3",
        "hypervisor": "kvm",
        "cpus": 2,
        "memory_mb": 4096,
        "disk_gb": 30,
    },
    {
        "id": "redos-8",
        "display_name": "РедОС 8",
        "profile": "redos-8",
        "hypervisor": "kvm",
        "cpus": 2,
        "memory_mb": 4096,
        "disk_gb": 40,
    },
    {
        "id": "astralinux-1.7",
        "display_name": "Astra Linux 1.7",
        "profile": "astralinux-1.7",
        "hypervisor": "kvm",
        "cpus": 2,
        "memory_mb": 4096,
        "disk_gb": 40,
    },
    {
        "id": "altlinux-8",
        "display_name": "Альт 8",
        "profile": "altlinux-8",
        "hypervisor": "kvm",
        "cpus": 2,
        "memory_mb": 4096,
        "disk_gb": 40,
    },
    {
        "id": "centos-7",
        "display_name": "CentOS 7",
        "profile": "centos-7",
        "hypervisor": "kvm",
        "cpus": 2,
        "memory_mb": 4096,
        "disk_gb": 30,
    },
]

FAILURE_MATRIX = {
    "test": {
        "redos-7.3": ["REDOS73-CTRL-001", "REDOS73-CTRL-004"],
        "redos-8": ["REDOS8-CTRL-003"],
        "astralinux-1.7": ["ASTRA17-CTRL-002"],
        "altlinux-8": ["ALT8-CTRL-004", "ALT8-CTRL-005"],
        "centos-7": ["CENTOS7-CTRL-005"],
    },
    "prod": {
        "redos-7.3": ["REDOS73-CTRL-004"],
        "redos-8": ["REDOS8-CTRL-003"],
        "astralinux-1.7": [],
        "altlinux-8": ["ALT8-CTRL-005"],
        "centos-7": [],
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_profile(profile_id: str) -> dict:
    path = SCENARIO_DIR / f"{profile_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Не найден профиль {profile_id}: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _host_name(vm_id: str, environment: str) -> str:
    normalized = vm_id.replace(".", "").replace("-", "")
    return f"vm-{normalized}-{environment}"


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_lines(path: Path, lines: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _simulate_environment(environment: str) -> None:
    env_dir = ARTIFACTS_DIR / environment
    env_dir.mkdir(parents=True, exist_ok=True)

    summary = []
    vulnerability_events = []
    inventory_events = []

    for vm in VM_DEFINITIONS:
        profile = _load_profile(vm["profile"])
        failures = set(FAILURE_MATRIX[environment].get(vm["id"], []))
        host = _host_name(vm["id"], environment)
        controls = profile.get("controls", [])
        control_results = []
        for control in controls:
            status = "passed" if control["id"] not in failures else "failed"
            control_results.append({
                "id": control["id"],
                "title": control.get("title"),
                "severity": control.get("severity", "medium"),
                "status": status,
                "tags": control.get("tags", []),
                "reference": control.get("secaudit_reference"),
            })
            if status == "failed":
                vulnerability_events.append(
                    {
                        "type": "vulnerability",
                        "host": host,
                        "profile": profile["metadata"]["id"],
                        "control_id": control["id"],
                        "title": control.get("title"),
                        "severity": control.get("severity", "medium"),
                        "environment": environment,
                        "os": vm["display_name"],
                        "category": control.get("category"),
                        "tags": control.get("tags", []),
                    }
                )
        passed = sum(1 for item in control_results if item["status"] == "passed")
        compliance = round(passed / max(len(control_results), 1) * 100, 1)
        vm_dir = env_dir / vm["id"]
        _write_json(
            vm_dir / "build-plan.json",
            {
                "generated_at": _now(),
                "environment": environment,
                "vm": vm,
                "profile": profile["metadata"],
                "packer_template": "tests/vms/packer/linux.pkr.hcl",
                "ansible_playbook": "tests/vms/ansible/playbooks/hardening.yml",
            },
        )
        _write_json(
            vm_dir / "compliance-report.json",
            {
                "host": host,
                "environment": environment,
                "profile": profile["metadata"],
                "compliance_percent": compliance,
                "controls": control_results,
            },
        )
        _write_lines(
            vm_dir / "build-log.txt",
            [
                f"[{_now()}] packer simulate build for {vm['id']} ({environment})",
                "[00:00] downloading iso placeholder",
                "[00:05] applying kickstart/preseed",
                "[00:10] running ansible hardening",
                f"[00:15] compliance summary: {compliance}% ({passed}/{len(control_results)})",
                "[00:16] exporting image artifact",
            ],
        )
        inventory_events.append(
            {
                "type": "inventory",
                "host": host,
                "environment": environment,
                "os": vm["display_name"],
                "profile": profile["metadata"]["id"],
                "controls": len(controls),
                "compliance": compliance,
                "hypervisor": vm["hypervisor"],
                "memory_mb": vm["memory_mb"],
                "disk_gb": vm["disk_gb"],
            }
        )
        summary.append(
            {
                "vm_id": vm["id"],
                "host": host,
                "environment": environment,
                "compliance": compliance,
                "failed_controls": sorted(failures),
            }
        )

    _write_json(
        env_dir / "simulation-summary.json",
        {
            "environment": environment,
            "generated_at": _now(),
            "systems": summary,
        },
    )

    telemetry_dir = env_dir / "telemetry"
    metrics = HardeningMetricsVisualizer(telemetry_dir).build(vulnerability_events + inventory_events)

    events_path = telemetry_dir / "events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with events_path.open("w", encoding="utf-8") as handle:
        for event in vulnerability_events:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    inventory_path = telemetry_dir / "inventory.jsonl"
    with inventory_path.open("w", encoding="utf-8") as handle:
        for item in inventory_events:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")

    _write_json(
        telemetry_dir / "metrics.json",
        {
            "generated_at": metrics.generated_at,
            "vulnerability_total": metrics.vulnerability_total,
            "inventory_total": metrics.inventory_total,
            "unique_hosts": metrics.unique_hosts,
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Симуляция подготовки hardening ВМ")
    parser.add_argument(
        "environment",
        nargs="?",
        default="all",
        choices=["all", "test", "prod"],
        help="Какие окружения симулировать",
    )
    args = parser.parse_args()

    environments = ["test", "prod"] if args.environment == "all" else [args.environment]
    for env in environments:
        _simulate_environment(env)


if __name__ == "__main__":
    main()
