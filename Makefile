.PHONY: up down logs restart hardening-suite

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

restart: down up

hardening-suite:
	./scripts/run_hardening_suite.sh
