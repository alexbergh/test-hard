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
    
    # Извлечь метрики из XML и создать Prometheus metrics
    extract_openscap_metrics "$name" "/reports/openscap/${name}.xml"
    
    echo "[OpenSCAP] Scan completed for $name" >&2
    return 0
  else
    echo "[OpenSCAP] Scan failed for $name" >&2
    return 1
  fi
}

extract_openscap_metrics() {
  local name="$1"
  local xml_file="$2"
  local metrics_file="/reports/openscap/${name}_metrics.prom"
  
  echo "[OpenSCAP] Extracting metrics for ${name}" >&2
  
  if [ ! -f "$xml_file" ]; then
    echo "[OpenSCAP] XML file not found: $xml_file" >&2
    return 1
  fi
  
  # Извлечь количество passed, failed, notselected правил
  local pass_count
  local fail_count
  local notselected_count
  
  pass_count=$(grep -o 'result="pass"' "$xml_file" | wc -l | tr -d ' ' || echo "0")
  fail_count=$(grep -o 'result="fail"' "$xml_file" | wc -l | tr -d ' ' || echo "0") 
  notselected_count=$(grep -o 'result="notselected"' "$xml_file" | wc -l | tr -d ' ' || echo "0")
  
  # Вычислить score из pass/fail
  local total=$((pass_count + fail_count))
  local score=0
  if [ "$total" -gt 0 ]; then
    score=$((pass_count * 100 / total))
  fi
  
  # Создать Prometheus metrics файл
  cat > "$metrics_file" <<EOF
# HELP openscap_pass_count OpenSCAP passed rules count
# TYPE openscap_pass_count gauge
openscap_pass_count{host="${name}"} ${pass_count}
# HELP openscap_fail_count OpenSCAP failed rules count
# TYPE openscap_fail_count gauge
openscap_fail_count{host="${name}"} ${fail_count}
# HELP openscap_score OpenSCAP compliance score
# TYPE openscap_score gauge
openscap_score{host="${name}"} ${score}
EOF

  echo "[OpenSCAP] Metrics saved to $metrics_file" >&2
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
