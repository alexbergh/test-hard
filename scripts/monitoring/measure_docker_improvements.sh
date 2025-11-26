#!/bin/bash
# Script for measuring improvements after Docker image optimization

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "Docker Optimization Metrics"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to format size in MB
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

echo -e "${BLUE}1. Docker Image Sizes${NC}"
echo "----------------------------------------"

# List of images to check
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

echo -e "${BLUE}2. BuildKit Cache Statistics${NC}"
echo "----------------------------------------"
if command -v docker &> /dev/null && docker buildx version &> /dev/null 2>&1; then
    docker buildx du || echo "BuildKit cache info unavailable"
else
    echo "Docker Buildx not installed"
fi
echo ""

echo -e "${BLUE}3. Docker System Information${NC}"
echo "----------------------------------------"
docker system df
echo ""

echo -e "${BLUE}4. Image Layers (examples)${NC}"
echo "----------------------------------------"

# Show layers for several images
for image in "test-hard/ubuntu:latest" "test-hard/telegraf:latest"; do
    if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "$image"; then
        echo ""
        echo -e "${YELLOW}Layers for $image:${NC}"
        docker history "$image" --format "table {{.CreatedBy}}\t{{.Size}}" --no-trunc=false | head -n 10
    fi
done
echo ""

echo -e "${BLUE}5. Health Check Statuses${NC}"
echo "----------------------------------------"
printf "%-30s %20s\n" "CONTAINER" "HEALTH STATUS"
printf "%-30s %20s\n" "---------" "-------------"

# Check healthcheck for running containers
if docker ps --format "{{.Names}}" | grep -q .; then
    for container in $(docker ps --format "{{.Names}}"); do
        health=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no healthcheck")
        printf "%-30s %20s\n" "$container" "$health"
    done
else
    echo "No running containers"
fi
echo ""

echo -e "${BLUE}6. Recommendations${NC}"
echo "----------------------------------------"

# Check BuildKit usage
if ! grep -q "DOCKER_BUILDKIT" ~/.bashrc 2>/dev/null && ! grep -q "DOCKER_BUILDKIT" ~/.zshrc 2>/dev/null; then
    echo -e "${YELLOW}[WARN] BuildKit not set in shell profile${NC}"
    echo "   Add to ~/.bashrc or ~/.zshrc:"
    echo "   export DOCKER_BUILDKIT=1"
    echo ""
fi

# Check cache size
cache_size=$(docker system df --format "{{.BuildCache}}" | awk '{print $1}')
if [ -n "$cache_size" ]; then
    cache_num=$(format_size "$cache_size")
    if (( $(echo "$cache_num > 5000" | bc -l) )); then
        echo -e "${YELLOW}[WARN] Build cache takes a lot of space: $cache_size${NC}"
        echo "   Consider cleanup: docker builder prune"
        echo ""
    fi
fi

# Check unused images
unused=$(docker images -f "dangling=true" -q | wc -l)
if [ "$unused" -gt 0 ]; then
    echo -e "${YELLOW}[WARN] Found $unused dangling images${NC}"
    echo "   Cleanup: docker image prune"
    echo ""
fi

echo -e "${GREEN}[OK] Analysis complete${NC}"
echo ""

# Optional benchmark comparison
if [ -f "$PROJECT_DIR/benchmark_sizes.txt" ]; then
    echo -e "${BLUE}7. Benchmark Comparison${NC}"
    echo "----------------------------------------"
    echo "Benchmark file: $PROJECT_DIR/benchmark_sizes.txt"
    echo "TODO: Implement benchmark comparison"
    echo ""
fi

echo "To save current sizes as benchmark:"
echo "  docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep test-hard > benchmark_sizes.txt"
echo ""
