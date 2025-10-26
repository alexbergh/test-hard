#!/usr/bin/env bash
set -euo pipefail

: "${RUN_HARDENING_ON_START:=false}"

if [[ "${RUN_HARDENING_ON_START}" == "true" ]]; then
  echo "[hardening] RUN_HARDENING_ON_START=true — launching security checks"
  if ! /opt/hardening/scripts/run_all_checks.sh; then
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
