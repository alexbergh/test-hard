#!/usr/bin/env bash
# =============================================================================
# Сканирование контейнерных образов с помощью Trivy
# Генерация отчётов уязвимостей и SBOM (CycloneDX + SPDX)
#
# Использование:
#   ./scripts/scanning/scan-images.sh [--all|--image IMAGE] [--sbom] [--fail-on HIGH]
#
# Примеры:
#   ./scripts/scanning/scan-images.sh --all              # Сканировать все образы из docker-compose
#   ./scripts/scanning/scan-images.sh --image nginx:latest --sbom
#   ./scripts/scanning/scan-images.sh --all --fail-on CRITICAL
#   ./scripts/scanning/scan-images.sh --all --sbom --output json
# =============================================================================
set -euo pipefail

# ---- Цвета ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ---- Настройки по умолчанию ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORTS_DIR="${PROJECT_ROOT}/reports/trivy"
SBOM_DIR="${PROJECT_ROOT}/reports/sbom"
TRIVY_CONFIG="${PROJECT_ROOT}/trivy/trivy.yaml"
TRIVYIGNORE="${PROJECT_ROOT}/trivy/.trivyignore"

SCAN_ALL=false
SCAN_IMAGE=""
GENERATE_SBOM=false
FAIL_ON="CRITICAL"
OUTPUT_FORMAT="table"
USE_SERVER=false
TRIVY_SERVER_URL="http://localhost:4954"

# ---- Парсинг аргументов ----
while [[ $# -gt 0 ]]; do
    case "$1" in
        --all)          SCAN_ALL=true; shift ;;
        --image)        SCAN_IMAGE="$2"; shift 2 ;;
        --sbom)         GENERATE_SBOM=true; shift ;;
        --fail-on)      FAIL_ON="$2"; shift 2 ;;
        --output)       OUTPUT_FORMAT="$2"; shift 2 ;;
        --server)       USE_SERVER=true; shift ;;
        --server-url)   TRIVY_SERVER_URL="$2"; shift 2 ;;
        -h|--help)
            echo "Использование: $0 [--all|--image IMAGE] [--sbom] [--fail-on SEVERITY] [--output FORMAT]"
            echo ""
            echo "Параметры:"
            echo "  --all              Сканировать все образы из docker-compose.yml"
            echo "  --image IMAGE      Сканировать конкретный образ"
            echo "  --sbom             Генерировать SBOM (CycloneDX + SPDX)"
            echo "  --fail-on SEVERITY Минимальная серьёзность для ошибки (CRITICAL|HIGH|MEDIUM|LOW)"
            echo "  --output FORMAT    Формат вывода (table|json|sarif|cyclonedx)"
            echo "  --server           Использовать Trivy-сервер"
            echo "  --server-url URL   URL Trivy-сервера (по умолчанию: http://localhost:4954)"
            exit 0
            ;;
        *) echo -e "${RED}Неизвестный параметр: $1${NC}"; exit 1 ;;
    esac
done

# ---- Проверка Trivy ----
check_trivy() {
    if command -v trivy &>/dev/null; then
        echo -e "${GREEN}[OK] Trivy найден: $(trivy --version 2>/dev/null | head -1)${NC}"
        return 0
    fi

    echo -e "${YELLOW}[WARN] Trivy не установлен. Установка...${NC}"
    if [[ "$(uname)" == "Linux" ]]; then
        curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
    elif [[ "$(uname)" == "Darwin" ]]; then
        brew install trivy
    else
        echo -e "${RED}[ERROR] Автоустановка недоступна для этой ОС. Установите Trivy вручную:${NC}"
        echo "  https://aquasecurity.github.io/trivy/latest/getting-started/installation/"
        exit 1
    fi
}

# ---- Получение списка образов ----
get_compose_images() {
    cd "$PROJECT_ROOT"
    # Извлекаем уникальные image: строки из docker-compose.yml
    docker compose config --images 2>/dev/null | sort -u || \
        grep -E '^\s+image:' docker-compose.yml | awk '{print $2}' | sort -u
}

