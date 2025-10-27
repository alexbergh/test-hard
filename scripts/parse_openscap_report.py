#!/usr/bin/env python3
import sys
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

DEFAULT_RESULTS_ROOT = Path(os.environ.get("HARDENING_RESULTS_DIR", "/var/lib/hardening/results"))
DEFAULT_RESULTS_DIR = DEFAULT_RESULTS_ROOT / "openscap"


def _latest_report(results_dir: Path) -> Optional[Path]:
    """Return the most recent ARF report in ``results_dir`` if it exists."""
    if not results_dir.is_dir():
        return None

    try:
        reports = sorted(
            results_dir.glob("*.arf"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        return None

    return reports[0] if reports else None


# Очень упрощённый разбор ARF: считаем количество pass/fail/other
def main(argv: list[str]) -> int:
    if argv:
        arf_path = Path(argv[0])
    else:
        arf_path = _latest_report(DEFAULT_RESULTS_DIR)
        if arf_path is None:
            print(
                "Usage: parse_openscap_report.py <report.arf>\n"
                "Either provide a path explicitly or place reports under "
                f"{DEFAULT_RESULTS_DIR}",
                file=sys.stderr,
            )
            return 1

    if not arf_path.exists():
        print(f"ARF not found: {arf_path}", file=sys.stderr)
        return 1

    tree = ET.parse(arf_path)
    root = tree.getroot()

    ns = {"arf": "http://scap.nist.gov/schema/arf/1.1",
          "xccdf": "http://checklists.nist.gov/xccdf/1.2"}

    results = root.findall(".//xccdf:rule-result", ns)
    counts = {"pass":0, "fail":0, "error":0, "unknown":0, "notchecked":0, "notselected":0, "informational":0, "fixed":0}

    for r in results:
        res = r.findtext("xccdf:result", default="unknown", namespaces=ns).lower()
        counts[res] = counts.get(res, 0) + 1

    hostname = os.uname().nodename
    for k, v in counts.items():
        print(f'openscap_{k}_count{{host="{hostname}"}} {v}')

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
