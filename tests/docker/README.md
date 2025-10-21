# Docker test harness

`docker-compose.yml` агрегирует пилотные сервисы и упрощает запуск интеграционных тестов:

- `openscap-runner` выполняет локальный OVAL-скан и складывает результаты в `artifacts/openscap`.
- `influxdb`, `telegraf-listener`, `grafana` формируют телеметрический пайплайн для проверки пакетов osquery.
- `kuma-mock` эмулирует приёмник KUMA и сохраняет батчи телеметрии для последующего анализа.
- `osquery-simulator` периодически отправляет события на Telegraf по HTTP и UDP.
- `wazuh-*` поднимают менеджер, индексатор и дашборд Wazuh вместе с агентом, который регистрируется автоматически.

Перед запуском убедитесь, что Docker Engine поддерживает Compose V2 (`docker compose`). Если Docker недоступен (например, в CI),
скрипт `run.sh` автоматически переключится на оффлайн-симуляцию, подготовит базу ФСТЭК через `prepare_fstec_content.py` и сгенерирует примерные отчёты в каталоге `artifacts/`. Учебный архив `scanoval.zip` формируется на лету утилитой `tests/tools/create_sample_fstec_archive.py`, поэтому бинарные файлы не хранятся в репозитории.

```bash
# поднять телеметрию и wazuh в фоне
./run.sh all

# однократный запуск OpenSCAP (контейнер или симуляция)
./run.sh openscap

# остановить и удалить контейнеры (актуально, когда Docker доступен)
docker compose -f docker-compose.yml --profile openscap --profile telemetry --profile wazuh down
```

Артефакты сохраняются в `tests/docker/artifacts` (игнорируются git). В режиме симуляции формируются JSON/текстовые логи для всех профилей, а также готовые заготовки:

- `telemetry/hardening-dashboard.md` — Markdown-панель с визуализацией и ASCII-графиками по критичности.
- `telemetry/grafana-dashboard.json` — экспорт готового дашборда Grafana, использующего InfluxDB.
- `telemetry/kuma-payload.json` и `telemetry/collector.log` — батч и журнал условного коллектора для передачи в KUMA.

Эти артефакты формируются как при работе настоящих контейнеров, так и в режиме оффлайн-симуляции.
