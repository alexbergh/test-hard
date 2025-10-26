#!/usr/bin/env bash
set -euo pipefail

SERVICES=(
  debian-agent
  ubuntu-agent
  fedora-agent
  centos-agent
  redos-agent
  altlinux-agent
  astra-agent
)

if [[ "${1:-}" == "--list" ]]; then
  printf '%s\n' "${SERVICES[@]}"
  exit 0
fi

compose_bin=${COMPOSE_BIN:-docker compose}

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
