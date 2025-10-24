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
* Alertmanager: http://localhost:9093
* Grafana: http://localhost:3000 (учётные данные из `.env`)

## Alerting
Prometheus загружает правила из `prometheus/alert.rules.yml` и пересылает сработавшие оповещения в Alertmanager.
Настройте webhook в `prometheus/alertmanager.yml`, чтобы направлять уведомления в нужную систему (Grafana, Slack, PagerDuty и т.д.).

## Настройка агентов
1. Установите Osquery и Telegraf на целевых хостах.
2. Примените конфигурацию из `telegraf/telegraf.conf` — она открывает эндпоинт `/metrics` на порту `9091` и может выполнять осмысленные запросы Osquery через `[[inputs.exec]]`.
3. В файле `prometheus/prometheus.yml` замените `<host-ip>` на адреса хостов с Telegraf (например, `host.docker.internal:9091` на Docker Desktop или IP-адрес сервера).

## Интеграция hardening-инструментов
Каталог `scripts/` содержит вспомогательные обёртки:

* `run_lynis.sh` и `parse_lynis_report.py` — запускают аудит Lynis и выводят метрики (`lynis_score`, `lynis_warnings_count`, `lynis_suggestions_count`).
* `run_openscap.sh` и `parse_openscap_report.py` — выполняют профиль OpenSCAP и подсчитывают количество правил по статусам (`openscap_pass_count`, `openscap_fail_count`, ...).
* `run_atomic_red_team_test.sh` и `parse_atomic_red_team_result.py` — запускают реальные сценарии Atomic Red Team и преобразуют результаты (`art_test_result`, `art_scenario_status`, `art_summary_total`).

Настройте периодический запуск (cron/systemd timers/Ansible) и сбор метрик через `[[inputs.exec]]`, `[[inputs.file]]` или `[[inputs.socket_listener]]` в Telegraf.

### Atomic Red Team сценарии

* Каталог `atomic-red-team/` содержит файл `scenarios.yaml` с готовыми наборами атомарных тестов для Linux и Windows (например, `T1082`, `T1049`, `T1119`).
* Скрипт `scripts/run_atomic_red_team_suite.py` использует [atomic-operator](https://github.com/redcanaryco/atomic-operator) для скачивания/обновления репозитория Atomic Red Team, исполнения сценариев и сохранения структурированных отчётов.
* Результаты складываются в отдельное хранилище `art-storage/`:
  * `art-storage/history/<timestamp>.json` — архив выполнений;
  * `art-storage/latest.json` и `art-storage/latest.prom` — последний запуск;
  * `art-storage/prometheus/art_results.prom` — метрики в формате Prometheus для прямого экспорта.

#### Запуск

```bash
pip install atomic-operator attrs click pyyaml
./scripts/run_atomic_red_team_test.sh                # выполняет сценарии из atomic-red-team/scenarios.yaml
./scripts/run_atomic_red_team_test.sh T1082 run      # точечный запуск техники T1082
./scripts/run_atomic_red_team_test.sh --mode prereqs # загрузка зависимостей без выполнения
```

Скрипт автоматически скачивает (или обновляет) репозиторий Atomic Red Team в `~/.cache/atomic-red-team`, либо принимает путь через `--atomics-path`.

#### Интеграция с Telegraf

Добавьте во входные плагины Telegraf (путь скорректируйте под свою установку):

```toml
[[inputs.exec]]
  commands = [
    "python3 /opt/hardening/scripts/parse_atomic_red_team_result.py /var/lib/atomic-results/latest.json"
  ]
  timeout = "10s"
  data_format = "prometheus"
  name_suffix = "_atomic"
  interval = "60s"
```

Где `/var/lib/atomic-results` — примонтированное хранилище с содержимым каталога `art-storage/`.

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
├── atomic-red-team/
│   └── scenarios.yaml         # Подготовленные сценарии Atomic Red Team
├── prometheus/
│   ├── alert.rules.yml
│   ├── alertmanager.yml
│   └── prometheus.yml
├── scripts/
│   ├── parse_atomic_red_team_result.py
│   ├── parse_lynis_report.py
│   ├── parse_openscap_report.py
│   ├── run_atomic_red_team_test.sh
│   ├── run_lynis.sh
│   └── run_openscap.sh
├── art-storage/               # Хранилище результатов Atomic Red Team (latest.json, history/, prometheus/)
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
* Настройте интеграцию Alertmanager с выбранной системой уведомлений.
* Расширьте Telegraf дополнительными входными плагинами (cpu, disk, net и т.д.).
* Интегрируйте реальные сценарии Atomic Red Team и храните результаты в отдельном хранилище.
