#!/bin/bash
set -euo pipefail

# Health check script for all services
set -e

echo "🏥 Checking services health..."
echo ""

# Prometheus
if curl -sf http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "✓ Prometheus: healthy"
else
    echo "✗ Prometheus: unhealthy"
    exit 1
fi

# Grafana
if curl -sf http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✓ Grafana: healthy"
else
    echo "✗ Grafana: unhealthy"
    exit 1
fi

# Telegraf
if curl -sf http://localhost:9091/metrics > /dev/null 2>&1; then
    echo "✓ Telegraf: healthy"
else
    echo "✗ Telegraf: unhealthy"
    exit 1
fi

# Alertmanager
if curl -sf http://localhost:9093/-/healthy > /dev/null 2>&1; then
    echo "✓ Alertmanager: healthy"
else
    echo "✗ Alertmanager: unhealthy"
    exit 1
fi

echo ""
echo "✅ All services are healthy!"
