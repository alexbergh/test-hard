#!/usr/bin/env bash
set -euo pipefail

IFS=' ' read -r -a targets <<< "${TARGET_CONTAINERS:-}"

if [ ${#targets[@]} -eq 0 ]; then
  echo "No target containers provided via TARGET_CONTAINERS" >&2
  exit 1
fi

mkdir -p /reports/lynis

run_install() {
  local name="$1"
  case "$name" in
    target-fedora)
      docker exec "$name" sh -c "dnf -y update && dnf -y install lynis procps-ng"
      ;;
    target-centos)
      docker exec "$name" sh -c "dnf -y update && dnf -y install epel-release && dnf -y install lynis procps-ng"
      ;;
    target-debian|target-ubuntu)
      docker exec "$name" sh -c "apt-get update && apt-get install -y lynis procps"
      ;;
    *)
      echo "Unknown container $name for Lynis install" >&2
      return 1
      ;;
  esac
}

audit_container() {
  local name="$1"
  local logfile="/reports/lynis/${name}.log"
  echo "[Lynis] Running audit for ${name}" >&2
  
  # Удалить старые PID и lock файлы
  docker exec "$name" sh -c "rm -f /var/run/lynis.pid /var/run/lynis.lock" 2>/dev/null || true
  
  if ! docker exec "$name" lynis audit system --quiet --logfile /tmp/lynis.log --report-file /tmp/lynis-report.dat; then
    echo "Lynis audit failed inside ${name}" >&2
    return 1
  fi
  docker cp "${name}:/tmp/lynis.log" "$logfile" >/dev/null 2>&1 || docker exec "$name" cat /tmp/lynis.log > "$logfile"
  docker cp "${name}:/var/log/lynis-report.dat" "/reports/lynis/${name}.dat" >/dev/null 2>&1 || true
}

status=0

for target in "${targets[@]}"; do
  if ! run_install "$target"; then
    status=1
    continue
  fi
  if ! audit_container "$target"; then
    status=1
  fi
done

exit $status
