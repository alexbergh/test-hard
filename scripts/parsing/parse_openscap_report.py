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

    try:
        # Be liberal in what we accept: ARF/XCCDF vendors sometimes vary in namespaces.
        results = root.findall(".//{*}rule-result")
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
        failed_rules: list[dict[str, str]] = []

        for r in results:
            res = (r.findtext("{*}result", default="unknown") or "unknown").lower()
            counts[res] = counts.get(res, 0) + 1

            if res == "fail":
                rule_id = r.attrib.get("idref") or r.attrib.get("id") or "unknown"
                # SSG ids are long; keep dashboards readable.
                rule_id_short = rule_id.replace("xccdf_org.ssgproject.content_rule_", "")
                severity = r.attrib.get("severity") or "unknown"
                title = rule_id_short.replace("_", " ")[:80]
                failed_rules.append(
                    {
                        "rule_id": rule_id_short,
                        "severity": severity,
                        "title": title,
                    }
                )

        logger.info("Parsed %d rule results from %s", len(results), arf_path)
        stem_parts = arf_path.stem.split("-")
        if len(stem_parts) >= 3 and stem_parts[0] == "openscap":
            hostname = "-".join(stem_parts[1:-1])
        else:
            hostname = os.uname().nodename
        # Prepare metrics lines. Telegraf's inputs.file has name_override = "security_scanners",
        # so we intentionally emit bare metric names (openscap_*) here.
        metrics_lines = []
        for k, v in counts.items():
            metrics_lines.append(f'openscap_{k}_count{{host="{hostname}"}} {v}')

        pass_count = counts.get("pass", 0)
        fail_count = counts.get("fail", 0)
        evaluated = (
            counts.get("pass", 0)
            + counts.get("fail", 0)
            + counts.get("fixed", 0)
            + counts.get("notapplicable", 0)
            + counts.get("informational", 0)
        )
        if evaluated > 0:
            score = int(((evaluated - fail_count) * 100) / evaluated)
        else:
            score = 0

        metrics_lines.append(f'openscap_pass_count{{host="{hostname}"}} {pass_count}')
        metrics_lines.append(f'openscap_fail_count{{host="{hostname}"}} {fail_count}')
        metrics_lines.append(f'openscap_score{{host="{hostname}"}} {score}')

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

        # Write details file with failed rules, so Grafana can show a table.
        try:
            def escape_label_value(val: str) -> str:
                return str(val).replace("\\", "\\\\").replace('"', "")

            details_lines: list[str] = []
            for rule in failed_rules:
                title = escape_label_value(rule["title"])
                rule_id = escape_label_value(rule["rule_id"])
                severity = escape_label_value(rule["severity"])
                details_lines.append(
                    "openscap_rule_result"
                    f"{{host=\"{escape_label_value(hostname)}\",rule_id=\"{rule_id}\",severity=\"{severity}\",title=\"{title}\"}} 0"
                )

            if not details_lines:
                details_lines.append(
                    "openscap_rule_result"
                    f"{{host=\"{escape_label_value(hostname)}\",rule_id=\"none\",severity=\"none\",title=\"No failed rules\"}} 1"
                )

            details_file = arf_path.with_name(f"{arf_path.stem}_details.prom")
            with details_file.open("w", encoding="utf-8") as f:
                f.write("\n".join(details_lines) + "\n")
            logger.info("Wrote details file: %s", details_file)
        except Exception as exc:  # pragma: no cover - best-effort
            logger.warning("Failed to write details file next to ARF: %s", exc)

        return 0
    except Exception as exc:
        logger.error("Error processing ARF results: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
