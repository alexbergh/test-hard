# Docker test harness

`docker-compose.yml` агрегирует пилотные сервисы и упрощает запуск интеграционных тестов:

- `openscap-runner` выполняет локальный OVAL-скан и складывает результаты в `artifacts/openscap`.
- `influxdb`, `telegraf-listener`, `grafana` формируют телеметрический пайплайн для проверки пакетов osquery.
- `osquery-simulator` периодически отправляет события на Telegraf по HTTP и UDP.
- `wazuh-*` поднимают менеджер, индексатор и дашборд Wazuh вместе с агентом, который регистрируется автоматически.

Перед запуском убедитесь, что Docker Engine поддерживает Compose V2 (`docker compose`).

```bash
# поднять телеметрию и wazuh в фоне
./run.sh all

# остановить и удалить контейнеры
docker compose -f docker-compose.yml --profile openscap --profile telemetry --profile wazuh down
```

Артефакты сохраняются в `tests/docker/artifacts` (игнорируются git).
