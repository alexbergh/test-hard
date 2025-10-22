"""Shared утилиты для построения метрик и визуализаций hardening."""
from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from time_utils import TimeSequencer


@dataclass
class SeverityBreakdown:
    severity: str
    count: int
    percentage: float


def _ascii_bar(value: int, max_value: int, width: int = 20) -> str:
    if max_value <= 0:
        return ""
    filled = max(1, math.ceil(value / max_value * width)) if value else 0
    return "█" * filled


def _normalize_severity(raw: str | None) -> str:
    if not raw:
        return "unknown"
    normalized = raw.strip().lower()
    mapping = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "moderate": "medium",
        "low": "low",
        "info": "informational",
        "informational": "informational",
    }
    return mapping.get(normalized, normalized)


def _unique_hosts(events: Iterable[dict]) -> set[str]:
    hosts: set[str] = set()
    for event in events:
        host = event.get("host") or event.get("hostname")
        if host:
            hosts.add(str(host))
    return hosts


@dataclass
class HardeningMetrics:
    generated_at: str
    vulnerability_total: int
    inventory_total: int
    unique_hosts: int
    severity: list[SeverityBreakdown]
    top_cves: list[tuple[str, int]]
    top_packages: list[tuple[str, int]]


class HardeningMetricsVisualizer:
    """Строит артефакты визуализации и полезные payload-ы."""

    def __init__(self, output_dir: Path, time_sequencer: Optional[TimeSequencer] = None):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._time = time_sequencer or TimeSequencer()

    def build(self, events: list[dict]) -> HardeningMetrics:
        vulnerability_events = [e for e in events if e.get("type") == "vulnerability"]
        inventory_events = [e for e in events if e.get("type") == "inventory"]

        severity_counter = Counter(_normalize_severity(e.get("severity")) for e in vulnerability_events)
        package_counter = Counter(e.get("package", "unknown") for e in vulnerability_events)
        cve_counter = Counter(e.get("cve", "unknown") for e in vulnerability_events)

        total_vulnerabilities = sum(severity_counter.values())
        severity_breakdown: list[SeverityBreakdown] = []
        for severity, count in sorted(severity_counter.items(), key=lambda item: (-item[1], item[0])):
            percentage = (count / total_vulnerabilities * 100) if total_vulnerabilities else 0
            severity_breakdown.append(SeverityBreakdown(severity=severity, count=count, percentage=percentage))

        generated_at_dt = self._time.next_datetime()
        metrics = HardeningMetrics(
            generated_at=generated_at_dt.isoformat(),
            vulnerability_total=total_vulnerabilities,
            inventory_total=len(inventory_events),
            unique_hosts=len(_unique_hosts(events)),
            severity=severity_breakdown,
            top_cves=cve_counter.most_common(5),
            top_packages=package_counter.most_common(5),
        )

        self._write_dashboard(metrics)
        self._write_grafana_dashboard(metrics)
        self._write_kuma_payload(metrics, vulnerability_events, inventory_events, generated_at_dt)
        self._write_collector_log(metrics, vulnerability_events, inventory_events)
        return metrics

    def _write_dashboard(self, metrics: HardeningMetrics) -> None:
        lines: list[str] = [
            "# Итоговая панель по метрикам hardening",
            "",
            f"Дата генерации: {metrics.generated_at}",
            f"Всего уязвимостей: {metrics.vulnerability_total}",
            f"Инвентарных записей: {metrics.inventory_total}",
            f"Уникальных хостов: {metrics.unique_hosts}",
            "",
            "## Распределение по критичности",
            "",
            "| Критичность | Кол-во | Доля | График |",
            "|-------------|--------|------|--------|",
        ]
        max_count = max((item.count for item in metrics.severity), default=0)
        for item in metrics.severity:
            bar = _ascii_bar(item.count, max_count)
            lines.append(
                f"| {item.severity.capitalize()} | {item.count} | {item.percentage:5.1f}% | {bar or '-'} |"
            )

        def _format_top(title: str, entries: list[tuple[str, int]]) -> None:
            lines.append("")
            lines.append(f"## {title}")
            lines.append("")
            if not entries:
                lines.append("Нет данных")
                return
            lines.append("| Значение | Кол-во |")
            lines.append("|----------|--------|")
            for value, count in entries:
                lines.append(f"| {value} | {count} |")

        _format_top("Топ CVE", metrics.top_cves)
        _format_top("Чаще всего встречающиеся пакеты", metrics.top_packages)

        dashboard_path = self.output_dir / "hardening-dashboard.md"
        dashboard_path.write_text("\n".join(lines), encoding="utf-8")

    def _write_grafana_dashboard(self, metrics: HardeningMetrics) -> None:
        panels = []
        if metrics.severity:
            panels.append(
                {
                    "type": "bargauge",
                    "title": "Vulnerability severity",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                    "targets": [
                        {
                            "refId": "A",
                            "datasource": {"type": "influxdb", "uid": "osquery-influx"},
                            "query": "from(bucket: 'osquery') |> range(start: -6h) |> filter(fn: (r) => r._measurement == 'hardening_vulnerabilities')",
                        }
                    ],
                    "options": {
                        "reduceOptions": {"fields": "Values", "values": False, "calcs": ["last"]},
                        "orientation": "horizontal",
                    },
                    "fieldConfig": {
                        "defaults": {"mappings": [], "thresholds": {"steps": [{"color": "green"}, {"color": "orange", "value": 5}, {"color": "red", "value": 10}]}},
                        "overrides": [],
                    },
                }
            )
        panels.append(
            {
                "type": "stat",
                "title": "Unique hosts",
                "gridPos": {"h": 6, "w": 6, "x": 12, "y": 0},
                "targets": [
                    {
                        "refId": "B",
                        "datasource": {"type": "influxdb", "uid": "osquery-influx"},
                        "query": "from(bucket: 'osquery') |> range(start: -6h) |> filter(fn: (r) => r._measurement == 'inventory') |> distinct(column: 'host') |> count()",
                    }
                ],
                "options": {"reduceOptions": {"values": False, "calcs": ["last"]}},
            }
        )

        dashboard = {
            "title": "Hardening telemetry overview",
            "timezone": "browser",
            "panels": panels,
            "refresh": "30s",
            "time": {"from": "now-6h", "to": "now"},
        }
        (self.output_dir / "grafana-dashboard.json").write_text(
            json.dumps(dashboard, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _write_kuma_payload(
        self,
        metrics: HardeningMetrics,
        vulnerability_events: list[dict],
        inventory_events: list[dict],
        batch_dt: Optional[datetime] = None,
    ) -> None:
        batch_time = batch_dt or self._time.next_datetime()
        payload = {
            "batch_id": f"kuma-{batch_time.strftime('%Y%m%d%H%M%S')}",
            "generated_at": metrics.generated_at,
            "summary": {
                "vulnerability_total": metrics.vulnerability_total,
                "inventory_total": metrics.inventory_total,
                "unique_hosts": metrics.unique_hosts,
                "severity_breakdown": [
                    {"severity": item.severity, "count": item.count, "share": round(item.percentage, 2)}
                    for item in metrics.severity
                ],
            },
            "events": [],
        }
        for event in vulnerability_events:
            payload["events"].append(
                {
                    "category": "hardening",
                    "kind": "vulnerability",
                    "host": event.get("host"),
                    "package": event.get("package"),
                    "version": event.get("version"),
                    "severity": _normalize_severity(event.get("severity")),
                    "cve": event.get("cve"),
                    "collected_at": event.get("collected_at"),
                }
            )
        for event in inventory_events:
            payload["events"].append(
                {
                    "category": "hardening",
                    "kind": "inventory",
                    "host": event.get("host"),
                    "os": event.get("os"),
                    "kernel": event.get("kernel_version"),
                    "collected_at": event.get("collected_at"),
                }
            )
        (self.output_dir / "kuma-payload.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _write_collector_log(
        self,
        metrics: HardeningMetrics,
        vulnerability_events: list[dict],
        inventory_events: list[dict],
    ) -> None:
        lines = [
            "hardening-collector", "--------------------", f"timestamp={metrics.generated_at}",
            f"vulnerability_total={metrics.vulnerability_total}",
            f"inventory_total={metrics.inventory_total}",
            f"unique_hosts={metrics.unique_hosts}", "severity_breakdown=" + ",".join(
                f"{item.severity}:{item.count}" for item in metrics.severity
            ), ""
        ]
        lines.append("Последние события:")
        for event in vulnerability_events[:5]:
            lines.append(
                f"vulnerability host={event.get('host')} package={event.get('package')} severity={_normalize_severity(event.get('severity'))} cve={event.get('cve')}"
            )
        for event in inventory_events[:5]:
            lines.append(
                f"inventory host={event.get('host')} os={event.get('os')} kernel={event.get('kernel_version')}"
            )
        (self.output_dir / "collector.log").write_text("\n".join(lines), encoding="utf-8")
