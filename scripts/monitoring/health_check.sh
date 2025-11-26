#!/bin/bash
set -euo pipefail

# Health check script for all services
set -e

echo "[HEALTH] Checking services health..."
echo ""

# Prometheus
if curl -sf http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "[OK] Prometheus: healthy"
else
    echo "[ERROR] Prometheus: unhealthy"
    exit 1
fi

# Grafana
if curl -sf http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "[OK] Grafana: healthy"
else
    echo "[ERROR] Grafana: unhealthy"
    exit 1
fi

# Telegraf
if curl -sf http://localhost:9091/metrics > /dev/null 2>&1; then
    echo "[OK] Telegraf: healthy"
else
    echo "[ERROR] Telegraf: unhealthy"
    exit 1
fi

# Alertmanager
if curl -sf http://localhost:9093/-/healthy > /dev/null 2>&1; then
    echo "[OK] Alertmanager: healthy"
else
    echo "[ERROR] Alertmanager: unhealthy"
    exit 1
fi

echo ""
echo "[SUCCESS] All services are healthy!"
