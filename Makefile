COMPOSE ?= docker compose

.PHONY: up down logs restart hardening-suite scan clean

up:
$(COMPOSE) up -d

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
