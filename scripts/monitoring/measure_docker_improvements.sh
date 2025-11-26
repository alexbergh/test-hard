#!/bin/bash
# Скрипт для измерения улучшений после оптимизации Docker образов

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "Docker Optimization Metrics"
echo "======================================"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для форматирования размера в MB
format_size() {
    local size=$1
    if [[ $size == *"GB"* ]]; then
        size=$(echo "$size" | sed 's/GB//' | awk '{print $1 * 1024}')
    elif [[ $size == *"MB"* ]]; then
        size=${size//MB/}
    elif [[ $size == *"KB"* ]]; then
        size=$(echo "$size" | sed 's/KB//' | awk '{print $1 / 1024}')
    fi
    echo "$size"
}

echo -e "${BLUE}1. Размеры Docker образов${NC}"
echo "----------------------------------------"

# Список образов для проверки
IMAGES=(
    "test-hard/ubuntu"
    "test-hard/debian"
    "test-hard/fedora"
    "test-hard/centos"
    "test-hard/altlinux"
    "test-hard/openscap-scanner"
    "test-hard/lynis-scanner"
    "test-hard/telegraf"
)

total_size=0
image_count=0

printf "%-30s %15s\n" "IMAGE" "SIZE"
printf "%-30s %15s\n" "-----" "----"

for image in "${IMAGES[@]}"; do
    if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "$image"; then
        size=$(docker images --format "{{.Size}}" "$image:latest" 2>/dev/null || echo "N/A")
        printf "%-30s %15s\n" "$image" "$size"
        
        if [ "$size" != "N/A" ]; then
            size_mb=$(format_size "$size")
            total_size=$(echo "$total_size + $size_mb" | bc)
            ((image_count++))
        fi
    fi
done

echo "----------------------------------------"
printf "%-30s %15s\n" "TOTAL ($image_count images)" "${total_size}MB"
echo ""

echo -e "${BLUE}2. BuildKit Cache статистика${NC}"
echo "----------------------------------------"
if command -v docker &> /dev/null && docker buildx version &> /dev/null 2>&1; then
    docker buildx du || echo "BuildKit cache info недоступна"
else
    echo "Docker Buildx не установлен"
fi
echo ""

echo -e "${BLUE}3. Docker System информация${NC}"
echo "----------------------------------------"
docker system df
echo ""

echo -e "${BLUE}4. Слои образов (примеры)${NC}"
echo "----------------------------------------"

# Показываем слои для нескольких образов
for image in "test-hard/ubuntu:latest" "test-hard/telegraf:latest"; do
    if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "$image"; then
        echo ""
        echo -e "${YELLOW}Слои для $image:${NC}"
        docker history "$image" --format "table {{.CreatedBy}}\t{{.Size}}" --no-trunc=false | head -n 10
    fi
done
echo ""

echo -e "${BLUE}5. Health Check статусы${NC}"
echo "----------------------------------------"
printf "%-30s %20s\n" "CONTAINER" "HEALTH STATUS"
printf "%-30s %20s\n" "---------" "-------------"

# Проверка healthcheck для запущенных контейнеров
if docker ps --format "{{.Names}}" | grep -q .; then
    for container in $(docker ps --format "{{.Names}}"); do
        health=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no healthcheck")
        printf "%-30s %20s\n" "$container" "$health"
    done
else
    echo "Нет запущенных контейнеров"
fi
echo ""

echo -e "${BLUE}6. Рекомендации${NC}"
echo "----------------------------------------"

# Проверка использования BuildKit
if ! grep -q "DOCKER_BUILDKIT" ~/.bashrc 2>/dev/null && ! grep -q "DOCKER_BUILDKIT" ~/.zshrc 2>/dev/null; then
    echo -e "${YELLOW}[WARN] BuildKit не установлен в shell profile${NC}"
    echo "   Добавьте в ~/.bashrc или ~/.zshrc:"
    echo "   export DOCKER_BUILDKIT=1"
    echo ""
fi

# Проверка размера cache
cache_size=$(docker system df --format "{{.BuildCache}}" | awk '{print $1}')
if [ -n "$cache_size" ]; then
    cache_num=$(format_size "$cache_size")
    if (( $(echo "$cache_num > 5000" | bc -l) )); then
        echo -e "${YELLOW}[WARN] Build cache занимает много места: $cache_size${NC}"
        echo "   Рассмотрите очистку: docker builder prune"
        echo ""
    fi
fi

# Проверка неиспользуемых образов
unused=$(docker images -f "dangling=true" -q | wc -l)
if [ "$unused" -gt 0 ]; then
    echo -e "${YELLOW}[WARN] Найдено $unused dangling образов${NC}"
    echo "   Очистка: docker image prune"
    echo ""
fi

echo -e "${GREEN}[OK] Анализ завершен${NC}"
echo ""

# Опциональное сравнение с бенчмарком
if [ -f "$PROJECT_DIR/benchmark_sizes.txt" ]; then
    echo -e "${BLUE}7. Сравнение с benchmark${NC}"
    echo "----------------------------------------"
    echo "Benchmark файл: $PROJECT_DIR/benchmark_sizes.txt"
    echo "TODO: Implement benchmark comparison"
    echo ""
fi

echo "Для сохранения текущих размеров как benchmark:"
echo "  docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep test-hard > benchmark_sizes.txt"
echo ""
