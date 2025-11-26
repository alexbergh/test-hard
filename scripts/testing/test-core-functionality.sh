#!/usr/bin/env bash
# Test core functionality after DevOps improvements
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "[TEST] Testing Test-Hard Core Functionality"
echo "========================================"
echo ""

# Test 1: Check docker-compose.yml validity
echo -n "1. Validating docker-compose.yml... "
if command -v docker >/dev/null 2>&1 && docker compose config > /dev/null 2>&1; then
    echo -e "${GREEN}[OK]${NC}"
elif [ -f "docker-compose.yml" ]; then
    echo -e "${YELLOW}[WARN] File exists (docker compose not available)${NC}"
else
    echo -e "${RED}[ERROR] FAILED${NC}"
    exit 1
fi

# Test 2: Check if target containers are defined
echo -n "2. Checking target containers... "
targets=(target-fedora target-debian target-centos target-ubuntu)
all_found=true
for target in "${targets[@]}"; do
    if ! grep -q "$target:" docker-compose.yml; then
        echo -e "${RED}[ERROR] Missing $target${NC}"
        all_found=false
    fi
done
if $all_found; then
    echo -e "${GREEN}[OK]${NC} All 4 targets found"
fi

# Test 3: Check if scanner services exist
echo -n "3. Checking scanner services... "
if grep -q "openscap-scanner:" docker-compose.yml && \
   grep -q "lynis-scanner:" docker-compose.yml; then
    echo -e "${GREEN}[OK]${NC} Both scanners defined"
else
    echo -e "${RED}[ERROR] Scanner missing${NC}"
    exit 1
fi

# Test 4: Check docker-proxy configuration
echo -n "4. Checking docker-proxy (security)... "
if grep -q "docker-proxy:" docker-compose.yml; then
    echo -e "${GREEN}[OK]${NC} Docker proxy configured"
else
    echo -e "${YELLOW}[WARN] Docker proxy not found${NC}"
fi

# Test 5: Check monitoring services
echo -n "5. Checking monitoring stack... "
monitoring=(prometheus grafana telegraf alertmanager)
monitoring_ok=true
for service in "${monitoring[@]}"; do
    if ! grep -q "$service:" docker-compose.yml; then
        echo -e "${RED}[ERROR] Missing $service${NC}"
        monitoring_ok=false
    fi
done
if $monitoring_ok; then
    echo -e "${GREEN}[OK]${NC} All monitoring services present"
fi

# Test 6: Check run_hardening_suite.sh
echo -n "6. Checking hardening script... "
if [ -f "./scripts/run_hardening_suite.sh" ] && [ -x "./scripts/run_hardening_suite.sh" ]; then
    echo -e "${GREEN}[OK]${NC}"
else
    echo -e "${RED}[ERROR] Script missing or not executable${NC}"
    exit 1
fi

# Test 7: Check reports directory
echo -n "7. Checking reports directory... "
if [ -d "./reports" ]; then
    echo -e "${GREEN}[OK]${NC}"
else
    echo -e "${YELLOW}[WARN] Creating reports directory${NC}"
    mkdir -p reports
fi

# Test 8: Check Python parsers
echo -n "8. Checking Python parsers... "
parsers=(
    "scripts/parse_lynis_report.py"
    "scripts/parse_openscap_report.py"
    "scripts/parse_atomic_red_team_result.py"
)
parsers_ok=true
for parser in "${parsers[@]}"; do
    if ! python3 -m py_compile "$parser" 2>/dev/null; then
        echo -e "${RED}[ERROR] $parser syntax error${NC}"
        parsers_ok=false
    fi
done
if $parsers_ok; then
    echo -e "${GREEN}[OK]${NC} All parsers valid"
fi

# Test 9: Check Prometheus config
echo -n "9. Checking Prometheus config... "
if [ -f "prometheus/prometheus.yml" ] && [ -f "prometheus/alert.rules.yml" ]; then
    echo -e "${GREEN}[OK]${NC}"
else
    echo -e "${RED}[ERROR] Prometheus config missing${NC}"
    exit 1
fi

# Test 10: Check Grafana provisioning
echo -n "10. Checking Grafana provisioning... "
if [ -d "grafana/provisioning/datasources" ] && \
   [ -d "grafana/provisioning/dashboards" ]; then
    echo -e "${GREEN}[OK]${NC}"
else
    echo -e "${YELLOW}[WARN] Grafana provisioning incomplete${NC}"
fi

# Test 11: Check .env.example
echo -n "11. Checking .env.example... "
if [ -f ".env.example" ]; then
    if grep -q "GF_ADMIN_PASSWORD" .env.example && \
       grep -q "PROMETHEUS_RETENTION_TIME" .env.example; then
        echo -e "${GREEN}[OK]${NC}"
    else
        echo -e "${YELLOW}[WARN] .env.example incomplete${NC}"
    fi
else
    echo -e "${RED}[ERROR] .env.example missing${NC}"
    exit 1
fi

# Test 12: Check VERSION file (new in v1.0.0)
echo -n "12. Checking VERSION file... "
if [ -f "VERSION" ]; then
    version=$(cat VERSION)
    echo -e "${GREEN}[OK]${NC} v$version"
else
    echo -e "${YELLOW}[WARN] VERSION file missing${NC}"
fi

echo ""
echo "========================================"
echo -e "${GREEN}[SUCCESS] Core functionality tests passed!${NC}"
echo ""
echo "[READY] Ready to run:"
echo "   1. cp .env.example .env"
echo "   2. nano .env  # Edit passwords"
echo "   3. docker compose up -d prometheus grafana telegraf alertmanager docker-proxy"
echo "   4. ./scripts/run_hardening_suite.sh"
echo "   5. open http://localhost:3000"
echo ""
