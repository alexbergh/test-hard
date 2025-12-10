.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help

COMPOSE ?= docker compose
PYTHON ?= python3

TARGET_SERVICES = target-fedora target-debian target-centos target-ubuntu
SCANNER_SERVICES = openscap-scanner lynis-scanner
MONITORING_SERVICES = docker-proxy prometheus alertmanager grafana telegraf loki promtail

.PHONY: up up-targets monitor down logs restart hardening-suite scan clean check-deps health validate test \
	test-unit test-integration test-all coverage install-dev ci lint format build push run-lynis run-openscap run-all

# Build unified image
build: ## Build unified test-hard Docker image
	docker build -t test-hard:latest -t ghcr.io/alexbergh/test-hard:latest .

# Push unified image to registry
push: build ## Build and push unified image to GitHub Container Registry
	docker push ghcr.io/alexbergh/test-hard:latest

# Run specific scanners using unified image
run-lynis: ## Run Lynis scanner using unified image
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/reports:/opt/test-hard/reports \
		ghcr.io/alexbergh/test-hard:latest scan-lynis

run-openscap: ## Run OpenSCAP scanner using unified image
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/reports:/opt/test-hard/reports \
		ghcr.io/alexbergh/test-hard:latest scan-openscap

run-all: ## Run all scanners using unified image
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/reports:/opt/test-hard/reports \
		ghcr.io/alexbergh/test-hard:latest scan-all

run-atomic: ## Run Atomic Red Team tests using unified image
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/reports:/opt/test-hard/reports \
		-v $(PWD)/art-storage:/var/lib/hardening/art-storage \
		ghcr.io/alexbergh/test-hard:latest atomic --dry-run

up: ## Start all services (targets, scanners, monitoring)
	$(COMPOSE) up -d $(TARGET_SERVICES) $(SCANNER_SERVICES) $(MONITORING_SERVICES)

up-targets: ## Start only target containers and scanners
	$(COMPOSE) up -d $(TARGET_SERVICES) $(SCANNER_SERVICES)

monitor: ## Start monitoring stack (Prometheus, Grafana, etc)
	$(COMPOSE) up -d $(MONITORING_SERVICES)

up-with-logging: ## Start all services with centralized logging (Loki)
	$(COMPOSE) -f docker-compose.yml -f docker-compose.logging.yml up -d

logging: ## Start only logging stack (Loki, Promtail)
	$(COMPOSE) -f docker-compose.yml -f docker-compose.logging.yml up -d loki promtail

up-with-tracing: ## Start all services with distributed tracing (Tempo)
	$(COMPOSE) -f docker-compose.yml -f docker-compose.tracing.yml up -d

tracing: ## Start only tracing stack (Tempo)
	$(COMPOSE) -f docker-compose.yml -f docker-compose.tracing.yml up -d tempo

dashboard: ## Start dashboard (backend + frontend)
	$(COMPOSE) -f dashboard/docker-compose.yml up -d

dashboard-dev: ## Start dashboard in development mode
	cd dashboard/backend && uvicorn app.main:app --reload &
	cd dashboard/frontend && npm run dev

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=200

restart: down up

hardening-suite:
	./scripts/scanning/run_hardening_suite.sh

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
	@./scripts/monitoring/health_check.sh

validate:
	@echo "Validating configurations..."
	@$(COMPOSE) config >/dev/null && echo "✓ docker-compose.yml valid" || echo "✗ docker-compose.yml invalid"
	@$(PYTHON) -c "import yaml; yaml.safe_load(open('prometheus/prometheus.yml'))" && echo "✓ prometheus.yml valid" || echo "✗ prometheus.yml invalid"
	@$(PYTHON) -c "import yaml; yaml.safe_load(open('prometheus/alert.rules.yml'))" && echo "✓ alert.rules.yml valid" || echo "✗ alert.rules.yml invalid"
	@test -f .env || echo "⚠ .env file not found - using defaults"

test:
	@echo "Running basic tests..."
	@find scripts -name "*.py" -exec $(PYTHON) -m py_compile {} \; && echo "✓ Python scripts syntax OK" || echo "✗ Python syntax errors"
	@find scripts -name "*.sh" -exec bash -n {} \; && echo "✓ Shell scripts syntax OK" || echo "✗ Shell syntax errors"

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

test-unit: ## Run unit tests
	@echo "Running unit tests..."
	@$(PYTHON) -m pytest tests/unit/ -v

test-integration: ## Run integration tests
	@echo "Running integration tests..."
	@$(PYTHON) -m pytest tests/integration/ -v -m integration

test-e2e: ## Run end-to-end tests
	@echo "Running E2E tests..."
	@$(PYTHON) -m pytest tests/e2e/ -v -m e2e

