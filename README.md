# test-hard — Платформа Security Hardening & Monitoring

![CI Status](https://github.com/alexbergh/test-hard/workflows/CI%20Pipeline/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![Kubernetes](https://img.shields.io/badge/kubernetes-ready-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)


## Цель
Автоматизированная платформа для security hardening и мониторинга контейнеров. Включает security сканирование (OpenSCAP, Lynis), мониторинг (Prometheus, Grafana), атомарные тесты (Atomic Red Team) и сбор метрик безопасности через Telegraf.

## Возможности

* **Security Scanning** — автоматическое сканирование контейнеров (OpenSCAP, Lynis)
* **Monitoring Stack** — Prometheus + Grafana + Alertmanager для визуализации метрик безопасности
* **Centralized Logging** — Loki + Promtail для централизованного сбора и анализа логов
* **Atomic Red Team** — тестирование техник MITRE ATT&CK в режиме dry-run
* **GitOps Deployment** — автоматический deployment с ArgoCD
* **Container Registry** — автоматическая публикация образов в GitHub Container Registry
* **Multi-Environment** — поддержка dev/staging/prod через Docker Compose
* **CI/CD Ready** — GitHub Actions для автоматического тестирования и сканирования
* **Multi-Distribution** — сканирование Debian, Ubuntu, Fedora, CentOS Stream
* **Metrics Collection** — Telegraf для сбора и экспорта метрик в Prometheus
* **Docker Security** — изолированный доступ к Docker API через security proxy
* **High Test Coverage** — 80%+ покрытие тестами (unit, integration, E2E, shell)

## Быстрый старт

### Для нового хоста:
См. **[docs/QUICKSTART.md](docs/QUICKSTART.md)** для быстрого развертывания (5-10 минут)

### Для разработки:
```bash
# (опционально) создайте .env, чтобы переопределить учетные данные Grafana
cp .env.example .env
# можно пропустить этот шаг — docker compose использует admin/admin по умолчанию
make up
```

### Документация:
- **[Быстрый старт](docs/QUICKSTART.md)** - развертывание за 5-10 минут
- **[Полное руководство](docs/DEPLOYMENT.md)** - детальная инструкция с troubleshooting
- **[Сканирование реальных хостов](docs/REAL-HOSTS-SCANNING.md)** - как сканировать production серверы, VM и Docker контейнеры ⭐

### Режимы работы

**1. Тестовые контейнеры (по умолчанию)** - для демонстрации и разработки
**2. Реальные хосты через SSH** - для production серверов и VM
**3. Production Docker контейнеры** - через Docker API

Подробнее: [docs/REAL-HOSTS-SCANNING.md](docs/REAL-HOSTS-SCANNING.md)

### Автоматические сканы контейнеров (режим 1)

В корне репозитория добавлен отдельный `docker-compose.yml`, который поднимает четыре тестовых
контейнера (Fedora, Debian, CentOS Stream, Ubuntu) и два сервисных сканера (OpenSCAP и Lynis).
Все сканы выполняются через Docker API, а отчёты складываются в `./reports/`.

```bash
make up                # поднимает целевые контейнеры, мониторинг и собирает образы сканеров
make up-with-logging   # запуск с centralized logging (Loki + Promtail)
make up-targets        # только целевые контейнеры и сканеры без мониторинга
make monitor           # Prometheus + Alertmanager + Grafana + Telegraf
make logging           # только Loki + Promtail
make scan              # запускает OpenSCAP и Lynis внутри сервисных контейнеров
make help              # показать все доступные команды
```

* OpenSCAP сохраняет как HTML-, так и XML-отчёты в `reports/openscap/`.
* Lynis устанавливается внутрь целевых контейнеров и выгружает журналы в `reports/lynis/`.

После завершения можно остановить инфраструктуру `make down` и очистить отчёты `make clean`.

* Prometheus: http://localhost:9090
* Alertmanager: http://localhost:9093
* Grafana: http://localhost:3000 (учётные данные из `.env`)

## Демонстрационная мультидистрибутивная среда

В каталоге `docker/` подготовлены Dockerfile'ы для Debian, Ubuntu, Fedora и CentOS Stream. Контейнеры
собираются через общий `docker-compose.yml` и монтируют каталоги `scripts/`, `atomic-red-team/` и `art-storage/`, чтобы использовать
одинаковые сценарии hardening-аудита.

```bash
# сборка и запуск всех контейнеров + выполнение проверок внутри
./scripts/run_hardening_suite.sh

# только перечислить доступные сервисы
./scripts/run_hardening_suite.sh --list
```

По умолчанию проверки Atomic Red Team выполняются в режиме dry-run (`ATOMIC_DRY_RUN=true`). Чтобы запускать реальные техники,
установите переменную окружения при запуске `docker compose`, например: `ATOMIC_DRY_RUN=false docker compose up`. Для немедленного запуска
проверок при старте контейнера добавьте `RUN_HARDENING_ON_START=true`.

По умолчанию `docker-compose.yml` и `scripts/run_hardening_suite.sh` запускают дистрибутивы с публично доступными образами
(Debian, Ubuntu, Fedora, CentOS).

## Alerting
Prometheus загружает правила из `prometheus/alert.rules.yml` и пересылает сработавшие оповещения в Alertmanager.
Настройте webhook в `prometheus/alertmanager.yml`, чтобы направлять уведомления в нужную систему (Grafana, Slack, PagerDuty и т.д.).

## Настройка агентов
1. В составе `make up` автоматически поднимается контейнер `telegraf`, который использует конфигурацию из `telegraf/telegraf.conf` и публикует метрики на `http://localhost:9091/metrics`.
2. При необходимости разверните Telegraf на реальных хостах, используя тот же конфигурационный файл, и обновите `prometheus/prometheus.yml`, добавив адреса ваших агентов вместо внутреннего сервиса `telegraf:9091`.

## Интеграция hardening-инструментов
Каталог `scripts/` содержит вспомогательные обёртки:

* `run_lynis.sh` и `parse_lynis_report.py` — запускают аудит Lynis и выводят метрики (`lynis_score`, `lynis_warnings_count`, `lynis_suggestions_count`).
* `run_openscap.sh` и `parse_openscap_report.py` — выполняют профиль OpenSCAP и подсчитывают количество правил по статусам (`openscap_pass_count`, `openscap_fail_count`, ...). Если парсеру не передать путь до ARF-файла, он попытается взять самый свежий отчёт из каталога `${HARDENING_RESULTS_DIR:-/var/lib/hardening/results}/openscap`.
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

### Диагностика 401 при обращении к Grafana API

`401 Unauthorized` чаще всего появляется, когда вы попадаете не в тот экземпляр Grafana — например, порт `3000` уже занят другой
службой, и браузер/API-клиент стучится не в контейнер из этого compose-файла. Прежде чем сбрасывать пароли, выполните последовательность
проверок:

1. **Убедитесь, что порт 3000 не занят чужой Grafana.**
   ```bash
   docker ps --filter "publish=3000" --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}'
   sudo ss -tulpn | grep ':3000'           # или lsof -iTCP:3000 -sTCP:LISTEN
   ```
   Если в выводе видны другие контейнеры или процессы, либо версию `/api/health` отвечает не `11.0.0`, остановите конфликтующий сервис
   или смените порт в `.env` (`GRAFANA_HOST_PORT=3300`) и перезапустите `docker compose`.
2. **Проверьте, что работает именно нужный контейнер.**
   ```bash
   docker compose ps grafana
   docker compose exec grafana grafana-cli -v
   docker compose exec grafana env | grep '^GF_'
   ```
   Так вы увидите имя контейнера, версию Grafana и актуальные переменные окружения.
3. **Убедитесь, что не отключены basic-auth и форма логина.** В `docker-compose.yml` заданы переменные
   `GF_AUTH_BASIC_ENABLED=true` и `GF_AUTH_DISABLE_LOGIN_FORM=false`. При необходимости переопределите их в `.env` перед запуском.
4. **Перезапустите контейнер после изменения настроек или порта.**
   ```bash
   docker compose up -d grafana
   ```

При включённом [provisioning](grafana/provisioning/datasources/prometheus.yml) стандартный datasource Prometheus создаётся
автоматически без дополнительных запросов к API.

## Структура репозитория
```
test-hard/
├── .env.example               # Пример переменных окружения Grafana
├── docker-compose.yml         # Prometheus, Grafana и доступные агенты
├── docker/
│   ├── common/                # Общие entrypoint-скрипты для агентов
│   ├── debian/                # Dockerfile для Debian 12
│   ├── ubuntu/                # Dockerfile для Ubuntu 22.04
│   ├── fedora/                # Dockerfile для Fedora 39
│   └── centos/                # Dockerfile для CentOS Stream 9
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
│   ├── run_all_checks.sh
│   ├── run_atomic_red_team_test.sh
│   ├── run_hardening_suite.sh
│   ├── run_lynis.sh
│   └── run_openscap.sh
├── art-storage/               # Хранилище результатов Atomic Red Team (latest.json, history/, prometheus/)
│   └── results/               # Метрики и итоги комплексных проверок
├── telegraf/
│   └── telegraf.conf
└── Makefile                   # Упрощённые команды docker compose
```

## Makefile
```bash
make up          # полный стек (целевые контейнеры, мониторинг, сканеры)
make up-targets  # только целевые контейнеры и сканеры
make monitor     # Prometheus + Alertmanager + Grafana + Telegraf
make down        # docker compose down
make logs        # docker compose logs -f --tail=200
make restart     # перезапуск стека
```

## Документация

**Полная документация доступна в каталоге [`docs/`](docs/)**:

* **[Quick Start Guide](docs/QUICK-USAGE.md)** — быстрое руководство по запуску
* **[Security Scanning](docs/README-SECURITY-SCANNING.md)** — подробное описание security сканирования
* **[Troubleshooting](docs/TROUBLESHOOTING.md)** — решение проблем
* **[User Guide](docs/USER-GUIDE.md)** — полное руководство пользователя
* **[Changelog](docs/CHANGELOG.md)** — история изменений
* **[Security Policy](docs/SECURITY.md)** — политика безопасности

## Тестирование

```bash
# Запустить полный набор тестов (unit + integration)
make test

# Только unit тесты
make test-unit

# Только integration тесты
make test-integration

# Проверить покрытие кода
make test-coverage
```

## CI/CD

Проект включает GitHub Actions workflows:

* **Security Scanning** — автоматическое сканирование при каждом push
* **Docker Build** — проверка сборки образов
* **Pytest Tests** — запуск unit и integration тестов
* **Secret Scanning** — поиск случайно закоммиченных секретов

## Kubernetes

Manifests для развертывания в Kubernetes доступны в `k8s/`:

```bash
# Deploy в dev окружение
kubectl apply -k k8s/overlays/dev

# Deploy в production
kubectl apply -k k8s/overlays/prod
```

## 🆕 Новые возможности (Октябрь 2025)

### Centralized Logging
- **Loki** для хранения логов
- **Promtail** для сбора логов из контейнеров
- **LogQL** для мощного поиска и анализа
- Готовый дашборд для анализа логов
- Документация: [docs/LOGGING.md](docs/LOGGING.md)

### GitOps Deployment
- **ArgoCD** для автоматического deployment
- Автоматическая синхронизация для dev/staging
- Ручное подтверждение для production
- Rollback support
- Документация: [argocd/README.md](argocd/README.md)

### Container Registry
- Автоматическая публикация в **GitHub Container Registry**
- Image signing с Cosign
- Multi-platform builds (amd64, arm64)
- Семантическое версионирование

### Расширенное тестирование
- **80%+ test coverage**
- Unit, integration, E2E тесты
- Shell script тесты с bats
- Kubernetes deployment тесты
- Coverage reporting

## 🗺️ План развития

**Статус проекта:** Production Ready (9.0/10)  
**Test Coverage:** 80%+

Полный план развития на 2026 год:
- **[ROADMAP.md](ROADMAP.md)** - детальный roadmap с задачами по кварталам

### Ближайшие задачи (Q1 2026)
* Web UI для управления сканированиями
* Scheduled scanning
* Distributed tracing с Grafana Tempo

### Среднесрочные (Q2-Q3 2026)
* Runtime security с Falco
* Compliance as Code (InSpec, OPA)
* ML-based anomaly detection
* Multi-tenancy support

### Долгосрочные (Q4 2026)
* Multi-cloud support (AWS, Azure, GCP)
* Advanced reporting и analytics
* Integration marketplace
