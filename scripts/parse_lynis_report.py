#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def parse_lynis_report(report_path: Path) -> None:
    with report_path.open("r", encoding="utf-8") as handle:
        report = json.load(handle)

    general = report.get("general", {})
    hostname = general.get("hostname", "unknown")

    metrics = {}
    hardening_index = general.get("hardening_index")
    if hardening_index is not None:
        metrics["lynis_score"] = int(hardening_index)

    warnings = report.get("warnings", [])
    metrics["lynis_warnings_count"] = len(warnings)

    suggestions = report.get("suggestions", [])
    metrics["lynis_suggestions_count"] = len(suggestions)

    for key, value in metrics.items():
        print(f"{key}{{host=\"{hostname}\"}} {value}")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: parse_lynis_report.py <path_to_lynis_json_report>", file=sys.stderr)
        sys.exit(1)

    report_path = Path(sys.argv[1])
    if not report_path.exists():
        print(f"Report file {report_path} does not exist", file=sys.stderr)
        sys.exit(1)

    parse_lynis_report(report_path)


if __name__ == "__main__":
    main()
