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
  echo "OpenSCAP (oscap) not found; install it (e.g. 'sudo apt install openscap-scanner' or 'sudo dnf install openscap-scanner')" >&2
  echo "Alternatively run 'docker compose run --rm openscap-scanner' from the repository root." >&2
  exit 1
fi

XCCDF=$(find /usr/share/xml/scap/ssg -type f -name "ssg-*.xml" | head -n1 || true)
if [[ -z "${XCCDF}" ]]; then
  echo "No SSG XCCDF found under /usr/share/xml/scap/ssg" >&2
  exit 1
fi

# Validate requested profile exists in the selected XCCDF; pick a reasonable fallback
available_profiles=$(oscap info "$XCCDF" 2>/dev/null | grep -Eo 'Profile ID: .*|Id: .*' | sed -E 's/(Profile ID: |Id: )//' | tr -d '\r' || true)
if [[ -z "${available_profiles}" ]]; then
  echo "No profiles discovered in XCCDF, proceeding with requested profile: ${PROFILE}" >&2
else
  if ! echo "$available_profiles" | grep -q "^${PROFILE}$"; then
    echo "Requested profile ${PROFILE} not present in XCCDF; selecting a fallback profile" >&2
    if echo "$available_profiles" | grep -q "^xccdf_org.ssgproject.content_profile_standard$"; then
      PROFILE="xccdf_org.ssgproject.content_profile_standard"
      echo "Fallback to profile: ${PROFILE}" >&2
    else
      PROFILE=$(echo "$available_profiles" | head -n1)
      echo "Fallback to first available profile: ${PROFILE}" >&2
    fi
  fi
fi

oscap xccdf eval \
  --profile "$PROFILE" \
  --results-arf "$REPORT_ARF" \
  --report "$REPORT_HTML" \
  "$XCCDF"

PARSE_SCRIPT="$(dirname "$0")/../parsing/parse_openscap_report.py"
if [[ -x "$PARSE_SCRIPT" || -f "$PARSE_SCRIPT" ]]; then
  "$PARSE_SCRIPT" "$REPORT_ARF"
else
  echo "Parser not found: $PARSE_SCRIPT" >&2
  exit 1
fi
