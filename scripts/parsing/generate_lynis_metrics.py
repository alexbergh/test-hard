#!/usr/bin/env python3
"""Generate a tiny Prometheus metrics file from a Lynis text report.

This is a pragmatic helper that extracts a few useful counts so Telegraf
can ingest them via the file input plugin.
"""
import re
import sys
from pathlib import Path


def main(path: str) -> int:
    p = Path(path)
    if not p.exists():
        print(f"Report not found: {p}", file=sys.stderr)
        return 1

    text = p.read_text(errors="ignore")
    stem_parts = p.stem.split("-")
    if len(stem_parts) >= 3 and stem_parts[0] == "lynis":
        hostname = "-".join(stem_parts[1:-1])
    else:
        hostname = p.stem

    failed = 1 if re.search(r"(?i)fatal error|error", text) else 0
    warnings = len(re.findall(r"(?i)\bwarning\b", text))
    suggestions = len(re.findall(r"(?i)\bsuggestion\b", text))

    # Try to extract hardening index if present (common formats include: 'Hardening index : [75]')
    match = re.search(r"(?i)hardening index\s*[: ]+\[?([0-9]+)\]?", text)
    score = int(match.group(1)) if match else None

    # Telegraf reads these files with name_override="security_scanners",
    # so it will export them as security_scanners_<metric_name>. Do NOT prefix here.
    metrics: list[str] = []
    metrics.append(f"lynis_failed{{host=\"{hostname}\"}} {failed}")
    metrics.append(f"lynis_warnings{{host=\"{hostname}\"}} {warnings}")
    metrics.append(f"lynis_suggestions{{host=\"{hostname}\"}} {suggestions}")
    if score is not None:
        metrics.append(f"lynis_score{{host=\"{hostname}\"}} {score}")

    out_file = p.with_name(f"{p.stem}_metrics.prom")
    out_file.write_text("\n".join(metrics) + "\n")
    print(f"Wrote Lynis metrics: {out_file}")

    # Write details file (warnings/suggestions with test IDs) for Grafana tables.
    # Expected by dashboard via Telegraf: security_scanners_lynis_test_result{host,type,test_id,description}
    def esc(val: str) -> str:
        return str(val).replace("\\", "\\\\").replace('"', "\\\"")

    details: list[str] = []
    # Lynis commonly includes [test:XYZ-1234] markers.
    test_id_re = re.compile(r"\[test:([A-Z]+-[0-9]+)\]")

    for line in text.splitlines():
        m = test_id_re.search(line)
        test_id = m.group(1) if m else "unknown"
        if re.search(r"(?i)^\s*warning:", line):
            issue_type = "warning"
            description = re.sub(r"(?i)^\s*warning:\s*", "", line)
        elif re.search(r"(?i)^\s*suggestion:", line):
            issue_type = "suggestion"
            description = re.sub(r"(?i)^\s*suggestion:\s*", "", line)
        else:
            continue

        # Remove test marker and trim to keep label sizes reasonable.
        description = test_id_re.sub("", description).strip()
        description = re.sub(r"\s+", " ", description)[:120]
        details.append(
            "lynis_test_result"
            f"{{host=\"{esc(hostname)}\",type=\"{esc(issue_type)}\",test_id=\"{esc(test_id)}\",description=\"{esc(description)}\"}} 1"
        )

    if not details:
        details.append(
            "lynis_test_result"
            f"{{host=\"{esc(hostname)}\",type=\"info\",test_id=\"none\",description=\"No issues found\"}} 1"
        )

    details_file = p.with_name(f"{p.stem}_details.prom")
    details_file.write_text("\n".join(details) + "\n")
    print(f"Wrote Lynis details: {details_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
