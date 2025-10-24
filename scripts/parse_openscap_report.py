#!/usr/bin/env python3
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


NAMESPACE = {
    "arf": "http://scap.nist.gov/schema/arf/1.1",
    "xccdf": "http://checklists.nist.gov/xccdf/1.2",
}


def parse_arf(arf_path: Path) -> None:
    tree = ET.parse(arf_path)
    root = tree.getroot()

    results = root.findall(".//xccdf:rule-result", NAMESPACE)
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

    for result in results:
        status = result.findtext("xccdf:result", default="unknown", namespaces=NAMESPACE).lower()
        counts[status] = counts.get(status, 0) + 1

    hostname = os.uname().nodename
    for key, value in counts.items():
        print(f"openscap_{key}_count{{host=\"{hostname}\"}} {value}")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: parse_openscap_report.py <report.arf>", file=sys.stderr)
        sys.exit(1)

    arf_path = Path(sys.argv[1])
    if not arf_path.exists():
        print(f"ARF not found: {arf_path}", file=sys.stderr)
        sys.exit(1)

    parse_arf(arf_path)


if __name__ == "__main__":
    main()
