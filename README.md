# test-hard — Monitoring/Hardening Demo

## Цель
Преобразованный репозиторий поднимает демонстрационную среду мониторинга на базе Prometheus и Grafana, хранит эталонные конфигурации Osquery и Telegraf и включает скрипты для интеграции результатов Lynis, OpenSCAP и Atomic Red Team.

## Быстрый старт
```bash
cp .env.example .env
# при необходимости измените GF_ADMIN_USER/GF_ADMIN_PASSWORD
docker compose up -d
```

* Prometheus: http://localhost:9090
* Grafana: http://localhost:3000 (учётные данные из `.env`)

## Настройка агентов
1. Установите Osquery и Telegraf на целевых хостах.
2. Примените конфигурацию из `telegraf/telegraf.conf` — она открывает эндпоинт `/metrics` на порту `9091` и может выполнять осмысленные запросы Osquery через `[[inputs.exec]]`.
3. В файле `prometheus/prometheus.yml` замените `<host-ip>` на адреса хостов с Telegraf (например, `host.docker.internal:9091` на Docker Desktop или IP-адрес сервера).

## Интеграция hardening-инструментов
Каталог `scripts/` содержит вспомогательные обёртки:

* `run_lynis.sh` и `parse_lynis_report.py` — запускают аудит Lynis и выводят метрики (`lynis_score`, `lynis_warnings_count`, `lynis_suggestions_count`).
* `run_openscap.sh` и `parse_openscap_report.py` — выполняют профиль OpenSCAP и подсчитывают количество правил по статусам (`openscap_pass_count`, `openscap_fail_count`, ...).
* `run_atomic_red_team_test.sh` и `parse_atomic_red_team_result.py` — помогают фиксировать бинарный результат атомарных тестов Atomic Red Team (`art_test_result`).

Настройте периодический запуск (cron/systemd timers/Ansible) и сбор метрик через `[[inputs.exec]]`, `[[inputs.file]]` или `[[inputs.socket_listener]]` в Telegraf.

## Дашборды Grafana
Файлы JSON с дашбордами поместите в `grafana/provisioning/dashboards/` — Grafana автоматически подхватит их при старте согласно `grafana/provisioning/dashboards/default.yml`.

## Структура репозитория
```
test-hard/
├── .env.example               # Пример переменных окружения Grafana
├── docker-compose.yml         # Prometheus и Grafana
├── grafana/
│   └── provisioning/
│       ├── dashboards/
│       │   └── default.yml    # Автоматическая загрузка дашбордов
│       └── datasources/
│           └── prometheus.yml # Datasource Grafana → Prometheus
├── osquery/
│   ├── osquery.conf
│   ├── osquery.yaml
│   └── pack.conf
├── prometheus/
│   └── prometheus.yml
├── scripts/
│   ├── parse_atomic_red_team_result.py
│   ├── parse_lynis_report.py
│   ├── parse_openscap_report.py
│   ├── run_atomic_red_team_test.sh
│   ├── run_lynis.sh
│   └── run_openscap.sh
├── telegraf/
│   └── telegraf.conf
└── Makefile                   # Упрощённые команды docker compose
```

## Makefile
```bash
make up      # docker compose up -d
make down    # docker compose down
make logs    # docker compose logs -f --tail=200
make restart # перезапуск стека
```

## Дальнейшие идеи
* Добавьте правила alerting и Alertmanager в Prometheus.
* Расширьте Telegraf дополнительными входными плагинами (cpu, disk, net и т.д.).
* Интегрируйте реальные сценарии Atomic Red Team и храните результаты в отдельном хранилище.