test-shell: ## Run shell script tests with bats
	@echo "Running shell tests..."
	@./scripts/testing/run_shell_tests.sh

test-all: ## Run all tests (unit, integration, shell)
	@echo "Running all tests..."
	@$(PYTHON) -m pytest tests/unit/ tests/integration/ -v
	@./scripts/testing/run_shell_tests.sh

test-full: ## Run full test suite including E2E
	@echo "Running full test suite..."
	@$(PYTHON) -m pytest tests/ -v -m ""
	@./scripts/testing/run_shell_tests.sh

coverage: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	@$(PYTHON) -m pytest tests/unit/ tests/integration/ -v --cov=scripts --cov-report=html --cov-report=term --cov-report=xml
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
	@./scripts/utils/bump-version.sh patch

bump-minor:
	@echo "Bumping minor version..."
	@./scripts/utils/bump-version.sh minor

bump-major:
	@echo "Bumping major version..."
	@./scripts/utils/bump-version.sh major

# Backup and restore
backup: ## Create backup of configuration and data
	@echo "Creating backup..."
	@./scripts/backup/backup.sh

# Security checks
security: ## Run security checks on configuration
	@echo "Running security checks..."
	@./scripts/testing/verify_fixes.sh
	@echo "Checking for secrets in code..."
	@git secrets --scan || echo "⚠ git-secrets not installed"

# Validation helpers
validate-all: validate ## Comprehensive validation of all configs
	@echo "Validating YAML files..."
	@yamllint . || echo "⚠ yamllint not installed"
	@echo "Validating shell scripts..."
	@shellcheck scripts/**/*.sh || echo "⚠ shellcheck not installed"
	@echo "Validating Dockerfiles..."
	@hadolint docker/Dockerfile.* || echo "⚠ hadolint not installed"

# Docker optimization
docker-measure: ## Measure Docker image sizes and build times
	@./scripts/monitoring/measure_docker_improvements.sh

docker-prune: ## Clean up Docker resources
	@echo "Cleaning Docker resources..."
	@docker system prune -a --volumes
	docker builder prune -a

# Status and info
status: ## Show detailed status of all services
	@echo "=== Service Status ==="
	@$(COMPOSE) ps
	@echo ""
	@echo "=== Resource Usage ==="
	@docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
	@echo ""
	@echo "=== Disk Usage ==="
	@docker system df

metrics: ## Show current metrics from Prometheus
	@echo "=== Prometheus Metrics ==="
	@curl -s http://localhost:9090/api/v1/label/__name__/values | jq -r '.data[]' | grep security | head -10
	@echo ""
	@echo "=== Telegraf Metrics ==="
	@curl -s http://localhost:9091/metrics | grep security_scanners | head -10

# Documentation
docs-serve: ## Serve documentation locally
	@echo "Serving documentation at http://localhost:8000"
	@$(PYTHON) -m http.server 8000 --directory docs

# Development helpers
dev-install: install-dev ## Alias for install-dev

dev-shell: ## Open shell in development environment
	@$(COMPOSE) exec prometheus sh

pre-commit-all: ## Run pre-commit on all files
	@pre-commit run --all-files

# Cleanup targets
clean-all: clean ## Clean everything including volumes
	@echo "Cleaning all data..."
	@$(COMPOSE) down -v
	@rm -rf prometheus-data grafana-data
	@echo "✓ All data cleaned"

clean-reports: ## Clean only report files
	@rm -rf reports/*
	@mkdir -p reports
	@echo "✓ Reports cleaned"

clean-cache: ## Clean Docker build cache
	@docker builder prune -a -f
	@echo "✓ Build cache cleaned"

# Troubleshooting
troubleshoot: ## Run diagnostic commands
	@echo "=== Docker Version ==="
	@docker --version
	@docker compose version
	@echo ""
	@echo "=== Python Version ==="
	@$(PYTHON) --version
	@echo ""
	@echo "=== Services Status ==="
	@make status
	@echo ""
	@echo "=== Recent Logs ==="
	@$(COMPOSE) logs --tail=50

diagnostics: ## Create diagnostic bundle
	@echo "Creating diagnostic bundle..."
	@mkdir -p diagnostics
	@$(COMPOSE) ps > diagnostics/ps.txt 2>&1
	@$(COMPOSE) logs > diagnostics/logs.txt 2>&1
	@docker stats --no-stream > diagnostics/stats.txt 2>&1
	@docker system df > diagnostics/df.txt 2>&1
	@cp docker-compose.yml diagnostics/ 2>&1
	@tar czf diagnostics-$(shell date +%Y%m%d).tar.gz diagnostics/
	@rm -rf diagnostics/
	@echo "✓ Diagnostic bundle created: diagnostics-$(shell date +%Y%m%d).tar.gz"
