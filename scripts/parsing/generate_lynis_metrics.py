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
    hostname = p.stem

    failed = 1 if re.search(r"(?i)fatal error|error", text) else 0
    warnings = len(re.findall(r"(?i)warning", text))
    suggestions = len(re.findall(r"(?i)suggestion", text))

    # Try to extract hardening index if present
    match = re.search(r"(?i)hardening index[: ]+([0-9]+)", text)
    score = int(match.group(1)) if match else None

    metrics = []
    metrics.append(f"lynis_failed{{host=\"{hostname}\"}} {failed}")
    metrics.append(f"lynis_warnings_count{{host=\"{hostname}\"}} {warnings}")
    metrics.append(f"lynis_suggestions_count{{host=\"{hostname}\"}} {suggestions}")
    if score is not None:
        metrics.append(f"lynis_score{{host=\"{hostname}\"}} {score}")

    # Also emit dashboard-friendly metric names with a security_scanners_ prefix
    metrics.append(f"security_scanners_lynis_failed{{host=\"{hostname}\"}} {failed}")
    metrics.append(f"security_scanners_lynis_warnings{{host=\"{hostname}\"}} {warnings}")
    metrics.append(f"security_scanners_lynis_suggestions{{host=\"{hostname}\"}} {suggestions}")
    if score is not None:
        metrics.append(f"security_scanners_lynis_score{{host=\"{hostname}\"}} {score}")

    out_file = p.with_name(f"{p.stem}_metrics.prom")
    out_file.write_text("\n".join(metrics) + "\n")
    print(f"Wrote Lynis metrics: {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
