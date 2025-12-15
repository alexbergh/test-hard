#!/usr/bin/env bash
set -euo pipefail

compose_bin=${COMPOSE_BIN:-docker compose}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "${script_dir}/../.." && pwd)"

targets=(
  target-fedora
  target-debian
  target-centos
  target-ubuntu
)

scanners=(
  openscap-scanner
  lynis-scanner
)

print_usage() {
  cat <<USAGE
Usage: ${0##*/} [--list-targets|--list-scanners]

Runs the hardening suite by starting target containers and executing all scanners.
USAGE
}

if [[ $# -gt 0 ]]; then
  case "$1" in
    --list)
      printf '%s\n' "${targets[@]}"
      exit 0
      ;;
    --list-targets)
      printf '%s\n' "${targets[@]}"
      exit 0
      ;;
    --list-scanners)
      printf '%s\n' "${scanners[@]}"
      exit 0
      ;;
    --help|-h)
      print_usage
      exit 0
      ;;
    *)
      print_usage >&2
      exit 1
      ;;
  esac
fi

if ! command -v "${compose_bin%% *}" >/dev/null 2>&1; then
  echo "[suite] Required command '${compose_bin}' is not available. Install Docker Compose or set COMPOSE_BIN." >&2
  exit 1
fi

cd "$project_root"

mkdir -p reports

${compose_bin} up -d docker-proxy "${targets[@]}"
# No need to build - unified image already exists

# Run scanners as one-off tasks. They will write results to ./reports via the /reports volume.
echo "[suite] Running scanners..."
status=0

for scanner in "${scanners[@]}"; do
  echo "[suite] Running ${scanner}"
  if ${compose_bin} run --rm "$scanner"; then
    echo "[suite] ${scanner} completed successfully"
  else
    echo "[suite] ${scanner} reported failures" >&2
    status=1
  fi
done

echo "[suite] Reports were written to ./reports via volume mounts"

printf '\n[suite] Reports saved under %s\n' "$(realpath reports)"

# РџСЂРѕРІРµСЂРёС‚СЊ СЃРєРѕРїРёСЂРѕРІР°РЅРЅС‹Рµ С„Р°Р№Р»С‹
echo "[suite] Checking report files:"
find reports -type f -name "*" | sort

exit "$status"
