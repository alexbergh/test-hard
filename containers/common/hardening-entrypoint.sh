#!/usr/bin/env bash
set -euo pipefail

: "${RUN_HARDENING_ON_START:=false}"

umask 002

ensure_dir() {
  local path="$1"
  local mode="${2:-0775}"
  [[ -z "$path" ]] && return 0

  if install -d -m "$mode" "$path" 2>/dev/null; then
    return 0
  fi

  if command -v sudo >/dev/null 2>&1; then
    if sudo install -d -m "$mode" "$path"; then
      sudo chown "$(id -u)":"$(id -g)" "$path"
      return 0
    fi
  fi

  echo "[hardening] Warning: unable to ensure directory $path" >&2
  return 1
}

ensure_dir "${HARDENING_RESULTS_DIR:-/var/lib/hardening/results}"
ensure_dir "${HARDENING_RESULTS_DIR:-/var/lib/hardening/results}/lynis"
ensure_dir "${HARDENING_RESULTS_DIR:-/var/lib/hardening/results}/openscap"
ensure_dir "${HARDENING_RESULTS_DIR:-/var/lib/hardening/results}/atomic"
ensure_dir "${HARDENING_ART_STORAGE:-/var/lib/hardening/art-storage}"

if [[ "${RUN_HARDENING_ON_START}" == "true" ]]; then
  echo "[hardening] RUN_HARDENING_ON_START=true - launching security checks"
  if ! /opt/hardening/scripts/scanning/run_all_checks.sh; then
    echo "[hardening] Security checks completed with errors" >&2
  else
    echo "[hardening] Security checks completed successfully"
  fi
fi

if [[ $# -gt 0 ]]; then
  exec "$@"
else
  exec sleep infinity
fi
