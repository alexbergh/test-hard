#!/usr/bin/env python3
"""Parse Atomic Red Team execution results into Prometheus metrics."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable

STATUS_TO_VALUE = {"passed": 0, "failed": 1, "skipped": 2, "error": 3, "unknown": 4}


def main(path: str) -> None:
    result_path = Path(path)
    if not result_path.exists():
        print(f"Result file {result_path} not found; skipping", file=sys.stderr)
        return

    with result_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    host = data.get("host", os.uname().nodename)

    if "scenarios" in data:
        emit_modern_format(host, data)
    elif "tests" in data:
        emit_legacy_format(host, data)
    else:
        raise ValueError("Unsupported Atomic Red Team result schema")


def emit_modern_format(host: str, data: Dict[str, Any]) -> None:
    scenarios: Iterable[Dict[str, Any]] = data.get("scenarios", [])
    for scenario in scenarios:
        scenario_id = scenario.get("id") or scenario.get("technique") or "unknown"
        technique = scenario.get("technique")
        status = scenario.get("status", "unknown")
        tests = scenario.get("tests", [])
        for test in tests:
            labels = {
                "host": host,
                "scenario": scenario_id,
                "technique": technique or test.get("technique"),
                "test": f"{technique or 'unknown'}-{test.get('number', 'na')}",
                "status": test.get("status", "unknown"),
            }
            executor = test.get("executor")
            if executor:
                labels["executor"] = executor
            platforms = test.get("supported_platforms")
            if platforms:
                labels["platforms"] = ",".join(platforms)
            value = STATUS_TO_VALUE.get(test.get("status", "unknown"), STATUS_TO_VALUE["unknown"])
            print(render_metric("art_test_result", labels, value))

        if status:
            scenario_value = STATUS_TO_VALUE.get(status, STATUS_TO_VALUE["unknown"])
            print(
                render_metric(
                    "art_scenario_status",
                    {
                        "host": host,
                        "scenario": scenario_id,
                        "technique": technique or "unknown",
                        "status": status,
                    },
                    scenario_value,
                )
            )

    summary = data.get("summary", {})
    for key, value in summary.items():
        if isinstance(value, (int, float)):
            print(
                render_metric(
                    "art_summary_total",
                    {"host": host, "bucket": key},
                    value,
                )
            )


def emit_legacy_format(host: str, data: Dict[str, Any]) -> None:
    for test in data.get("tests", []):
        test_id = test.get("id", "unknown")
        passed = bool(test.get("passed", False))
        value = 0 if passed else 1
        print(
            render_metric(
                "art_test_result",
                {"host": host, "scenario": "legacy", "technique": test_id, "test": test_id, "status": "passed" if passed else "failed"},
                value,
            )
        )


def render_metric(name: str, labels: Dict[str, Any], value: Any) -> str:
    encoded = ",".join(
        f"{key}=\"{str(val).replace('\\\\', '\\\\').replace('\"', '\\\"')}\""
        for key, val in sorted(labels.items())
    )
    return f"{name}{{{encoded}}} {value}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: parse_atomic_red_team_result.py <result.json>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
