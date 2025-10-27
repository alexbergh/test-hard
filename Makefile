COMPOSE ?= docker compose
PYTHON ?= python3

TARGET_SERVICES = target-fedora target-debian target-centos target-ubuntu
SCANNER_SERVICES = openscap-scanner lynis-scanner
MONITORING_SERVICES = docker-proxy prometheus alertmanager grafana telegraf

.PHONY: up up-targets monitor down logs restart hardening-suite scan clean check-deps health validate test \
	test-unit test-integration test-all coverage install-dev ci lint format

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

install-dev:
	@echo "Installing development dependencies..."
	@$(PYTHON) -m pip install -r requirements.txt
	@pre-commit install
	@echo "✓ Development environment ready"

test-unit:
	@echo "Running unit tests..."
	@$(PYTHON) -m pytest tests/unit/ -v

test-integration:
	@echo "Running integration tests..."
	@$(PYTHON) -m pytest tests/integration/ -v -m integration

test-all:
	@echo "Running all tests..."
	@$(PYTHON) -m pytest tests/ -v

coverage:
	@echo "Running tests with coverage..."
	@$(PYTHON) -m pytest tests/ -v --cov=scripts --cov-report=html --cov-report=term
	@echo "Coverage report: htmlcov/index.html"

lint:
	@echo "Running linters..."
	@$(PYTHON) -m flake8 scripts/ tests/
	@$(PYTHON) -m black --check scripts/ tests/
	@$(PYTHON) -m isort --check-only scripts/ tests/

format:
	@echo "Formatting code..."
	@$(PYTHON) -m black scripts/ tests/
	@$(PYTHON) -m isort scripts/ tests/
	@echo "✓ Code formatted"

ci: lint test-all
	@echo "✓ CI checks passed"

# Environment-specific deployments
up-dev:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml up -d

up-staging:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.staging.yml up -d

up-prod:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml up -d

# Kubernetes deployment
k8s-dev:
	kubectl apply -k k8s/overlays/dev/

k8s-staging:
	kubectl apply -k k8s/overlays/staging/

k8s-prod:
	kubectl apply -k k8s/overlays/prod/

k8s-delete:
	kubectl delete -k k8s/overlays/dev/ --ignore-not-found=true

# Version management
version:
	@cat VERSION

bump-patch:
	@echo "Bumping patch version..."
	@./scripts/bump-version.sh patch

bump-minor:
	@echo "Bumping minor version..."
	@./scripts/bump-version.sh minor

bump-major:
	@echo "Bumping major version..."
	@./scripts/bump-version.sh major
