#!/usr/bin/env bash
set -euo pipefail

compose_bin=${COMPOSE_BIN:-docker compose}

targets=(
  target-fedora
  target-debian
  target-centos
  target-ubuntu
)

scanners=(
  openscap-scanner
  lynis-scanner
)

print_usage() {
  cat <<USAGE
Usage: ${0##*/} [--list-targets|--list-scanners]

Runs the hardening suite by starting target containers and executing all scanners.
USAGE
}

if [[ $# -gt 0 ]]; then
  case "$1" in
    --list)
      printf '%s\n' "${targets[@]}"
      exit 0
      ;;
    --list-targets)
      printf '%s\n' "${targets[@]}"
      exit 0
      ;;
    --list-scanners)
      printf '%s\n' "${scanners[@]}"
      exit 0
      ;;
    --help|-h)
      print_usage
      exit 0
      ;;
    *)
      print_usage >&2
      exit 1
      ;;
  esac
fi

if ! command -v "${compose_bin%% *}" >/dev/null 2>&1; then
  echo "[suite] Required command '${compose_bin}' is not available. Install Docker Compose or set COMPOSE_BIN." >&2
  exit 1
fi

mkdir -p reports

${compose_bin} up -d "${targets[@]}"
${compose_bin} build "${scanners[@]}"

# Поднимаем сканеры как сервисы для доступа к их файловой системе
echo "[suite] Starting scanner services..."
${compose_bin} up -d "${scanners[@]}"

# Запускаем сканирование
for scanner in "${scanners[@]}"; do
  echo "[suite] Running ${scanner}"
  case "$scanner" in
    lynis-scanner)
      if ${compose_bin} exec -T "$scanner" /usr/local/bin/entrypoint.sh; then
        echo "[suite] ${scanner} completed successfully"
      else
        echo "[suite] ${scanner} reported failures" >&2
      fi
      ;;
    openscap-scanner)
      if ${compose_bin} exec -T "$scanner" /usr/local/bin/openscap_entrypoint.sh; then
        echo "[suite] ${scanner} completed successfully"
      else
        echo "[suite] ${scanner} reported failures" >&2
      fi
      ;;
    *)
      echo "[suite] Unknown scanner: $scanner" >&2
      ;;
  esac
done

# Копируем отчёты из работающих контейнеров
echo "[suite] Copying reports from containers..."

# OpenSCAP отчёты
for target in "${targets[@]}"; do
  echo "[suite] Copying OpenSCAP report for $target"
  mkdir -p reports/openscap
  ${compose_bin} exec -T openscap-scanner sh -c "
    if [ -f /reports/openscap/${target}.xml ]; then
      cat /reports/openscap/${target}.xml
    fi
  " > "reports/openscap/${target}.xml" 2>/dev/null || true
  
  ${compose_bin} exec -T openscap-scanner sh -c "
    if [ -f /reports/openscap/${target}.html ]; then
      cat /reports/openscap/${target}.html  
    fi
  " > "reports/openscap/${target}.html" 2>/dev/null || true
done

# Lynis отчёты  
for target in "${targets[@]}"; do
  echo "[suite] Copying Lynis report for $target"
  mkdir -p reports/lynis
  ${compose_bin} exec -T lynis-scanner sh -c "
    if [ -f /reports/lynis/${target}.log ]; then
      cat /reports/lynis/${target}.log
    fi
  " > "reports/lynis/${target}.log" 2>/dev/null || true
  
  ${compose_bin} exec -T lynis-scanner sh -c "
    if [ -f /reports/lynis/${target}.dat ]; then
      cat /reports/lynis/${target}.dat
    fi
  " > "reports/lynis/${target}.dat" 2>/dev/null || true
done

# Останавливаем сканеры
echo "[suite] Stopping scanner services..."
${compose_bin} stop "${scanners[@]}" 2>/dev/null || true

printf '\n[suite] Reports saved under %s\n' "$(realpath reports)"
