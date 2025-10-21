#!/usr/bin/env python3
"""Offline симуляция docker-окружения для генерации отчётов и логов."""
from __future__ import annotations

import argparse
import json
import random
import textwrap
from datetime import datetime, timezone
from dataclasses import asdict
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
FSTEC_CONTENT_DIR = BASE_DIR / "openscap" / "content" / "fstec"
FALLBACK_OVAL_FILE = BASE_DIR / "openscap" / "content" / "sample-oval.xml"
RNG = random.Random(42)

sys.path.append(str(BASE_DIR.parent / "shared"))
from hardening_metrics import HardeningMetricsVisualizer  # noqa: E402


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_oval_definitions_from_file(path: Path) -> list[dict]:
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {"def": "http://oval.mitre.org/XMLSchema/oval-definitions-5", "oval": "http://oval.mitre.org/XMLSchema/oval-common-5"}
    parsed: list[dict] = []
    for definition in root.findall("def:definitions/def:definition", ns):
        definition_id = definition.get("id", "unknown")
        title = definition.findtext("def:metadata/def:title", default="Без названия", namespaces=ns)
        severity = definition.findtext("def:metadata/oval:advisory/oval:severity", default="", namespaces=ns)
        family = definition.findtext("def:metadata/def:affected/def:family", default="", namespaces=ns)
        platforms = [
            platform.text.strip()
            for platform in definition.findall("def:metadata/def:affected/def:platform", ns)
            if platform.text
        ]
        parsed.append(
            {
                "id": definition_id,
                "title": title,
                "severity": severity,
                "family": family,
                "platforms": platforms,
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
                        "title": definition.get("title", "Без названия"),
                        "severity": definition.get("severity") or "",
                        "family": definition.get("family") or "",
                        "platforms": definition.get("platforms", []),
                        "file": file_entry.get("relative_path", ""),
                    }
                )
    else:
        xml_files = sorted(FSTEC_CONTENT_DIR.rglob("*.xml")) if FSTEC_CONTENT_DIR.exists() else []
        if xml_files:
            for xml_file in xml_files:
                for definition in parse_oval_definitions_from_file(xml_file):
                    definition["file"] = str(xml_file.relative_to(FSTEC_CONTENT_DIR))
                    definitions.append(definition)
    if not definitions and FALLBACK_OVAL_FILE.exists():
        definitions = parse_oval_definitions_from_file(FALLBACK_OVAL_FILE)
        for definition in definitions:
            definition["file"] = FALLBACK_OVAL_FILE.name
    return definitions


def simulate_openscap() -> dict:
    ensure_dir(ARTIFACTS_DIR / "openscap")
    definitions = load_fstec_definitions()

    results = []
    for index, definition in enumerate(definitions, start=1):
        status = "pass" if index % 2 == 1 else "fail"
        platforms = ", ".join(definition.get("platforms", []))
        severity = definition.get("severity") or "n/a"
        family = definition.get("family") or "unknown"
        source = definition.get("file", "fstec/manifest")
        details = (
            f"Платформа: {platforms or 'не указано'}, семья: {family}, источник: {source}, критичность: {severity}"
            if status == "pass"
            else f"Нарушение политики для {platforms or 'платформы по умолчанию'} (severity={severity})"
        )
        results.append({
            "id": definition["id"],
            "title": definition["title"],
            "status": status,
            "details": details,
        })

    summary = {
        "generated_at": timestamp(),
        "scanner": "openscap-simulator",
        "definitions_evaluated": len(results),
        "passed": sum(1 for item in results if item["status"] == "pass"),
        "failed": sum(1 for item in results if item["status"] == "fail"),
        "results": results,
    }

    report_path = ARTIFACTS_DIR / "openscap" / "scan-report.json"
    report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    human_report = ARTIFACTS_DIR / "openscap" / "scan-report.txt"
    human_report.write_text(
        textwrap.dedent(
            f"""
            Отчёт OpenSCAP (симуляция)
            -------------------------
            Время генерации: {summary['generated_at']}

            Проверено определений: {summary['definitions_evaluated']}
            Успешно: {summary['passed']}
            Провалено: {summary['failed']}

            Детали:
            """
        ).strip()
        + "\n\n"
        + "\n".join(
            f"- [{item['status'].upper()}] {item['title']} ({item['id']}): {item['details']}"
            for item in results
        ),
        encoding="utf-8",
    )

    return summary


