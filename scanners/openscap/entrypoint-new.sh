#!/usr/bin/env bash
set -euo pipefail

IFS=' ' read -r -a targets <<< "${TARGET_CONTAINERS:-}"

if [ ${#targets[@]} -eq 0 ]; then
  echo "No target containers provided via TARGET_CONTAINERS" >&2
  exit 1
fi

mkdir -p /reports/openscap

PROFILE="xccdf_org.ssgproject.content_profile_standard"

install_openscap() {
  local name="$1"
  case "$name" in
    target-fedora)
      docker exec "$name" sh -c "dnf -y install openscap-scanner scap-security-guide 2>&1 | grep -v 'already installed' || true"
      ;;
    target-centos)
      docker exec "$name" sh -c "dnf -y install openscap-scanner scap-security-guide 2>&1 | grep -v 'already installed' || true"
      ;;
    target-debian|target-ubuntu)
      # Для Debian/Ubuntu не устанавливаем - будем использовать host сканер
      echo "Skipping OpenSCAP install for $name - will use host scanner"
      ;;
    *)
      echo "Unknown container $name for OpenSCAP install" >&2
      return 1
      ;;
  esac
}

get_datastream() {
  local name="$1"
  case "$name" in
    target-fedora)
      echo "/usr/share/xml/scap/ssg/content/ssg-fedora-ds.xml"
      ;;
    target-centos)
      echo "/usr/share/xml/scap/ssg/content/ssg-cs9-ds.xml"
      ;;
    target-debian)
      # Пробуем разные пути для datastream
      echo "/usr/share/xml/scap/ssg/content/ssg-debian12-ds.xml"
      ;;
    target-ubuntu)
      # Пробуем разные пути для datastream
      echo "/usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml"
      ;;
    *)
      echo ""
      ;;
  esac
}

scan_container() {
  local name="$1"
  local datastream
  datastream=$(get_datastream "$name")
  
  if [ -z "$datastream" ]; then
    echo "No datastream mapping for $name, skipping" >&2
    return 0
  fi
  
  # Проверить что datastream существует, или найти альтернативный путь
  if ! docker exec "$name" test -f "$datastream" 2>/dev/null; then
    echo "Primary datastream $datastream not found, searching alternatives..." >&2
    
    # Искать datastream файлы автоматически
    local found_datastream
    found_datastream=$(docker exec "$name" find /usr -name "*ssg*ds.xml" -type f 2>/dev/null | head -1 || true)
    
    if [ -z "$found_datastream" ]; then
      echo "No datastream files found in $name, skipping" >&2
      return 0
    fi
    
    datastream="$found_datastream"
    echo "Found alternative datastream: $datastream" >&2
  fi
  
  local result_file="/tmp/openscap-results.xml"
  local report_file="/tmp/openscap-report.html"
  
  echo "[OpenSCAP] Scanning $name using $datastream" >&2
  
  # Запустить сканирование внутри контейнера
  if docker exec "$name" oscap xccdf eval \
    --profile "$PROFILE" \
    --results "$result_file" \
    --report "$report_file" \
    "$datastream" >/dev/null 2>&1 || true; then
    
    # Скопировать результаты
    docker cp "$name:$result_file" "/reports/openscap/${name}.xml" 2>/dev/null || echo "Failed to copy XML"
    docker cp "$name:$report_file" "/reports/openscap/${name}.html" 2>/dev/null || echo "Failed to copy HTML"
    
    echo "[OpenSCAP] Scan completed for $name" >&2
    return 0
  else
    echo "[OpenSCAP] Scan failed for $name" >&2
    return 1
  fi
}

status=0

for target in "${targets[@]}"; do
  if ! install_openscap "$target"; then
    echo "Failed to install OpenSCAP in $target" >&2
    status=1
    continue
  fi
  
  if ! scan_container "$target"; then
    status=1
  fi
done

exit $status
