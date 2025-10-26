#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-xccdf_org.ssgproject.content_profile_cis}"
HOSTNAME="$(hostname 2>/dev/null || echo "unknown-host")"
REPORT_HTML="/tmp/openscap-${HOSTNAME}.html"
REPORT_ARF="/tmp/openscap-${HOSTNAME}.arf"

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
