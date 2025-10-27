COMPOSE ?= docker compose

TARGET_SERVICES = target-fedora target-debian target-centos target-ubuntu
SCANNER_SERVICES = openscap-scanner lynis-scanner
MONITORING_SERVICES = prometheus alertmanager grafana telegraf

.PHONY: up up-targets monitor down logs restart hardening-suite scan clean

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
