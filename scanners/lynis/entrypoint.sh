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
  docker cp "${name}:/tmp/lynis.log" "$logfile" >/dev/null 2>&1 || docker exec "${name}" cat /tmp/lynis.log > "$logfile"
  docker cp "${name}:/var/log/lynis-report.dat" "/reports/lynis/${name}.dat" >/dev/null 2>&1 || true
  
  # Извлечь метрики из отчёта и создать Prometheus metrics
  extract_lynis_metrics "$name" "$logfile"
}

extract_lynis_metrics() {
  local name="$1"
  local logfile="$2"
  local metrics_file="/reports/lynis/${name}_metrics.prom"
  local details_file="/reports/lynis/${name}_details.prom"
  
  echo "[Lynis] Extracting metrics for ${name}" >&2
  
  # Извлечь hardness score
  local score
  score=$(grep -i "hardening index" "$logfile" | grep -oE "\[[0-9]+\]" | grep -oE "[0-9]+" | head -1 || echo "0")
  
  # Извлечь количество предупреждений
  local warnings
  warnings=$(grep -c "Warning:" "$logfile" 2>/dev/null || echo "0")
  
  # Извлечь количество предложений
  local suggestions
  suggestions=$(grep -c "Suggestion:" "$logfile" 2>/dev/null || echo "0")
  
  # Создать основной Prometheus metrics файл
  cat > "$metrics_file" <<EOF
# HELP lynis_score Lynis hardening score
# TYPE lynis_score gauge
lynis_score{host="${name}"} ${score}
# HELP lynis_warnings Lynis warnings count
# TYPE lynis_warnings gauge
lynis_warnings{host="${name}"} ${warnings}
# HELP lynis_suggestions Lynis suggestions count
# TYPE lynis_suggestions gauge
lynis_suggestions{host="${name}"} ${suggestions}
EOF

  # Создать детальный файл с конкретными проблемами
  {
    echo "# HELP lynis_test_result Lynis test results (1=issue found, 0=passed)"
    echo "# TYPE lynis_test_result gauge"
    
    # Извлечь warnings с test ID
    grep "Warning:" "$logfile" | grep -oE "\[test:[A-Z]+-[0-9]+\]" | sed 's/\[test://;s/\]//' | sort -u | while read -r test_id; do
      if [ -n "$test_id" ]; then
        # Получить описание warning
        description=$(grep "Warning:.*\[test:${test_id}\]" "$logfile" | head -1 | sed 's/.*Warning: //;s/ \[test:.*$//' | sed 's/"//g' | cut -c1-100)
        echo "lynis_test_result{host=\"${name}\",test_id=\"${test_id}\",type=\"warning\",description=\"${description}\"} 1"
      fi
    done
    
    # Извлечь suggestions с test ID (топ-20)
    grep "Suggestion:" "$logfile" | grep -oE "\[test:[A-Z]+-[0-9]+\]" | sed 's/\[test://;s/\]//' | sort -u | head -20 | while read -r test_id; do
      if [ -n "$test_id" ]; then
        description=$(grep "Suggestion:.*\[test:${test_id}\]" "$logfile" | head -1 | sed 's/.*Suggestion: //;s/ \[test:.*$//' | sed 's/"//g' | cut -c1-100)
        echo "lynis_test_result{host=\"${name}\",test_id=\"${test_id}\",type=\"suggestion\",description=\"${description}\"} 1"
      fi
    done
  } > "$details_file"

  echo "[Lynis] Metrics saved to $metrics_file" >&2
  echo "[Lynis] Details saved to $details_file" >&2
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
