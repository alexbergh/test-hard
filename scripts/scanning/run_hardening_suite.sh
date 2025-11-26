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

# РџРѕРґРЅРёРјР°РµРј СЃРєР°РЅРµСЂС‹ РєР°Рє СЃРµСЂРІРёСЃС‹ РґР»СЏ РґРѕСЃС‚СѓРїР° Рє РёС… С„Р°Р№Р»РѕРІРѕР№ СЃРёСЃС‚РµРјРµ
echo "[suite] Starting scanner services..."
${compose_bin} up -d "${scanners[@]}"

# Р—Р°РїСѓСЃРєР°РµРј СЃРєР°РЅРёСЂРѕРІР°РЅРёРµ
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

# РљРѕРїРёСЂСѓРµРј РѕС‚С‡С‘С‚С‹ РёР· СЂР°Р±РѕС‚Р°СЋС‰РёС… РєРѕРЅС‚РµР№РЅРµСЂРѕРІ
echo "[suite] Copying reports from containers..."

# РЎРЅР°С‡Р°Р»Р° РїСЂРѕРІРµСЂСЏРµРј С‡С‚Рѕ С„Р°Р№Р»С‹ СЃСѓС‰РµСЃС‚РІСѓСЋС‚ РІ РєРѕРЅС‚РµР№РЅРµСЂР°С…
echo "[suite] Checking files in containers..."

echo "[suite] OpenSCAP container files:"
docker exec openscap-scanner find /reports -type f 2>/dev/null || echo "No files in openscap-scanner"

echo "[suite] Lynis container files:"
docker exec lynis-scanner find /reports -type f 2>/dev/null || echo "No files in lynis-scanner"

# OpenSCAP РѕС‚С‡С‘С‚С‹ - РєРѕРїРёСЂСѓРµРј С‡РµСЂРµР· docker cp
for target in "${targets[@]}"; do
  echo "[suite] Copying OpenSCAP report for $target"
  mkdir -p reports/openscap

  # РљРѕРїРёСЂСѓРµРј РЅР°РїСЂСЏРјСѓСЋ С‡РµСЂРµР· docker cp
  docker cp "openscap-scanner:/reports/openscap/${target}.xml" "reports/openscap/${target}.xml" 2>/dev/null || echo "No XML for $target"
  docker cp "openscap-scanner:/reports/openscap/${target}.html" "reports/openscap/${target}.html" 2>/dev/null || echo "No HTML for $target"
  docker cp "openscap-scanner:/reports/openscap/${target}_metrics.prom" "reports/openscap/${target}_metrics.prom" 2>/dev/null || echo "No metrics for $target"
done

# Lynis РѕС‚С‡С‘С‚С‹ - РєРѕРїРёСЂСѓРµРј С‡РµСЂРµР· docker cp
for target in "${targets[@]}"; do
  echo "[suite] Copying Lynis report for $target"
  mkdir -p reports/lynis

  # РљРѕРїРёСЂСѓРµРј РЅР°РїСЂСЏРјСѓСЋ С‡РµСЂРµР· docker cp
  docker cp "lynis-scanner:/reports/lynis/${target}.log" "reports/lynis/${target}.log" 2>/dev/null || echo "No log for $target"
  docker cp "lynis-scanner:/reports/lynis/${target}.dat" "reports/lynis/${target}.dat" 2>/dev/null || echo "No dat for $target"
  docker cp "lynis-scanner:/reports/lynis/${target}_metrics.prom" "reports/lynis/${target}_metrics.prom" 2>/dev/null || echo "No metrics for $target"
done

# РџСЂРѕРІРµСЂРёС‚СЊ С„РёРЅР°Р»СЊРЅС‹Рµ С„Р°Р№Р»С‹ РїРµСЂРµРґ РѕСЃС‚Р°РЅРѕРІРєРѕР№
echo "[suite] Final check of files before stopping containers..."

echo "[suite] Final OpenSCAP files:"
docker exec openscap-scanner find /reports -type f 2>/dev/null || echo "No files"

echo "[suite] Final Lynis files:"
docker exec lynis-scanner find /reports -type f 2>/dev/null || echo "No files"

# РћСЃС‚Р°РЅР°РІР»РёРІР°РµРј СЃРєР°РЅРµСЂС‹
echo "[suite] Stopping scanner services..."
${compose_bin} stop "${scanners[@]}" 2>/dev/null || true

printf '\n[suite] Reports saved under %s\n' "$(realpath reports)"

# РџСЂРѕРІРµСЂРёС‚СЊ СЃРєРѕРїРёСЂРѕРІР°РЅРЅС‹Рµ С„Р°Р№Р»С‹
echo "[suite] Checking copied files:"
find reports -type f -name "*" | sort
