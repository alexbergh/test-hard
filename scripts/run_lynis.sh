#!/usr/bin/env bash
set -euo pipefail

REPORT_FILE="/tmp/lynis-report-$(hostname).json"

if ! command -v lynis >/dev/null 2>&1; then
  echo "lynis not found; install it first." >&2
  exit 1
fi

# Run the audit (requires sudo for a full system scan).
sudo lynis audit system --quiet --no-colors --json --report-file "$REPORT_FILE"

# Emit metrics in Prometheus exposition format.
/usr/bin/env python3 "$(dirname "$0")/parse_lynis_report.py" "$REPORT_FILE"
