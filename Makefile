COMPOSE ?= docker compose
PYTHON ?= python3

TARGET_SERVICES = target-fedora target-debian target-centos target-ubuntu
SCANNER_SERVICES = openscap-scanner lynis-scanner
MONITORING_SERVICES = docker-proxy prometheus alertmanager grafana telegraf

.PHONY: up up-targets monitor down logs restart hardening-suite scan clean check-deps health validate test

up:
	$(COMPOSE) up -d $(TARGET_SERVICES) $(SCANNER_SERVICES) $(MONITORING_SERVICES)

up-targets:
	$(COMPOSE) up -d $(TARGET_SERVICES) $(SCANNER_SERVICES)

monitor:
	$(COMPOSE) up -d $(MONITORING_SERVICES)

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=200

restart: down up

hardening-suite:
	./scripts/run_hardening_suite.sh

scan:
	$(COMPOSE) run --rm openscap-scanner
	$(COMPOSE) run --rm lynis-scanner

clean:
	rm -rf reports/*
	mkdir -p reports

check-deps:
	@echo "Checking dependencies..."
	@command -v docker >/dev/null 2>&1 || { echo "Error: docker not found"; exit 1; }
	@command -v $(COMPOSE) >/dev/null 2>&1 || { echo "Error: docker compose not found"; exit 1; }
	@command -v $(PYTHON) >/dev/null 2>&1 || { echo "Error: python3 not found"; exit 1; }
	@echo "✓ All dependencies found"

health:
	@echo "Checking service health..."
	@$(COMPOSE) ps
	@echo ""
	@echo "Prometheus health:"
	@curl -sf http://localhost:9090/-/healthy || echo "✗ Prometheus unhealthy"
	@echo "Grafana health:"
	@curl -sf http://localhost:3000/api/health || echo "✗ Grafana unhealthy"
	@echo "Telegraf metrics:"
	@curl -sf http://localhost:9091/metrics | head -5 || echo "✗ Telegraf unhealthy"

validate:
	@echo "Validating configurations..."
	@$(COMPOSE) config >/dev/null && echo "✓ docker-compose.yml valid" || echo "✗ docker-compose.yml invalid"
	@$(PYTHON) -c "import yaml; yaml.safe_load(open('prometheus/prometheus.yml'))" && echo "✓ prometheus.yml valid" || echo "✗ prometheus.yml invalid"
	@$(PYTHON) -c "import yaml; yaml.safe_load(open('prometheus/alert.rules.yml'))" && echo "✓ alert.rules.yml valid" || echo "✗ alert.rules.yml invalid"
	@test -f .env || echo "⚠ .env file not found - using defaults"

test:
	@echo "Running basic tests..."
	@$(PYTHON) -m py_compile scripts/*.py && echo "✓ Python scripts syntax OK" || echo "✗ Python syntax errors"
	@bash -n scripts/*.sh && echo "✓ Shell scripts syntax OK" || echo "✗ Shell syntax errors"

setup:
	@echo "Initial setup..."
	@test -f .env || { cp .env.example .env && echo "✓ Created .env from .env.example"; }
	@mkdir -p reports art-storage/history art-storage/prometheus
	@echo "✓ Setup complete"
