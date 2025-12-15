#!/usr/bin/env python3
import logging
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.WARNING, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

DEFAULT_RESULTS_ROOT = Path(os.environ.get("HARDENING_RESULTS_DIR", "/var/lib/hardening/results"))
DEFAULT_RESULTS_DIR = DEFAULT_RESULTS_ROOT / "openscap"


def _latest_report(results_dir: Path) -> Optional[Path]:
    """Return the most recent ARF report in ``results_dir`` if it exists."""
    if not results_dir.is_dir():
        logger.debug("Results directory does not exist: %s", results_dir)
        return None

    latest_report = None
    latest_key = None

    try:
        for idx, report in enumerate(results_dir.glob("*.arf")):
            stat = report.stat()
            key = (stat.st_mtime_ns, stat.st_ctime_ns, idx)

            if latest_key is None or key > latest_key:
                latest_report = report
                latest_key = key
    except OSError as exc:
        logger.error("Error listing reports in %s: %s", results_dir, exc)
        return None

    if latest_report:
        logger.info("Found latest report: %s", latest_report)
    return latest_report


# Очень упрощённый разбор ARF: считаем количество pass/fail/other
def main(argv: list[str]) -> int:  # noqa: C901
    if argv:
        arf_path = Path(argv[0])
        logger.info("Using provided ARF path: %s", arf_path)
    else:
        arf_path = _latest_report(DEFAULT_RESULTS_DIR)
        if arf_path is None:
            logger.error(
                "No ARF report found. Provide path or place reports under %s",
                DEFAULT_RESULTS_DIR,
            )
            print(
                "Usage: parse_openscap_report.py <report.arf>\n"
                "Either provide a path explicitly or place reports under "
                f"{DEFAULT_RESULTS_DIR}",
                file=sys.stderr,
            )
            return 1

    if not arf_path.exists():
        logger.error("ARF not found: %s", arf_path)
        print(f"ARF not found: {arf_path}", file=sys.stderr)
        return 1

    try:
        tree = ET.parse(arf_path)
        root = tree.getroot()
    except ET.ParseError as exc:
        logger.error("Failed to parse XML from %s: %s", arf_path, exc)
        print(f"XML parse error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        logger.error("Error reading file %s: %s", arf_path, exc)
        return 1

    ns = {
        "arf": "http://scap.nist.gov/schema/arf/1.1",
        "xccdf": "http://checklists.nist.gov/xccdf/1.2",
    }

    try:
        results = root.findall(".//xccdf:rule-result", ns)
        counts = {
            "pass": 0,
            "fail": 0,
            "error": 0,
            "unknown": 0,
            "notchecked": 0,
            "notselected": 0,
            "informational": 0,
            "fixed": 0,
        }

        for r in results:
            res = r.findtext("xccdf:result", default="unknown", namespaces=ns).lower()
            counts[res] = counts.get(res, 0) + 1

        logger.info("Parsed %d rule results from %s", len(results), arf_path)
        hostname = os.uname().nodename
        # Prepare metrics lines for both raw and aggregated naming used by dashboards
        metrics_lines = []
        for k, v in counts.items():
            metrics_lines.append(f'openscap_{k}_count{{host="{hostname}"}} {v}')

        # Aggregated names expected by dashboards
        pass_count = counts.get("pass", 0)
        fail_count = counts.get("fail", 0)
        # Compliance score: percentage of passed rules among pass+fail
        denom = pass_count + fail_count
        score = int((pass_count * 100) / denom) if denom > 0 else 0

        metrics_lines.append(f'security_scanners_openscap_pass_count{{host="{hostname}"}} {pass_count}')
        metrics_lines.append(f'security_scanners_openscap_fail_count{{host="{hostname}"}} {fail_count}')
        metrics_lines.append(f'security_scanners_openscap_score{{host="{hostname}"}} {score}')

        # Print metrics to stdout for backward compatibility
        for ln in metrics_lines:
            print(ln)

        # Also write a Prometheus metrics file alongside the ARF so Telegraf can pick it up
        try:
            metrics_file = arf_path.with_name(f"{arf_path.stem}_metrics.prom")
            with metrics_file.open("w", encoding="utf-8") as f:
                f.write("\n".join(metrics_lines) + "\n")
            logger.info("Wrote metrics file: %s", metrics_file)
        except Exception as exc:  # pragma: no cover - best-effort
            logger.warning("Failed to write metrics file next to ARF: %s", exc)

        return 0
    except Exception as exc:
        logger.error("Error processing ARF results: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
