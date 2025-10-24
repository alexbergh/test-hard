#!/usr/bin/env python3
import sys, xml.etree.ElementTree as ET, os

# Очень упрощённый разбор ARF: считаем количество pass/fail/other
def main(arf_path):
    if not os.path.exists(arf_path):
        print(f"ARF not found: {arf_path}", file=sys.stderr)
        sys.exit(1)

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

if __name__ == "__main__":
    if len(sys.argv) < 1:
        print("Usage: parse_openscap_report.py <report.arf>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
