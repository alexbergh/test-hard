#!/usr/bin/env python3
import json
import logging
import sys
from pathlib import Path

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.WARNING, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def parse_lynis_report(report_path: str) -> None:
    """Parse Lynis JSON report and output Prometheus metrics."""
    path = Path(report_path)

    if not path.exists():
        logger.error("Report file not found: %s", path)
        sys.exit(1)

    try:
        with path.open("r", encoding="utf-8") as f:
            report = json.load(f)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse JSON from %s: %s", path, exc)
        sys.exit(1)
    except Exception as exc:
        logger.error("Error reading file %s: %s", path, exc)
        sys.exit(1)

    hostname = report.get("general", {}).get("hostname") or "unknown"
    metrics = {
        "lynis_warnings_count": len(report.get("warnings", []) or []),
        "lynis_suggestions_count": len(report.get("suggestions", []) or []),
        "lynis_tests_count": len(report.get("tests", []) or []),
        "lynis_plugins_count": len(report.get("plugins", []) or []),
    }
    metrics["lynis_tests_performed"] = metrics["lynis_tests_count"]

    # Lynis Score (hardening index)
    if "general" in report and "hardening_index" in report["general"]:
        try:
            metrics["lynis_score"] = int(report["general"]["hardening_index"])
        except (ValueError, TypeError) as exc:
            logger.warning("Invalid hardening_index value: %s", exc)

    logger.info("Parsed Lynis report from %s: %d metrics", path, len(metrics))

    # Вывод метрик в формате Prometheus
        for key, value in metrics.items():
            print(f'{key}{{host="{hostname}"}} {value}')
            # Also print prefixed metric names expected by dashboards
            print(f'security_scanners_lynis_{key[len("lynis_"):]}{{host="{hostname}"}} {value}')

        # Lynis score separately
        if "lynis_score" in metrics:
            print(f'security_scanners_lynis_score{{host="{hostname}"}} {metrics["lynis_score"]}')


if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Usage: parse_lynis_report.py <path_to_lynis_json_report>")
        print("Usage: parse_lynis_report.py <path_to_lynis_json_report>", file=sys.stderr)
        sys.exit(1)
    parse_lynis_report(sys.argv[1])
