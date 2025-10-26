#!/bin/bash
set -euo pipefail

if [[ "${LYNIS_ALREADY_ESCALATED:-0}" != "1" && "$(id -u)" -ne 0 ]]; then
  exec sudo -E LYNIS_ALREADY_ESCALATED=1 "$0" "$@"
fi

HOSTNAME="$(hostname 2>/dev/null || echo "unknown-host")"
REPORT_FILE="/tmp/lynis-report-${HOSTNAME}.txt"

echo "[hardening] Running Lynis"

lynis audit system --no-colors --quiet --nolog | tee "$REPORT_FILE"

echo "[hardening] Lynis scan completed (JSON output not available in this version)"
