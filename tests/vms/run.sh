#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PACKER_TEMPLATE="${SCRIPT_DIR}/packer/linux.pkr.hcl"
SIMULATOR="${SCRIPT_DIR}/simulate.py"
if [[ -z "${HARDENING_FIXED_TIMESTAMP:-}" ]]; then
  export HARDENING_FIXED_TIMESTAMP="2025-01-01T00:00:00+00:00"
fi
MODE="${HARDENING_VM_MODE:-simulate}"
ENVIRONMENT="${1:-all}"

declare -a DISTROS=("redos-7.3" "redos-8" "astralinux-1.7" "altlinux-8" "centos-7")
declare -a ENVIRONMENTS=()

case "$ENVIRONMENT" in
  test)
    ENVIRONMENTS=("test")
    ;;
  prod)
    ENVIRONMENTS=("prod")
    ;;
  all)
    ENVIRONMENTS=("test" "prod")
    ;;
  *)
    echo "Неизвестное окружение: ${ENVIRONMENT}" >&2
    exit 1
    ;;
esac

if [[ "$MODE" == "packer" ]] && command -v packer >/dev/null 2>&1; then
  VAR_FILE="${HARDENING_VM_IMAGE_VARS:-}"
  if [[ ! -f "$PACKER_TEMPLATE" ]]; then
    echo "Packer-шаблон не найден: $PACKER_TEMPLATE" >&2
    exit 1
  fi
  for env in "${ENVIRONMENTS[@]}"; do
    for distro in "${DISTROS[@]}"; do
      echo "[packer] Сборка ${distro} (${env})" >&2
      if [[ -n "$VAR_FILE" ]]; then
        packer build -var "distro=${distro}" -var "environment=${env}" -var-file "$VAR_FILE" "$PACKER_TEMPLATE"
      else
        packer build -var "distro=${distro}" -var "environment=${env}" "$PACKER_TEMPLATE"
      fi
    done
  done
  exit 0
fi

echo "Packer недоступен или режим не задан, выполняется симуляция (${ENVIRONMENTS[*]})" >&2
python3 "$SIMULATOR" "$ENVIRONMENT"
