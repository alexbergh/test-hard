# test-hard — Monitoring & Hardening Demo

Этот репозиторий разворачивает демонстрационную среду мониторинга, которая заменяет стэк Wazuh/ELK на более лёгкую связку Prometheus + Grafana. На целевых хостах работают агенты Osquery и Telegraf, а скрипты в каталоге `scripts/` помогают интегрировать результаты Lynis, OpenSCAP и Atomic Red Team в метрики.

## Шаги развёртывания

1. **Подготовьте переменные окружения.**
   ```bash
   cp .env.example .env
   # при необходимости измените GF_ADMIN_USER/GF_ADMIN_PASSWORD
   ```

2. **Поднимите центральные сервисы мониторинга.**
   ```bash
   docker compose up -d
   ```
   * Prometheus: http://localhost:9090
   * Grafana: http://localhost:3000 (логин/пароль из `.env`).

3. **Настройте агентов.**
   * Установите Osquery и Telegraf на необходимые хосты.
   * Примените эталонный конфиг `telegraf/telegraf.conf` — он открывает `/metrics` на порту `9091` и периодически запускает osquery-запросы через `inputs.exec`.
   * Обновите `prometheus/prometheus.yml`, указав корректные адреса Telegraf (`host.docker.internal:9091`, IP хоста или `network_mode: host`).

4. **Интегрируйте инструменты аудита.**
   В каталоге `scripts/` лежат готовые обёртки:
   * `run_lynis.sh` — запускает `lynis audit system` и выводит `lynis_score`, `lynis_warnings_count`, `lynis_suggestions_count`.
   * `run_openscap.sh` / `parse_openscap_report.py` — выполняют SCAP-профиль и подсчитывают количество правил по статусам (`openscap_pass`, `openscap_fail` и т.д.).
   * `run_atomic_red_team_test.sh` / `parse_atomic_red_team_result.py` — заглушки для запуска Atomic Red Team и преобразования результатов в метрики `art_test_result`.

   Настройте периодический запуск (cron/systemd timers/Ansible) и сбор метрик через `inputs.exec` или `inputs.file` Telegraf.

5. **Добавьте дашборды.**
   Поместите JSON-экспорты Grafana в `grafana/dashboards/` — они подхватятся автоматически благодаря провижинингу (`grafana/provisioning/dashboards/default.yml`).

## Структура репозитория

```
test-hard/
├── .env.example               # Пример переменных окружения Grafana
├── docker-compose.yml         # Prometheus и Grafana
├── grafana/
│   ├── dashboards/            # JSON-дэшборды Grafana
│   └── provisioning/
│       ├── dashboards/
│       │   └── default.yml    # Автоматическая загрузка дэшбордов
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
└── Makefile                   # Утилиты запуска docker compose
```

## Makefile

Для удобства можно использовать цели:

```bash
make up      # docker compose up -d
make down    # docker compose down
make logs    # tail -f логов
make restart # перезапуск стека
```

## Дальнейшие шаги

* Дополните Prometheus правилом alerting и Alertmanager.
* Расширьте конфиги Telegraf дополнительными входными плагинами.
* Добавьте реальные сценарии запуска Atomic Red Team и парсинг артефактов.
