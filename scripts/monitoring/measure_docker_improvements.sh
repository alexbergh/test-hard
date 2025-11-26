#!/bin/bash
# РЎРєСЂРёРїС‚ РґР»СЏ РёР·РјРµСЂРµРЅРёСЏ СѓР»СѓС‡С€РµРЅРёР№ РїРѕСЃР»Рµ РѕРїС‚РёРјРёР·Р°С†РёРё Docker РѕР±СЂР°Р·РѕРІ

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "Docker Optimization Metrics"
echo "======================================"
echo ""

# Р¦РІРµС‚Р° РґР»СЏ РІС‹РІРѕРґР°
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Р¤СѓРЅРєС†РёСЏ РґР»СЏ С„РѕСЂРјР°С‚РёСЂРѕРІР°РЅРёСЏ СЂР°Р·РјРµСЂР° РІ MB
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

echo -e "${BLUE}1. Р Р°Р·РјРµСЂС‹ Docker РѕР±СЂР°Р·РѕРІ${NC}"
echo "----------------------------------------"

# РЎРїРёСЃРѕРє РѕР±СЂР°Р·РѕРІ РґР»СЏ РїСЂРѕРІРµСЂРєРё
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

echo -e "${BLUE}2. BuildKit Cache СЃС‚Р°С‚РёСЃС‚РёРєР°${NC}"
echo "----------------------------------------"
if command -v docker &> /dev/null && docker buildx version &> /dev/null 2>&1; then
    docker buildx du || echo "BuildKit cache info РЅРµРґРѕСЃС‚СѓРїРЅР°"
else
    echo "Docker Buildx РЅРµ СѓСЃС‚Р°РЅРѕРІР»РµРЅ"
fi
echo ""

echo -e "${BLUE}3. Docker System РёРЅС„РѕСЂРјР°С†РёСЏ${NC}"
echo "----------------------------------------"
docker system df
echo ""

echo -e "${BLUE}4. РЎР»РѕРё РѕР±СЂР°Р·РѕРІ (РїСЂРёРјРµСЂС‹)${NC}"
echo "----------------------------------------"

# РџРѕРєР°Р·С‹РІР°РµРј СЃР»РѕРё РґР»СЏ РЅРµСЃРєРѕР»СЊРєРёС… РѕР±СЂР°Р·РѕРІ
for image in "test-hard/ubuntu:latest" "test-hard/telegraf:latest"; do
    if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "$image"; then
        echo ""
        echo -e "${YELLOW}РЎР»РѕРё РґР»СЏ $image:${NC}"
        docker history "$image" --format "table {{.CreatedBy}}\t{{.Size}}" --no-trunc=false | head -n 10
    fi
done
echo ""

echo -e "${BLUE}5. Health Check СЃС‚Р°С‚СѓСЃС‹${NC}"
echo "----------------------------------------"
printf "%-30s %20s\n" "CONTAINER" "HEALTH STATUS"
printf "%-30s %20s\n" "---------" "-------------"

# РџСЂРѕРІРµСЂРєР° healthcheck РґР»СЏ Р·Р°РїСѓС‰РµРЅРЅС‹С… РєРѕРЅС‚РµР№РЅРµСЂРѕРІ
if docker ps --format "{{.Names}}" | grep -q .; then
    for container in $(docker ps --format "{{.Names}}"); do
        health=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no healthcheck")
        printf "%-30s %20s\n" "$container" "$health"
    done
else
    echo "РќРµС‚ Р·Р°РїСѓС‰РµРЅРЅС‹С… РєРѕРЅС‚РµР№РЅРµСЂРѕРІ"
fi
echo ""

echo -e "${BLUE}6. Р РµРєРѕРјРµРЅРґР°С†РёРё${NC}"
echo "----------------------------------------"

# РџСЂРѕРІРµСЂРєР° РёСЃРїРѕР»СЊР·РѕРІР°РЅРёСЏ BuildKit
if ! grep -q "DOCKER_BUILDKIT" ~/.bashrc 2>/dev/null && ! grep -q "DOCKER_BUILDKIT" ~/.zshrc 2>/dev/null; then
    echo -e "${YELLOW}[WARN] BuildKit РЅРµ СѓСЃС‚Р°РЅРѕРІР»РµРЅ РІ shell profile${NC}"
    echo "   Р”РѕР±Р°РІСЊС‚Рµ РІ ~/.bashrc РёР»Рё ~/.zshrc:"
    echo "   export DOCKER_BUILDKIT=1"
    echo ""
fi

# РџСЂРѕРІРµСЂРєР° СЂР°Р·РјРµСЂР° cache
cache_size=$(docker system df --format "{{.BuildCache}}" | awk '{print $1}')
if [ -n "$cache_size" ]; then
    cache_num=$(format_size "$cache_size")
    if (( $(echo "$cache_num > 5000" | bc -l) )); then
        echo -e "${YELLOW}[WARN] Build cache Р·Р°РЅРёРјР°РµС‚ РјРЅРѕРіРѕ РјРµСЃС‚Р°: $cache_size${NC}"
        echo "   Р Р°СЃСЃРјРѕС‚СЂРёС‚Рµ РѕС‡РёСЃС‚РєСѓ: docker builder prune"
        echo ""
    fi
fi

# РџСЂРѕРІРµСЂРєР° РЅРµРёСЃРїРѕР»СЊР·СѓРµРјС‹С… РѕР±СЂР°Р·РѕРІ
unused=$(docker images -f "dangling=true" -q | wc -l)
if [ "$unused" -gt 0 ]; then
    echo -e "${YELLOW}[WARN] РќР°Р№РґРµРЅРѕ $unused dangling РѕР±СЂР°Р·РѕРІ${NC}"
    echo "   РћС‡РёСЃС‚РєР°: docker image prune"
    echo ""
fi

echo -e "${GREEN}[OK] РђРЅР°Р»РёР· Р·Р°РІРµСЂС€РµРЅ${NC}"
echo ""

# РћРїС†РёРѕРЅР°Р»СЊРЅРѕРµ СЃСЂР°РІРЅРµРЅРёРµ СЃ Р±РµРЅС‡РјР°СЂРєРѕРј
if [ -f "$PROJECT_DIR/benchmark_sizes.txt" ]; then
    echo -e "${BLUE}7. РЎСЂР°РІРЅРµРЅРёРµ СЃ benchmark${NC}"
    echo "----------------------------------------"
    echo "Benchmark С„Р°Р№Р»: $PROJECT_DIR/benchmark_sizes.txt"
    echo "TODO: Implement benchmark comparison"
    echo ""
fi

echo "Р”Р»СЏ СЃРѕС…СЂР°РЅРµРЅРёСЏ С‚РµРєСѓС‰РёС… СЂР°Р·РјРµСЂРѕРІ РєР°Рє benchmark:"
echo "  docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep test-hard > benchmark_sizes.txt"
echo ""
