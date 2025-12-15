#!/bin/bash
set -euo pipefail

# Skip sudo escalation in Docker containers - run as root directly
# Container should be started with proper capabilities

HOSTNAME="$(hostname 2>/dev/null || echo "unknown-host")"
RESULT_ROOT="${HARDENING_RESULTS_DIR:-/var/lib/hardening/results}"
RESULT_DIR="${RESULT_ROOT%/}/lynis"
TIMESTAMP="$(date +%Y%m%dT%H%M%S)"
REPORT_FILE="${RESULT_DIR}/lynis-${HOSTNAME}-${TIMESTAMP}.txt"

install -d -m 0775 "$RESULT_DIR"

echo "[hardening] Running Lynis"

ROOTDIR="${ROOTDIR:-/usr/share/lynis}"
export ROOTDIR
# Ensure plugin directories exist so Lynis doesn't abort
mkdir -p /etc/lynis/plugins /usr/share/lynis/plugins || true

# Default profile to use if none specified
PROFILE="${PROFILE:-/etc/lynis/default.prf}"
if [[ ! -f "$PROFILE" ]]; then
  # Try to create a fallback default profile from included profiles
  if [[ -f "$ROOTDIR/include/profiles" ]]; then
    cp "$ROOTDIR/include/profiles" "$PROFILE" || true
  fi
fi

if [[ -d "$ROOTDIR" ]]; then
  cd "$ROOTDIR"
fi

if ! lynis --profile "$PROFILE" audit system --no-colors --quiet --nolog | tee "$REPORT_FILE"; then
  echo "[hardening] Lynis execution failed" >&2
  # Do not exit here; allow post-processing (metrics generation / copying)
fi

echo "[hardening] Lynis scan completed (JSON output not available in this version)"

# Attempt to generate a Prometheus metrics file from the Lynis text report so
# Telegraf can pick it up via the file input plugin. Use the script shipped in
# scripts/parsing; tolerate failures so the scanner run overall doesn't fail.
PARSER_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PARSER="$PARSER_DIR/parsing/generate_lynis_metrics.py"
if [[ -x "$PARSER" || -f "$PARSER" ]]; then
  if ! python3 "$PARSER" "$REPORT_FILE"; then
    echo "[hardening] Lynis metrics generation failed" >&2
  fi
else
  echo "[hardening] Lynis metrics generator not found: $PARSER" >&2
fi
