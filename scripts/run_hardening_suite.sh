#!/usr/bin/env bash
set -euo pipefail

# Only include agents with publicly accessible base images by default.
SERVICES=(
  debian-agent
  ubuntu-agent
  fedora-agent
  centos-agent
)

if [[ "${1:-}" == "--list" ]]; then
  printf '%s\n' "${SERVICES[@]}"
  exit 0
fi

compose_bin=${COMPOSE_BIN:-docker compose}

if ! command -v "${compose_bin%% *}" >/dev/null 2>&1; then
  echo "[suite] Required command '${compose_bin}' is not available. Install Docker Compose or set COMPOSE_BIN." >&2
  exit 1
fi

${compose_bin} build "${SERVICES[@]}"
${compose_bin} up -d "${SERVICES[@]}"

for service in "${SERVICES[@]}"; do
  echo "[suite] Running security checks inside ${service}"
  if ${compose_bin} exec -T "$service" bash -lc '/opt/hardening/scripts/run_all_checks.sh'; then
    echo "[suite] ${service} completed successfully"
  else
    echo "[suite] ${service} reported failures" >&2
  fi
done