# ---- Сканирование одного образа ----
scan_image() {
    local image="$1"
    local safe_name
    safe_name=$(echo "$image" | tr '/:' '_')
    local report_file="${REPORTS_DIR}/${safe_name}"
    local exit_code=0

    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}[SCAN] Сканирование: ${image}${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Подтянуть образ если нужно
    if ! docker image inspect "$image" &>/dev/null; then
        echo -e "${YELLOW}[WAIT] Загрузка образа: ${image}${NC}"
        docker pull "$image" 2>/dev/null || {
            echo -e "${RED}[ERROR] Не удалось загрузить образ: ${image}${NC}"
            return 1
        }
    fi

    # Базовые аргументы Trivy
    local trivy_args=(
        image
        --severity "CRITICAL,HIGH,MEDIUM"
        --ignore-unfixed
    )

    # Конфиг-файл
    if [[ -f "$TRIVY_CONFIG" ]]; then
        trivy_args+=(--config "$TRIVY_CONFIG")
    fi

    # Файл игнорирования
    if [[ -f "$TRIVYIGNORE" ]]; then
        trivy_args+=(--ignorefile "$TRIVYIGNORE")
    fi

    # Использовать сервер
    if [[ "$USE_SERVER" == true ]]; then
        trivy_args+=(--server "$TRIVY_SERVER_URL")
    fi

    # 1) Отчёт в консоль (table or user-specified format)
    echo -e "${BLUE}[REPORT] Отчёт уязвимостей (формат: ${OUTPUT_FORMAT}):${NC}"
    trivy "${trivy_args[@]}" --format "${OUTPUT_FORMAT}" "$image" || true

    # 2) JSON-отчёт
    echo -e "${BLUE}[SAVE] Сохранение JSON-отчёта: ${report_file}.vuln.json${NC}"
    trivy "${trivy_args[@]}" --format json --output "${report_file}.vuln.json" "$image" || true

    # 3) SARIF-отчёт (для GitHub Security)
    echo -e "${BLUE}[SAVE] Сохранение SARIF-отчёта: ${report_file}.sarif${NC}"
    trivy "${trivy_args[@]}" --format sarif --output "${report_file}.sarif" "$image" || true

    # 4) Проверка на блокировку
    echo -e "${BLUE}[CHECK] Проверка блокировки (fail-on: ${FAIL_ON}):${NC}"
    if ! trivy "${trivy_args[@]}" --format table --exit-code 1 --severity "$FAIL_ON" "$image"; then
        echo -e "${RED}[BLOCK] Найдены уязвимости уровня ${FAIL_ON} и выше в ${image}${NC}"
        exit_code=1
    else
        echo -e "${GREEN}[PASS] Нет блокирующих уязвимостей уровня ${FAIL_ON}${NC}"
    fi

    # 5) SBOM
    if [[ "$GENERATE_SBOM" == true ]]; then
        generate_sbom "$image" "$safe_name"
    fi

    # 6) Prometheus-метрики
    generate_metrics "$image" "$safe_name"

    return $exit_code
}

# ---- Генерация SBOM ----
generate_sbom() {
    local image="$1"
    local safe_name="$2"

    echo -e "\n${BLUE}[SBOM] Генерация SBOM для: ${image}${NC}"

    # CycloneDX
    local cdx_file="${SBOM_DIR}/${safe_name}.cdx.json"
    echo -e "${BLUE}  → CycloneDX: ${cdx_file}${NC}"
    trivy image --format cyclonedx --output "$cdx_file" "$image" 2>/dev/null || {
        echo -e "${YELLOW}  [WARN] Ошибка генерации CycloneDX SBOM${NC}"
    }

    # SPDX
    local spdx_file="${SBOM_DIR}/${safe_name}.spdx.json"
    echo -e "${BLUE}  → SPDX: ${spdx_file}${NC}"
    trivy image --format spdx-json --output "$spdx_file" "$image" 2>/dev/null || {
        echo -e "${YELLOW}  [WARN] Ошибка генерации SPDX SBOM${NC}"
    }

    echo -e "${GREEN}  [OK] SBOM сгенерирован${NC}"
}

