#!/usr/bin/env python3
"""Parse Lynis text log and generate Prometheus metrics."""
import re
import sys
from pathlib import Path


def parse_lynis_log(log_path: str, hostname: str = "localhost") -> None:
    """Parse Lynis text log and output Prometheus metrics."""
    path = Path(log_path)

    if not path.exists():
        print(f"Error: Log file not found: {path}", file=sys.stderr)
        sys.exit(1)

    with open(path, "r") as f:
        content = f.read()

    # Extract hardening index
    score = 0
    # Try format: "Hardening index : [61]"
    hardening_match = re.search(r"Hardening index\s*:\s*\[?(\d+)\]?", content, re.IGNORECASE)
    if hardening_match:
        score = int(hardening_match.group(1))

    # Count warnings and suggestions
    warnings = content.count("Warning:")
    suggestions = content.count("Suggestion:")

    # Count tests performed
    tests_done = len(re.findall(r"Performing test ID", content))

    # Generate Prometheus metrics
    print("# HELP lynis_score Lynis hardening score")
    print("# TYPE lynis_score gauge")
    print(f'lynis_score{{host="{hostname}"}} {score}')
    print()
    print("# HELP lynis_warnings_count Lynis warnings count")
    print("# TYPE lynis_warnings_count gauge")
    print(f'lynis_warnings_count{{host="{hostname}"}} {warnings}')
    print()
    print("# HELP lynis_suggestions_count Lynis suggestions count")
    print("# TYPE lynis_suggestions_count gauge")
    print(f'lynis_suggestions_count{{host="{hostname}"}} {suggestions}')
    print()
    print("# HELP lynis_tests_performed Lynis tests performed")
    print("# TYPE lynis_tests_performed gauge")
    print(f'lynis_tests_performed{{host="{hostname}"}} {tests_done}')


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: parse_lynis_log.py <log_file> [hostname]", file=sys.stderr)
        sys.exit(1)

    log_file = sys.argv[1]
    hostname = sys.argv[2] if len(sys.argv) > 2 else "localhost"

    parse_lynis_log(log_file, hostname)
