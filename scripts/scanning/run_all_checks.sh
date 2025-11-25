#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULT_ROOT="${HARDENING_RESULTS_DIR:-/var/lib/hardening/results}"
ART_STORAGE="${HARDENING_ART_STORAGE:-/var/lib/hardening/art-storage}"
LOG_SUFFIX="$(date +%Y%m%dT%H%M%S)"

ensure_dir() {
  local path="$1"
  [[ -z "$path" ]] && return 0

  if install -d -m 0775 "$path" 2>/dev/null; then
    return 0
  fi

  if command -v sudo >/dev/null 2>&1; then
    if sudo install -d -m 0775 "$path"; then
      sudo chown "$(id -u)":"$(id -g)" "$path"
      return 0
    fi
  fi

  echo "[hardening] Unable to prepare directory $path" >&2
  return 1
}

ensure_dir "$RESULT_ROOT"
ensure_dir "$RESULT_ROOT/lynis"
ensure_dir "$RESULT_ROOT/openscap"
ensure_dir "$RESULT_ROOT/atomic"
ensure_dir "$ART_STORAGE"

status=0

run_step() {
  local name="$1"
  shift
  echo "[hardening] Running ${name}"
  if "$@"; then
    echo "[hardening] ${name} completed"
  else
    echo "[hardening] ${name} failed" >&2
    status=1
  fi
}

# Lynis audit (requires root privileges)
run_step "Lynis" bash "$SCRIPT_DIR/run_lynis.sh"

# OpenSCAP scan with default profile when available
run_step "OpenSCAP" bash "$SCRIPT_DIR/run_openscap.sh" "${OPENSCAP_PROFILE:-xccdf_org.ssgproject.content_profile_cis}"

# Atomic Red Team curated scenarios (dry run allowed via env)
ART_MODE="${ATOMIC_MODE:-run}"
ART_ARGS=("${SCRIPT_DIR}/run_atomic_red_team_suite.py" "--output" \
  "${HARDENING_ART_STORAGE:-/var/lib/hardening/art-storage}" "--timeout" "${ATOMIC_TIMEOUT:-60}")
if [[ "${ATOMIC_DRY_RUN:-false}" == "true" ]]; then
  ART_ARGS+=("--dry-run")
fi
if [[ -n "${ATOMIC_TECHNIQUE:-}" ]]; then
  ART_ARGS+=("--technique" "${ATOMIC_TECHNIQUE}")
fi
run_step "Atomic Red Team" python3 "${ART_ARGS[@]}" "--mode" "${ART_MODE}"

# Persist combined status for Telegraf or external scraping
METRICS_FILE="${RESULT_ROOT}/security-check-${LOG_SUFFIX}.prom"
{
  echo "security_hardening_last_run{check=\"lynis\"} $(date +%s)"
  echo "security_hardening_last_run{check=\"openscap\"} $(date +%s)"
  echo "security_hardening_last_run{check=\"atomic_red_team\"} $(date +%s)"
  echo "security_hardening_status ${status}"
} >"$METRICS_FILE"

exit "$status"
