#!/usr/bin/env python3
"""Сводный отчёт по process-impact.json из тестовых артефактов."""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

sys.path.append(str(Path(__file__).resolve().parents[1] / "shared"))
from time_utils import now_iso  # noqa: E402

_METRIC_FIELDS = (
    "cycle_time_hours",
    "review_rounds",
    "review_comments",
    "incident_frequency",
    "mttr_hours",
    "p95_latency_ms",
    "error_budget_consumed",
)


def _round_value(name: str, value: float) -> float:
    if name in {"review_rounds", "review_comments"}:
        return float(int(round(value)))
    if name in {"cycle_time_hours", "mttr_hours"}:
        return round(value, 2)
    if name in {"p95_latency_ms"}:
        return round(value, 1)
    return round(value, 3)


def _format_value(name: str, value: float) -> str:
    rounded = _round_value(name, value)
    if name in {"review_rounds", "review_comments"}:
        return str(int(rounded))
    return f"{rounded}"


def _load_reports(root: Path) -> List[Dict[str, Any]]:
    reports: List[Dict[str, Any]] = []
    for path in sorted(root.rglob("process-impact.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        data["source"] = str(path)
        reports.append(data)
    return reports


def _average(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def build_summary(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for report in reports:
        family = report.get("family") or report.get("function") or "unknown"
        groups[family].append(report)

    families: Dict[str, Any] = {}
    for family, entries in sorted(groups.items()):
        contexts: List[Dict[str, Any]] = []
        baseline_acc: Dict[str, List[float]] = {field: [] for field in _METRIC_FIELDS}
        observed_acc: Dict[str, List[float]] = {field: [] for field in _METRIC_FIELDS}
        delta_acc: Dict[str, List[float]] = {field: [] for field in _METRIC_FIELDS}
        for entry in entries:
            context = entry.get("context") or "n/a"
            context_payload = {
                "function": entry.get("function"),
                "context": context,
                "baseline": {field: _round_value(field, float(entry["baseline"][field])) for field in _METRIC_FIELDS},
                "observed": {field: _round_value(field, float(entry["observed"][field])) for field in _METRIC_FIELDS},
                "delta": {field: _round_value(field, float(entry["delta"][field])) for field in _METRIC_FIELDS},
                "source": entry.get("source"),
            }
            contexts.append(context_payload)
            for field in _METRIC_FIELDS:
                baseline_acc[field].append(context_payload["baseline"][field])
                observed_acc[field].append(context_payload["observed"][field])
                delta_acc[field].append(context_payload["delta"][field])
        averages = {
            "baseline": {field: _round_value(field, _average(values)) for field, values in baseline_acc.items()},
            "observed": {field: _round_value(field, _average(values)) for field, values in observed_acc.items()},
            "delta": {field: _round_value(field, _average(values)) for field, values in delta_acc.items()},
        }
        families[family] = {"contexts": contexts, "averages": averages}

    return {"generated_at": now_iso(), "families": families}


def render_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# Сводный отчёт по аналитике процессов hardening",
        "",
        f"Сформировано: {summary['generated_at']}",
        "",
    ]
    if not summary["families"]:
        lines.append("Артефакты process-impact.json не найдены.")
        return "\n".join(lines) + "\n"

    for family, payload in summary["families"].items():
        lines.append(f"## Семейство: {family}")
        for context in payload["contexts"]:
            lines.append(
                f"### Контекст: {context['context']} (функция: {context['function']})"
            )
            for field in _METRIC_FIELDS:
                baseline_value = _format_value(field, context["baseline"][field])
                observed_value = _format_value(field, context["observed"][field])
                delta_value = _format_value(field, context["delta"][field])
                if delta_value.startswith("-") or delta_value in {"0.0", "0"}:
                    delta_display = delta_value
                else:
                    delta_display = f"+{delta_value}"
                lines.append(
                    f"- {field}: {baseline_value} → {observed_value} (Δ {delta_display})"
                )
            lines.append("")
        lines.append("**Средние значения по семейству:**")
        for field in _METRIC_FIELDS:
            base = _format_value(field, payload["averages"]["baseline"][field])
            obs = _format_value(field, payload["averages"]["observed"][field])
            delta = _format_value(field, payload["averages"]["delta"][field])
            prefix = "-"
            if not delta.startswith("-") and delta != "0.0":
                delta_display = f"+{delta}"
            else:
                delta_display = delta
            lines.append(f"{prefix} {field}: {base} → {obs} (Δ {delta_display})")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Генерация отчёта по process-impact.json")
    default_root = Path(__file__).resolve().parents[1]
    default_reports_dir = Path(__file__).resolve().parents[2] / "reports"
    parser.add_argument("--search-root", type=Path, default=default_root, help="Где искать process-impact.json")
    parser.add_argument(
        "--output-json",
        type=Path,
        default=default_reports_dir / "process-metrics-summary.json",
        help="Куда сохранить агрегированный JSON",
    )
    parser.add_argument(
        "--output-markdown",
        type=Path,
        default=default_reports_dir / "2025-10-21-process-analytics.md",
        help="Куда сохранить Markdown-отчёт",
    )
    parser.add_argument("--quiet", action="store_true", help="Не выводить диагностические сообщения")
    args = parser.parse_args()

    reports = _load_reports(args.search_root)
    summary = build_summary(reports)

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    markdown = render_markdown(summary)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.write_text(markdown, encoding="utf-8")

    if not args.quiet:
        print(
            f"Сводка по процессным метрикам: найдено {len(reports)} источников,",
            f"Markdown -> {args.output_markdown}",
        )


if __name__ == "__main__":
    main()
