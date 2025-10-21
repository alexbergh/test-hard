#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-all}"
case "$PROFILE" in
  openscap)
    docker compose --project-name hardening-tests -f "$(dirname "$0")/docker-compose.yml" --profile openscap up --abort-on-container-exit
    ;;
  telemetry)
    docker compose --project-name hardening-tests -f "$(dirname "$0")/docker-compose.yml" --profile telemetry up -d
    ;;
  wazuh)
    docker compose --project-name hardening-tests -f "$(dirname "$0")/docker-compose.yml" --profile wazuh up -d
    ;;
  all)
    docker compose --project-name hardening-tests -f "$(dirname "$0")/docker-compose.yml" --profile openscap --profile telemetry --profile wazuh up -d
    ;;
  *)
    echo "Unknown profile: $PROFILE" >&2
    exit 1
    ;;
esac
