# test-hard — Платформа Security Hardening & Monitoring

![CI Status](https://github.com/alexbergh/test-hard/workflows/CI%20Pipeline/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)
![Podman](https://img.shields.io/badge/podman-ready-blue.svg)
![Kubernetes](https://img.shields.io/badge/kubernetes-ready-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)

## Цель

Автоматизированная платформа для security hardening, runtime-безопасности и мониторинга контейнеров. Включает security-сканирование (OpenSCAP, Lynis), runtime-защиту (Falco), сканирование образов (Trivy), мониторинг (Prometheus, Grafana), атомарные тесты (Atomic Red Team) и сбор метрик безопасности через Telegraf.

## Возможности

* **Security Scanning** — автоматическое сканирование контейнеров (OpenSCAP, Lynis)
* **Runtime Security** — Falco + Falcosidekick + автоматические реакции на угрозы
* **Container Image Scanning** — Trivy для сканирования уязвимостей + SBOM + OPA/Gatekeeper
* **Monitoring Stack** — Prometheus + Grafana + Alertmanager для визуализации метрик безопасности
* **Centralized Logging** — Loki + Promtail для централизованного сбора и анализа логов
* **Atomic Red Team** — тестирование техник MITRE ATT&CK в режиме dry-run
* **GitOps Deployment** — автоматический deployment с ArgoCD
* **Container Registry** — автоматическая публикация образов в GitHub Container Registry
* **Multi-Environment** — поддержка dev/staging/prod через Podman Compose
* **CI/CD Pipeline** — GitHub Actions (9 workflows) для тестирования, сканирования и блокировки
* **Multi-Distribution** — сканирование Debian, Ubuntu, Fedora, CentOS Stream, ALT Linux
* **Metrics Collection** — Telegraf для сбора и экспорта метрик в Prometheus
* **Podman Security** — изолированный доступ к Podman API через security proxy
* **Policy Enforcement** — OPA/Gatekeeper политики для Kubernetes
* **High Test Coverage** — 80%+ покрытие тестами (unit, integration, E2E, shell)

## Быстрый старт

### Для нового хоста

См. **[docs/QUICKSTART.md](docs/QUICKSTART.md)** для быстрого развертывания (5-10 минут)

### Для разработки

```bash
# (опционально) создайте .env, чтобы переопределить учетные данные Grafana
cp .env.example .env
# можно пропустить этот шаг — podman-compose использует admin/admin по умолчанию
make up
```

### Документация

**Основное:**

* **[Документация](docs/README.md)** - центральная страница документации
* **[Быстрый старт](docs/QUICKSTART.md)** - развертывание за 5-10 минут
* **[FAQ](docs/FAQ.md)** - часто задаваемые вопросы
* **[Troubleshooting](docs/TROUBLESHOOTING.md)** - устранение неполадок

**Развертывание:**

* **[Полное руководство](docs/DEPLOYMENT.md)** - детальная инструкция с troubleshooting
* **[Podman Quick Start](docs/PODMAN_QUICK_START.md)** — быстрое руководство по оптимизированным образам
* **[Нативная установка](docs/NATIVE-INSTALLATION.md)** — установка без Podman

**Безопасность:**

* **[Security Policy](docs/SECURITY.md)** - политика безопасности
* **[Создание пользователей](docs/USER-SETUP.md)** - безопасная настройка пользователей (полное руководство)
* **[Сканирование хостов](docs/REAL-HOSTS-SCANNING.md)** - как сканировать production серверы

**Дополнительно:**

* **[Podman оптимизации](docs/PODMAN_OPTIMIZATIONS.md)** — multi-stage builds, cache, метрики
* **[Централизованное логирование](docs/LOGGING.md)** - настройка Loki + Promtail

### Режимы работы

**1. Тестовые контейнеры (по умолчанию)** - для демонстрации и разработки
**2. Реальные хосты через SSH** - для production серверов и VM
**3. Production Podman контейнеры** — через Podman API

Подробнее: [docs/REAL-HOSTS-SCANNING.md](docs/REAL-HOSTS-SCANNING.md)

### Автоматические сканы контейнеров (режим 1)

В корне репозитория добавлен отдельный `podman-compose.yml`, который поднимает четыре тестовых
контейнера (Fedora, Debian, CentOS Stream, Ubuntu) и два сервисных сканера (OpenSCAP и Lynis).
Все сканы выполняются через Podman API, а отчёты складываются в `./reports/`.

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

* Prometheus: <http://localhost:9090>
* Alertmanager: <http://localhost:9093>
* Grafana: <http://localhost:3000> (учётные данные из `.env`)
* Falcosidekick: <http://localhost:2801>
* Trivy Server: <http://localhost:4954>
* Falco Responder: <http://localhost:5080>

## Демонстрационная мультидистрибутивная среда

В каталоге `containers/` подготовлены Containerfile'ы для Debian, Ubuntu, Fedora, CentOS Stream и ALT Linux. Контейнеры
собираются через общий `podman-compose.yml` и монтируют каталоги `scripts/`, `atomic-red-team/` и `art-storage/`, чтобы использовать
одинаковые сценарии hardening-аудита.

```bash
# сборка и запуск всех контейнеров + выполнение проверок внутри
./scripts/scanning/run_hardening_suite.sh

# только перечислить доступные сервисы
./scripts/scanning/run_hardening_suite.sh --list
```

По умолчанию проверки Atomic Red Team выполняются в режиме dry-run (`ATOMIC_DRY_RUN=true`). Чтобы запускать реальные техники,
установите переменную окружения при запуске `podman-compose`, например: `ATOMIC_DRY_RUN=false podman-compose up`. Для немедленного запуска
проверок при старте контейнера добавьте `RUN_HARDENING_ON_START=true`.

По умолчанию `podman-compose.yml` и `scripts/scanning/run_hardening_suite.sh` запускают дистрибутивы с публично доступными образами
(Debian, Ubuntu, Fedora, CentOS, ALT Linux).

## Alerting

Prometheus загружает правила из `prometheus/alert.rules.yml` и пересылает сработавшие оповещения в Alertmanager.
Настройте webhook в `prometheus/alertmanager.yml`, чтобы направлять уведомления в нужную систему (Grafana, Slack, PagerDuty и т.д.).

## Настройка агентов

1. В составе `make up` автоматически поднимается контейнер `telegraf`, который использует конфигурацию из `telegraf/telegraf.conf` и публикует метрики на `http://localhost:9091/metrics`.
2. При необходимости разверните Telegraf на реальных хостах, используя тот же конфигурационный файл, и обновите `prometheus/prometheus.yml`, добавив адреса ваших агентов вместо внутреннего сервиса `telegraf:9091`.

## Интеграция hardening-инструментов

Каталог `scripts/` содержит вспомогательные обёртки:

* `scripts/scanning/run_lynis.sh` и `scripts/parsing/parse_lynis_report.py` — запускают аудит Lynis и выводят метрики (`lynis_score`, `lynis_warnings_count`, `lynis_suggestions_count`).
* `scripts/scanning/run_openscap.sh` и `scripts/parsing/parse_openscap_report.py` — выполняют профиль OpenSCAP и подсчитывают количество правил по статусам (`openscap_pass_count`, `openscap_fail_count`, ...). Если парсеру не передать путь до ARF-файла, он попытается взять самый свежий отчёт из каталога `${HARDENING_RESULTS_DIR:-/var/lib/hardening/results}/openscap`.
* `scripts/scanning/run_atomic_red_team_test.sh` и `scripts/parsing/parse_atomic_red_team_result.py` — запускают реальные сценарии Atomic Red Team и преобразуют результаты (`art_test_result`, `art_scenario_status`, `art_summary_total`).

Настройте периодический запуск (cron/systemd timers/Ansible) и сбор метрик через `[[inputs.exec]]`, `[[inputs.file]]` или `[[inputs.socket_listener]]` в Telegraf.

### Atomic Red Team сценарии

* Каталог `atomic-red-team/` содержит файл `scenarios.yaml` с готовыми наборами атомарных тестов для Linux и Windows (например, `T1082`, `T1049`, `T1119`).
* Скрипт `scripts/scanning/run_atomic_red_team_suite.py` использует [atomic-operator](https://github.com/redcanaryco/atomic-operator) для скачивания/обновления репозитория Atomic Red Team, исполнения сценариев и сохранения структурированных отчётов.
* Результаты складываются в отдельное хранилище `art-storage/`:
  * `art-storage/history/<timestamp>.json` — архив выполнений;
  * `art-storage/latest.json` и `art-storage/latest.prom` — последний запуск;
  * `art-storage/prometheus/art_results.prom` — метрики в формате Prometheus для прямого экспорта.

#### Запуск

```bash
pip install atomic-operator attrs click pyyaml
./scripts/scanning/run_atomic_red_team_test.sh                # выполняет сценарии из atomic-red-team/scenarios.yaml
./scripts/scanning/run_atomic_red_team_test.sh T1082 run      # точечный запуск техники T1082
./scripts/scanning/run_atomic_red_team_test.sh --mode prereqs # загрузка зависимостей без выполнения
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

Дашборды автоматически загружаются из `grafana/dashboards/` при старте Grafana.

| Дашборд | Описание |
|----------|----------|
| **Security Overview** | Общий обзор безопасности: Lynis, OpenSCAP, Atomic Red Team |
| **Host Compliance** | Подробности соответствия по каждому хосту |
| **System Resources** | CPU, память, диск, сеть, процессы |
| **Security Issues Details** | Таблицы Lynis/OpenSCAP проблем |
| **Logs Analysis** | Анализ логов через Loki |
| **Falco Runtime Security** | Runtime-события Falco, правила, доставка через Falcosidekick |
| **Container Image Security** | Уязвимости образов Trivy, тренды, таблицы |
| **Network Security Monitoring** | Bandwidth, packets, errors/drops, TCP states, Falco network events |
| **Network Discovery** | Обнаруженные хосты, открытые порты, сервисы в Podman-сети |
| **Security Monitoring** | Метрики сканеров в динамике |

### Диагностика 401 при обращении к Grafana API

`401 Unauthorized` чаще всего появляется, когда вы попадаете не в тот экземпляр Grafana — например, порт `3000` уже занят другой
службой, и браузер/API-клиент стучится не в контейнер из этого compose-файла. Прежде чем сбрасывать пароли, выполните последовательность
проверок:

1. **Убедитесь, что порт 3000 не занят другой Grafana.**

   ```bash
   podman ps --filter "publish=3000" --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}'
   sudo ss -tulpn | grep ':3000'           # или lsof -iTCP:3000 -sTCP:LISTEN
   ```

   Если в выводе видны другие контейнеры или процессы, либо версию `/api/health` отвечает не `11.0.0`, остановите конфликтующий сервис
   или смените порт в `.env` (`GRAFANA_HOST_PORT=3300`) и перезапустите `podman-compose`.
2. **Проверьте, что работает именно нужный контейнер.**

   ```bash
   podman-compose ps grafana
   podman exec grafana grafana-cli -v
   podman exec grafana env | grep '^GF_'
   ```

   Так вы увидите имя контейнера, версию Grafana и актуальные переменные окружения.
3. **Убедитесь, что не отключены basic-auth и форма логина.** В `podman-compose.yml` заданы переменные
   `GF_AUTH_BASIC_ENABLED=true` и `GF_AUTH_DISABLE_LOGIN_FORM=false`. При необходимости переопределите их в `.env` перед запуском.
4. **Перезапустите контейнер после изменения настроек или порта.**

   ```bash
   podman-compose up -d grafana
   ```

При включённом [provisioning](grafana/provisioning/datasources/prometheus.yml) стандартный datasource Prometheus создаётся
автоматически без дополнительных запросов к API.

## Структура репозитория

```text
test-hard/
├── .env.example               # Переменные окружения
├── podman-compose.yml         # Все сервисы: мониторинг, сканеры, Falco, Trivy
├── Containerfile                 # Единый multi-stage образ
├── containers/                    # Dockerfiles для целевых ОС (Debian, Ubuntu, Fedora, CentOS, ALT)
├── falco/
│   ├── falco.yaml             # Конфигурация Falco
│   ├── falcosidekick.yaml     # Маршрутизация событий (Alertmanager, Loki, webhook)
│   ├── rules.d/               # Кастомные правила для hardening detection
│   └── responder/             # Автоматические реакции (kill, stop, isolate)
├── trivy/
│   ├── trivy.yaml             # Конфигурация Trivy
│   └── .trivyignore           # Игнорируемые CVE
├── grafana/
│   ├── dashboards/            # 10 преднастроенных дашбордов
│   └── provisioning/          # Datasources (Prometheus, Loki, Tempo)
├── prometheus/
│   ├── alert.rules.yml        # Правила алертинга (вкл. Falco)
│   ├── alertmanager.yml        # Маршрутизация алертов (вкл. Falco)
│   └── prometheus.yml         # Конфиг скрейпинга (Telegraf, Falco, Falcosidekick)
├── scripts/
│   ├── scanning/              # Сканирование: Lynis, OpenSCAP, ART, scan-images.sh
│   ├── parsing/               # Парсеры отчётов
│   └── setup/                 # Скрипты настройки
├── k8s/
│   ├── base/                  # Kustomize: Prometheus, Grafana, Telegraf, Falco, Gatekeeper
│   └── overlays/              # Оверлеи для dev/staging/prod
├── dashboard/
│   ├── backend/               # FastAPI backend (JWT, RBAC, SQLAlchemy)
│   └── frontend/              # React + TailwindCSS frontend
├── telegraf/
│   └── telegraf.conf          # Сбор метрик (system, Lynis, OpenSCAP, ART, Trivy)
└── Makefile                   # Упрощённые команды
```

## Makefile

```bash
make up          # полный стек (целевые контейнеры, мониторинг, сканеры)
make up-targets  # только целевые контейнеры и сканеры
make monitor     # Prometheus + Alertmanager + Grafana + Telegraf
make down        # podman-compose down
make logs        # podman-compose logs -f --tail=200
make restart     # перезапуск стека
```

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

Проект включает 9 GitHub Actions workflows:

* **CI Pipeline** — lint, валидация, unit/integration тесты, сборка
* **Security Scanning** — Trivy FS, Bandit, TruffleHog
* **Container Image Security** — сканирование образов, SBOM, блокировка уязвимых
* **Build and Push** — сборка, публикация в GHCR, Cosign signing, SBOM
* **CodeQL** — статический анализ кода
* **CD Pipeline** — деплой в staging/production
* **Podman Publish** — публикация Podman-образов
* **Hardening Suite** — запуск hardening-проверок
* **Dependency Update** — автообновление зависимостей

## Dashboard API

Платформа включает REST API для управления безопасностью:

### Аутентификация

```bash
# Получить JWT токен
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123!"}'
```

### Основные endpoints

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/v1/health` | GET | Проверка здоровья API |
| `/api/v1/auth/login` | POST | Аутентификация |
| `/api/v1/clusters` | GET/POST | Управление кластерами |
| `/api/v1/clusters/{id}/discover` | POST | Обнаружение контейнеров |
| `/api/v1/clusters/{id}/drift` | POST | Drift detection |
| `/api/v1/clusters/{id}/image-check` | POST | Проверка образов |
| `/api/v1/clusters/{id}/risk-score` | POST | Оценка рисков |
| `/api/v1/hosts` | GET | Список хостов/контейнеров |
| `/api/v1/scans` | GET/POST | Управление сканированиями |

### Создание Podman кластера

```bash
# Linux
curl -X POST http://localhost:8000/api/v1/clusters \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"local-podman","cluster_type":"podman","podman_host":"tcp://podman-proxy:2375"}'

# Windows (используйте host.containers.internal)
curl -X POST http://localhost:8000/api/v1/clusters \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"local-podman","cluster_type":"podman","podman_host":"tcp://host.containers.internal:2375"}'
```

### Учетные данные по умолчанию

* **Username:** `admin`
* **Password:** `admin123!`

## Kubernetes

Manifests для развертывания в Kubernetes доступны в `k8s/`:

```bash
# Deploy в dev окружение
kubectl apply -k k8s/overlays/dev

# Deploy в production
kubectl apply -k k8s/overlays/prod
```

## Runtime Security (Falco)

Платформа включает Falco для runtime-защиты контейнеров:

* **Falco** — мониторинг syscalls с 30+ кастомными правилами (7 категорий)
* **Falcosidekick** — маршрутизация событий в Alertmanager, Loki, webhook
* **Falco Exporter** — Prometheus-метрики через gRPC
* **Falco Responder** — автоматические реакции (kill, stop, isolate, pause)
* **10 Prometheus alert rules** для Falco-событий

Категории правил: целостность файлов, эскалация привилегий, безопасность контейнеров, сетевая безопасность, доступ к учётным данным, целостность ядра, фальсификация логов.

## Network Security Monitoring

* **NetworkPolicy** — 11 Kubernetes-политик (default-deny + per-service allow) для всех компонентов
* **Traffic Analysis** — мониторинг bandwidth, packets, errors, drops через Telegraf + Prometheus
* **Anomaly Detection** — 8 alert rules: traffic spikes, error rate, packet drops, connection count, TIME_WAIT, DNS query rate, Falco network events
* **TCP Connection Tracking** — Telegraf netstat для ESTABLISHED, TIME_WAIT, CLOSE_WAIT, SYN_RECV
* **Service Mesh** — Istio (mTLS, AuthorizationPolicy, DestinationRule с circuit breakers) и Linkerd (Server, ServerAuthorization)
* **Grafana Dashboard** — Network Security Monitoring: bandwidth, packets, errors/drops, TCP states, Falco network events, active alerts

## CIS Benchmarks Compliance

Политики безопасности основаны на актуальных требованиях из CIS Kubernetes Benchmark v1.12.0, CIS Podman Benchmark v1.8.0.

### OPA Gatekeeper — 14 политик

| # | Политика | CIS Ref | Назначение |
|---|----------|---------|------------|
| 1 | Disallowed Tags | 5.5.1 | Запрет :latest |
| 2 | Allowed Repos | 5.5.1 | Только доверенные реестры |
| 3 | Privileged Container | 5.2.1 | Запрет privileged |
| 4 | RunAsNonRoot | 5.2.6 | Non-root пользователь |
| 5 | Required Resources | best practice | CPU/memory лимиты |
| 6 | Block Podman Socket | Podman 5.31 | Запрет /var/run/docker.sock |
| 7 | Required Probes | best practice | liveness + readiness |
| 8 | Privilege Escalation | 5.2.5 | allowPrivilegeEscalation: false |
| 9 | Dangerous Capabilities | 5.2.7/5.2.8 | Блокировка SYS_ADMIN, SYS_MODULE и др. |
| 10 | Drop ALL Caps | 5.2.7/5.2.8 | capabilities.drop: ALL |
| 11 | Seccomp Profile | 5.7.2 | RuntimeDefault обязателен |
| 12 | Host Namespaces | 5.2.2-5.2.4 | Запрет hostNetwork/PID/IPC |
| 13 | ReadOnly RootFS | 5.2.x | readOnlyRootFilesystem: true |
| 14 | Require NetworkPolicy | 5.3.2 | NetworkPolicy на каждый namespace |

### Pod Security Admission (K8s 1.25+)

| Namespace | Enforce | Audit | Warn |
|-----------|---------|-------|------|
| monitoring | restricted | restricted | restricted |
| production | restricted | restricted | restricted |
| staging | baseline | restricted | restricted |
| kube-system | privileged | - | - |

### kube-bench (60 проверок)

| Группа | Проверок | CIS |
|--------|-----------|-----|
| Control Plane Files | 9 | 1.1.x |
| API Server | 20 | 1.2.x |
| Controller Manager | 7 | 1.3.x |
| Scheduler | 2 | 1.4.x |
| ETCD | 7 | 2.x |
| TLS Hardening | 4 | 1.2.22, 1.2.29, 2.1.5-6 |
| Kubelet | 7 | 4.2.x |

```bash
kube-bench --config k8s/base/kube-bench-config.yaml
```

### Kyverno — Image Verification & Supply Chain

| Политика | CIS | Назначение |
|----------|-------------|------------|
| verify-image-signatures | Контроль целостности | Cosign верификация подписей образов |
| always-pull-images | CIS 1.2.11 | imagePullPolicy: Always |
| restrict-automount-sa-token | CIS 5.1.6 | automountServiceAccountToken: false |

### RBAC Hardening (CIS 5.1.x)

* **monitoring-viewer** — read-only для разработчиков
* **monitoring-operator** — управление мониторингом для администраторов
* **security-auditor** — ClusterRole для аудита безопасности
* Выделенные ServiceAccount для каждого компонента (prometheus, grafana, telegraf, promtail)

### Покрытие требований безопасности

| Требование | Реализация | Статус |
|--------------------|------------|--------|
| Изоляция контейнеров | Namespaces, NetworkPolicy (11), securityContext | Done |
| Контроль Capabilities | Gatekeeper #9/#10, capabilities-config.yaml | Done |
| Privilege Escalation | Gatekeeper #8, Falco rules | Done |
| Запись в файловую систему | Gatekeeper #13 readOnlyRootFilesystem | Done |
| Централизованное управление образами | Gatekeeper #1/#2, Kyverno AlwaysPullImages | Done |
| Ограничение привилегий | Gatekeeper #3/#4/#12, Pod Security Admission | Done |
| Регистрация событий | Falco, Loki, Prometheus alerts, audit-log | Done |
| Управление доступом | RBAC roles, NodeRestriction, SA tokens | Done |
| TLS настройки API-сервера | kube-bench TLS group, tls-min-version | Done |
| Шифрование секретов | encryption-config.yaml (AES-CBC) | Done |
| TLS для etcd | kube-bench ETCD group, cert-file, client-cert-auth | Done |
| Разграничение доступа | NetworkPolicy, RBAC, Namespaces | Done |
| Выявление уязвимостей | Trivy scanning, CI/CD blocking | Done |
| Контроль целостности | Kyverno Cosign verification | Done |

## Container Image Scanning (Trivy)

* **Trivy Server** — локальное сканирование образов (podman-compose, :4954)
* **SBOM** — генерация CycloneDX + SPDX
* **CI/CD блокировка** — автоматическая блокировка образов с CRITICAL/HIGH уязвимостями
* **OPA/Gatekeeper** — 14 CIS-политик для Kubernetes (CIS 5.2.x, 5.3.x, 5.5.x, 5.7.x)

```bash
# Сканировать все образы из podman-compose
./scripts/scanning/scan-images.sh --all --sbom

# Сканировать конкретный образ
./scripts/scanning/scan-images.sh --image nginx:latest --fail-on CRITICAL
```

## План развития

**Статус проекта:** Production Ready  
**Test Coverage:** 80%+

Полный план развития: **[ROADMAP.md](ROADMAP.md)**

### Выполнено (Q1 2026)

* Runtime Security с Falco (deployment, правила, реакции, дашборд)
* Container Image Scanning с Trivy (SBOM, OPA/Gatekeeper, CI/CD блокировка)
* Network Security Monitoring (NetworkPolicy, traffic analysis, service mesh)
* CIS Compliance (14 Gatekeeper политик, Kyverno, RBAC, kube-bench 60 проверок, Encryption, TLS)

### Ближайшие задачи (Q2 2026)

* Compliance as Code (InSpec, OPA)
* ML-based anomaly detection
* Multi-tenancy support

### Долгосрочные (Q3-Q4 2026)

* Multi-cloud support (AWS, Azure, GCP)
* Advanced reporting и analytics
* Integration marketplace
