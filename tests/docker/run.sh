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
SAMPLE_XML="${SCRIPT_DIR}/openscap/content/sample-oval.xml"
SAMPLE_ARCHIVE="${SCRIPT_DIR}/openscap/content/fstec-sample.zip"
python3 "${SCRIPT_DIR}/../tools/create_sample_fstec_archive.py" \
  --source "${SAMPLE_XML}" \
  --archive "${SAMPLE_ARCHIVE}" \
  --prefix "linux"
python3 "${SCRIPT_DIR}/../../environments/openscap/tools/prepare_fstec_content.py" \
  --archive "${SAMPLE_ARCHIVE}" \
  --output "${SCRIPT_DIR}/openscap/content/fstec" \
  --clean >/dev/null
python3 "${SIMULATOR}" "${PROFILE}"
