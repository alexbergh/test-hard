#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-xccdf_org.ssgproject.content_profile_cis}"
HOSTNAME="$(hostname 2>/dev/null || echo "unknown-host")"
RESULT_ROOT="${HARDENING_RESULTS_DIR:-/var/lib/hardening/results}"
RESULT_DIR="${RESULT_ROOT%/}/openscap"
TIMESTAMP="$(date +%Y%m%dT%H%M%S)"
REPORT_HTML="${RESULT_DIR}/openscap-${HOSTNAME}-${TIMESTAMP}.html"
REPORT_ARF="${RESULT_DIR}/openscap-${HOSTNAME}-${TIMESTAMP}.arf"

install -d -m 0775 "$RESULT_DIR"

if ! command -v oscap >/dev/null 2>&1; then
  echo "OpenSCAP (oscap) not found; install it first." >&2
  exit 1
fi

XCCDF=$(find /usr/share/xml/scap/ssg -type f -name "ssg-*.xml" | head -n1 || true)
if [[ -z "${XCCDF}" ]]; then
  echo "No SSG XCCDF found under /usr/share/xml/scap/ssg" >&2
  exit 1
fi

sudo oscap xccdf eval \
  --profile "$PROFILE" \
  --results-arf "$REPORT_ARF" \
  --report "$REPORT_HTML" \
  "$XCCDF"

"$(dirname "$0")/parse_openscap_report.py" "$REPORT_ARF"