def simulate_telemetry() -> dict:
    ensure_dir(ARTIFACTS_DIR / "telemetry")
    events = []
    for sequence in range(1, 6):
        events.append(
            {
                "type": "vulnerability",
                "host": "simulated-osquery",
                "sequence": sequence,
                "package": "openssl",
                "version": f"1.1.{RNG.randint(0, 9)}",
                "severity": RNG.choice(["Low", "Medium", "High"]),
                "cve": RNG.choice(["CVE-2023-2650", "CVE-2024-2511", "CVE-2022-0778"]),
                "collected_at": timestamp(),
            }
        )
        events.append(
            {
                "type": "inventory",
                "host": "simulated-osquery",
                "sequence": sequence,
                "os": RNG.choice(["ubuntu", "centos", "debian"]),
                "kernel_version": f"5.15.{RNG.randint(0, 30)}",
                "collected_at": timestamp(),
            }
        )

    events_path = ARTIFACTS_DIR / "telemetry" / "osquery-events.jsonl"
    with events_path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    syslog_messages = []
    for event in events:
        if event["type"] != "inventory":
            continue
        syslog_messages.append(
            f"<134>{timestamp()} osquery-simulator {event['host']} hardening sequence={event['sequence']}"
        )

    (ARTIFACTS_DIR / "telemetry" / "syslog.log").write_text("\n".join(syslog_messages), encoding="utf-8")

    metrics = HardeningMetricsVisualizer(ARTIFACTS_DIR / "telemetry").build(events)

    return {
        "generated_at": timestamp(),
        "events": len(events),
        "syslog_messages": len(syslog_messages),
        "artifacts": [
            str(events_path),
            str(ARTIFACTS_DIR / "telemetry" / "syslog.log"),
            str(ARTIFACTS_DIR / "telemetry" / "hardening-dashboard.md"),
            str(ARTIFACTS_DIR / "telemetry" / "grafana-dashboard.json"),
            str(ARTIFACTS_DIR / "telemetry" / "kuma-payload.json"),
            str(ARTIFACTS_DIR / "telemetry" / "collector.log"),
        ],
        "metrics": asdict(metrics),
    }


def simulate_wazuh() -> dict:
    ensure_dir(ARTIFACTS_DIR / "wazuh")
    alerts = []
    for idx in range(1, 4):
        alerts.append(
            {
                "id": f"simulated-alert-{idx}",
                "rule": "550",
                "level": RNG.randint(3, 10),
                "agent": "simulated-wazuh-agent",
                "description": "Simulated integrity check",
                "timestamp": timestamp(),
            }
        )

    fim_entries = []
    for path in ["/etc/passwd", "/etc/ssh/sshd_config", "/var/log/auth.log"]:
        fim_entries.append(
            {
                "path": path,
                "event": RNG.choice(["modified", "added", "accessed"]),
                "timestamp": timestamp(),
            }
        )

    alerts_path = ARTIFACTS_DIR / "wazuh" / "alerts.json"
    alerts_path.write_text(json.dumps(alerts, indent=2, ensure_ascii=False), encoding="utf-8")
    fim_path = ARTIFACTS_DIR / "wazuh" / "fim-events.jsonl"
    with fim_path.open("w", encoding="utf-8") as handle:
        for entry in fim_entries:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return {
        "generated_at": timestamp(),
        "alerts": len(alerts),
        "fim_events": len(fim_entries),
        "artifacts": [str(alerts_path), str(fim_path)],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Симуляция docker-профилей")
    parser.add_argument(
        "profile",
        choices=["openscap", "telemetry", "wazuh", "all"],
        help="Профиль docker-compose или all",
    )
    args = parser.parse_args()

    summaries = {}
    if args.profile in {"openscap", "all"}:
        summaries["openscap"] = simulate_openscap()
    if args.profile in {"telemetry", "all"}:
        summaries["telemetry"] = simulate_telemetry()
    if args.profile in {"wazuh", "all"}:
        summaries["wazuh"] = simulate_wazuh()

    summary_path = ARTIFACTS_DIR / "simulation-summary.json"
    ensure_dir(ARTIFACTS_DIR)
    summary_path.write_text(json.dumps(summaries, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Симуляция завершена. Сводка сохранена в", summary_path)


if __name__ == "__main__":
    main()
