#!/bin/bash
set -euo pipefail

if [[ "${LYNIS_ALREADY_ESCALATED:-0}" != "1" && "$(id -u)" -ne 0 ]]; then
  exec sudo -E LYNIS_ALREADY_ESCALATED=1 "$0" "$@"
fi

HOSTNAME="$(hostname 2>/dev/null || echo "unknown-host")"
RESULT_ROOT="${HARDENING_RESULTS_DIR:-/var/lib/hardening/results}"
RESULT_DIR="${RESULT_ROOT%/}/lynis"
TIMESTAMP="$(date +%Y%m%dT%H%M%S)"
REPORT_FILE="${RESULT_DIR}/lynis-${HOSTNAME}-${TIMESTAMP}.txt"

install -d -m 0775 "$RESULT_DIR"

echo "[hardening] Running Lynis"

if ! lynis audit system --no-colors --quiet --nolog | tee "$REPORT_FILE"; then
  echo "[hardening] Lynis execution failed" >&2
  exit 1
fi

echo "[hardening] Lynis scan completed (JSON output not available in this version)"
