#!/usr/bin/env python3
"""Offline симуляция docker-окружения для генерации отчётов и логов."""
from __future__ import annotations

import argparse
import json
import random
import textwrap
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
OVAL_FILE = BASE_DIR / "openscap" / "content" / "sample-oval.xml"
RNG = random.Random(42)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def simulate_openscap() -> dict:
    ensure_dir(ARTIFACTS_DIR / "openscap")
    tree = ET.parse(OVAL_FILE)
    root = tree.getroot()
    ns = {"def": "http://oval.mitre.org/XMLSchema/oval-definitions-5", "oval": "http://oval.mitre.org/XMLSchema/oval-common-5"}

    definitions = []
    for definition in root.findall("def:definitions/def:definition", ns):
        definition_id = definition.get("id", "unknown")
        title = definition.findtext("def:metadata/def:title", default="Без названия", namespaces=ns)
        description = definition.findtext("def:metadata/def:description", default="", namespaces=ns)
        definitions.append({
            "id": definition_id,
            "title": title,
            "description": description,
        })

    results = []
    for index, definition in enumerate(definitions, start=1):
        status = "pass" if index % 2 == 1 else "fail"
        details = "Файл найден" if status == "pass" else "Файл отсутствует"
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

    return {
        "generated_at": timestamp(),
        "events": len(events),
        "syslog_messages": len(syslog_messages),
        "artifacts": [str(events_path), str(ARTIFACTS_DIR / "telemetry" / "syslog.log")],
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