# ---- Генерация Prometheus-метрик ----
generate_metrics() {
    local image="$1"
    local safe_name="$2"
    local json_file="${REPORTS_DIR}/${safe_name}.vuln.json"
    local metrics_file="${REPORTS_DIR}/${safe_name}_metrics.prom"

    if [[ ! -f "$json_file" ]]; then
        return
    fi

    # Парсим JSON и считаем уязвимости по серьёзности
    python3 - "$json_file" "$image" "$metrics_file" << 'PYEOF'
import json
import sys

json_file, image, metrics_file = sys.argv[1], sys.argv[2], sys.argv[3]

try:
    with open(json_file) as f:
        data = json.load(f)
except Exception:
    sys.exit(0)

counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
total_packages = 0
results = data.get("Results", [])

for result in results:
    vulns = result.get("Vulnerabilities") or []
    total_packages += len(result.get("Packages") or [])
    for v in vulns:
        sev = v.get("Severity", "UNKNOWN").upper()
        counts[sev] = counts.get(sev, 0) + 1

total_vulns = sum(counts.values())
safe_image = image.replace('"', '\\"')

lines = [
    f'# HELP trivy_image_vulnerabilities Количество уязвимостей в образе',
    f'# TYPE trivy_image_vulnerabilities gauge',
]
for sev, count in counts.items():
    lines.append(f'trivy_image_vulnerabilities{{image="{safe_image}",severity="{sev.lower()}"}} {count}')

lines.extend([
    f'# HELP trivy_image_vulnerability_total Общее количество уязвимостей',
    f'# TYPE trivy_image_vulnerability_total gauge',
    f'trivy_image_vulnerability_total{{image="{safe_image}"}} {total_vulns}',
    f'# HELP trivy_image_packages_total Общее количество пакетов',
    f'# TYPE trivy_image_packages_total gauge',
    f'trivy_image_packages_total{{image="{safe_image}"}} {total_packages}',
])

with open(metrics_file, "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"  [METRICS] {metrics_file} (total={total_vulns}, critical={counts['CRITICAL']}, high={counts['HIGH']})")
PYEOF
}

# ---- Итоговый отчёт ----
print_summary() {
    local total="$1"
    local failed="$2"
    local passed=$((total - failed))

    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}[SUMMARY] ИТОГО: ${total} образов просканировано${NC}"
    echo -e "${GREEN}  [PASS] Прошли: ${passed}${NC}"
    if [[ $failed -gt 0 ]]; then
        echo -e "${RED}  [BLOCK] Заблокированы: ${failed}${NC}"
    fi
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  Отчёты:  ${REPORTS_DIR}/"
    if [[ "$GENERATE_SBOM" == true ]]; then
        echo -e "  SBOM:    ${SBOM_DIR}/"
    fi
    echo ""
}

# ---- main ----
main() {
    check_trivy

    mkdir -p "$REPORTS_DIR" "$SBOM_DIR"

    local total=0
    local failed=0

    if [[ "$SCAN_ALL" == true ]]; then
        echo -e "${BLUE}[INFO] Получение списка образов из docker-compose.yml...${NC}"
        local images
        images=$(get_compose_images)
        local count
        count=$(echo "$images" | wc -l)
        echo -e "${BLUE}   Найдено образов: ${count}${NC}"

        while IFS= read -r image; do
            [[ -z "$image" ]] && continue
            total=$((total + 1))
            if ! scan_image "$image"; then
                failed=$((failed + 1))
            fi
        done <<< "$images"

    elif [[ -n "$SCAN_IMAGE" ]]; then
        total=1
        if ! scan_image "$SCAN_IMAGE"; then
            failed=1
        fi
    else
        echo -e "${RED}Укажите --all или --image IMAGE${NC}"
        exit 1
    fi

    print_summary "$total" "$failed"

    if [[ $failed -gt 0 ]]; then
        exit 1
    fi
}

main "$@"
