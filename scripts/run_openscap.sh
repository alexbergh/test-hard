#!/usr/bin/env bash
set -euo pipefail

# Пример профиля — замените на нужный (cis, stig и т.д.)
PROFILE="${1:-xccdf_org.ssgproject.content_profile_cis}"
REPORT_HTML="/tmp/openscap-$(hostname).html"
REPORT_ARF="/tmp/openscap-$(hostname).arf"

if ! command -v oscap >/dev/null 2>&1; then
  echo "OpenSCAP (oscap) not found; install it first." >&2
  exit 1
fi

# Пример для RHEL/Ubuntu с пакетами ssg-* (путь может отличаться)
# Найдём любой ssg-*.xml:
XCCDF=$(find /usr/share/xml/scap/ssg -type f -name "ssg-*.xml" | head -n1 || true)
if [ -z "${XCCDF}" ]; then
  echo "No SSG XCCDF found under /usr/share/xml/scap/ssg" >&2
  exit 1
fi

sudo oscap xccdf eval \
  --profile "$PROFILE" \
  --results-arf "$REPORT_ARF" \
  --report "$REPORT_HTML" \
  "$XCCDF"

# Парсинг результатов в Prometheus
"$(dirname "$0")/parse_openscap_report.py" "$REPORT_ARF"
