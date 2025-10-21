#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
SIMULATOR="${SCRIPT_DIR}/simulate.py"

PROFILE="${1:-all}"

if command -v docker >/dev/null 2>&1; then
  case "$PROFILE" in
    openscap)
      docker compose --project-name hardening-tests -f "${COMPOSE_FILE}" --profile openscap up --abort-on-container-exit
      ;;
    telemetry)
      docker compose --project-name hardening-tests -f "${COMPOSE_FILE}" --profile telemetry up -d
      ;;
    wazuh)
      docker compose --project-name hardening-tests -f "${COMPOSE_FILE}" --profile wazuh up -d
      ;;
    all)
      docker compose --project-name hardening-tests -f "${COMPOSE_FILE}" --profile openscap --profile telemetry --profile wazuh up -d
      ;;
    *)
      echo "Unknown profile: $PROFILE" >&2
      exit 1
      ;;
  esac
  exit 0
fi

echo "Docker не обнаружен. Запускается оффлайн-симуляция профиля ${PROFILE}" >&2
python3 "${SIMULATOR}" "${PROFILE}"
