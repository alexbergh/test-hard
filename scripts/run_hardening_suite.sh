#!/usr/bin/env bash
set -euo pipefail

compose_bin=${COMPOSE_BIN:-docker compose}

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

mkdir -p reports

${compose_bin} up -d "${targets[@]}"
${compose_bin} build "${scanners[@]}"

for scanner in "${scanners[@]}"; do
  echo "[suite] Running ${scanner}"
  if ${compose_bin} run --rm "$scanner"; then
    echo "[suite] ${scanner} completed successfully"
  else
    echo "[suite] ${scanner} reported failures" >&2
  fi
done

printf '\n[suite] Reports saved under %s\n' "$(realpath reports)"
