# Развертывание Security Monitoring Suite

## Требования

### Системные требования

- **OS**: Linux / macOS / Windows (WSL2)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **RAM**: минимум 4 GB (рекомендуется 8 GB)
- **Disk**: минимум 10 GB свободного места

### Проверка требований

```bash
docker --version
docker compose version
```

---

## Установка на новом хосте

### Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/alexbergh/test-hard.git
cd test-hard
```

### Шаг 2: Проверка структуры проекта

```bash
ls -la
# Должны быть:
# - docker-compose.yml
# - Dockerfile
# - docker/               (Dockerfiles для целевых ОС)
# - falco/                (конфигурация Falco)
# - trivy/                (конфигурация Trivy)
# - grafana/              (дашборды и provisioning)
# - prometheus/           (конфигурация Prometheus)
# - telegraf/             (конфигурация Telegraf)
# - loki/                 (конфигурация Loki)
# - dashboard/            (веб-интерфейс: backend + frontend)
# - scripts/              (скрипты сканирования, парсинга, мониторинга)
# - k8s/                  (Kubernetes manifests)
```

### Шаг 3: Настройка переменных окружения

```bash
# Скопировать шаблон
cp .env.example .env

# Отредактировать (как минимум пароль Grafana)
nano .env
```

### Шаг 4: Сборка образов

```bash
# Полная сборка всех сервисов
docker compose build --no-cache

# Или параллельная сборка (быстрее)
docker compose build --parallel
```

### Шаг 5: Запуск инфраструктуры

```bash
# Запуск всех сервисов
docker compose up -d

# Проверка статуса
docker compose ps
```

### Шаг 6: Проверка сервисов

```bash
# Prometheus
curl http://localhost:9090/-/healthy

# Telegraf
curl http://localhost:9091/metrics | head -5

# Grafana
curl http://localhost:3000/api/health

# Alertmanager
curl http://localhost:9093/-/healthy

# Falcosidekick
curl http://localhost:2801/healthz

# Trivy Server
curl http://localhost:4954/healthz

# Loki
curl http://localhost:3100/ready

# Web Dashboard (backend)
curl http://localhost:8000/health
```

---

## Запуск сканирования

### Полное сканирование всех хостов

```bash
# Lynis + OpenSCAP + Atomic Red Team
./scripts/scanning/run_hardening_suite.sh

# Trivy: сканирование всех контейнерных образов
python3 scripts/scan_all_images.py

# Falco: генерация событий для всех контейнеров
python3 scripts/send_falco_events.py

# Network: сканирование Docker-сети
docker exec telegraf python3 /opt/test-hard/scripts/scanning/run_network_scan.py \
  --targets 172.19.0.0/24 --scan-type quick --output /var/lib/network-scan
```

### Проверка результатов

```bash
# Отчеты Lynis и OpenSCAP
ls -lh reports/lynis/
ls -lh reports/openscap/

# Метрики Trivy
ls -lh reports/trivy/*_metrics.prom

# Метрики в Prometheus
curl -s "http://localhost:9090/api/v1/query?query=security_scanners_lynis_score" | python3 -m json.tool
curl -s "http://localhost:9090/api/v1/query?query=trivy_trivy_vulnerabilities_total" | python3 -m json.tool
curl -s "http://localhost:9090/api/v1/query?query=falco_events" | python3 -m json.tool
```

---

## Доступ к дашбордам

### Grafana

```
URL: http://localhost:3000
Login: admin
Password: admin (или значение из .env)
```

### Дашборды Grafana (10 штук)

| Дашборд | Описание |
|---------|----------|
| **Security Overview** | Общий обзор безопасности: Lynis, OpenSCAP, Atomic Red Team |
| **Security Monitoring** | Метрики сканеров в динамике |
| **Security Issues Details** | Таблицы Lynis/OpenSCAP проблем |
| **Host Compliance** | Подробности соответствия по каждому хосту |
| **Falco Runtime Security** | Runtime-события Falco, правила, доставка через Falcosidekick |
| **Container Image Security** | Уязвимости образов Trivy, тренды, таблицы |
| **Network Security Monitoring** | Bandwidth, packets, errors/drops, TCP states |
| **Network Discovery** | Обнаруженные хосты, открытые порты, сервисы |
| **System Resources** | CPU, память, диск, сеть, процессы |
| **Logs Analysis** | Анализ логов через Loki |

### Веб-дашборд

```
URL: http://localhost:3001
```

Локальный веб-интерфейс (React + FastAPI) для управления сканированиями, просмотра хостов и результатов.

### Prometheus

```
URL: http://localhost:9090
```

### Alertmanager

```
URL: http://localhost:9093
```

### Другие сервисы

| Сервис | URL | Назначение |
|--------|-----|------------|
| Falcosidekick | http://localhost:2801 | Маршрутизация Falco-событий |
| Trivy Server | http://localhost:4954 | Сканирование образов |
| Falco Responder | http://localhost:5080 | Автоматические реакции |
| Loki | http://localhost:3100 | Хранилище логов |
| Telegraf | http://localhost:9091/metrics | Метрики агента |

---

## Проверка метрик

### 1. Проверка в Telegraf

```bash
curl -s http://localhost:9091/metrics | grep security_scanners | head -20
```

### 2. Проверка в Prometheus

```bash
# Lynis
curl -s "http://localhost:9090/api/v1/query?query=security_scanners_lynis_score"

# OpenSCAP
curl -s "http://localhost:9090/api/v1/query?query=security_scanners_openscap_score"

# Trivy
curl -s "http://localhost:9090/api/v1/query?query=count(trivy_trivy_vulnerabilities_total)"

# Falco
curl -s "http://localhost:9090/api/v1/query?query=sum(increase(falco_events[24h]))"

# Network
curl -s "http://localhost:9090/api/v1/query?query=network_scan_hosts_total"
```

---

## Устранение неполадок

### Проблема: "No data" в Grafana

**Решение 1: Проверить метрики в Prometheus**

```bash
curl http://localhost:9090/api/v1/label/__name__/values | grep -E "security|trivy|falco|network"
```

**Решение 2: Перезапустить Telegraf**

```bash
docker compose restart telegraf
sleep 20
curl http://localhost:9091/metrics | grep security_scanners
```

**Решение 3: Проверить datasource в Grafana**

- Открыть: <http://localhost:3000/connections/datasources>
- Проверить что Prometheus и Loki datasources активны
- Test & Save

### Проблема: Сканеры не генерируют метрики

```bash
# Логи сканеров
docker logs lynis-scanner
docker logs openscap-scanner

# Проверить файлы метрик
ls -lh reports/lynis/
ls -lh reports/openscap/
ls -lh reports/trivy/
```

### Проблема: Контейнеры не запускаются

```bash
# Остановить все
docker compose down -v

# Очистить старые образы
docker system prune -a

# Пересобрать
docker compose build --no-cache

# Запустить
docker compose up -d
```

### Проблема: Trivy метрики не появляются в Prometheus

Telegraf читает `.prom` файлы из `/reports/trivy/`. Файлы должны иметь Unix-формат переносов строк (LF, не CRLF). Если файлы генерировались на Windows, исправьте:

```bash
# Внутри контейнера telegraf проверить логи на ошибки парсинга
docker logs telegraf --tail 20 | grep -i "trivy\|error"
```

---

## Обновление системы

```bash
# Получить последние изменения
git pull origin main

# Пересобрать измененные сервисы
docker compose build --no-cache

# Перезапустить
docker compose down
docker compose up -d
```

---

## Структура проекта

```
test-hard/
├── docker-compose.yml           # Все сервисы: мониторинг, сканеры, Falco, Trivy
├── Dockerfile                   # Единый multi-stage образ (Lynis, OpenSCAP, Telegraf)
├── .env.example                 # Шаблон переменных окружения
├── Makefile                     # Упрощенные команды
├── docker/                      # Dockerfiles для целевых ОС
│   ├── ubuntu/
│   ├── debian/
│   ├── fedora/
│   ├── centos/
│   └── altlinux/
├── falco/
│   ├── falco.yaml               # Конфигурация Falco
│   ├── falcosidekick.yaml       # Маршрутизация событий
│   ├── rules.d/                 # Кастомные правила (30+)
│   └── responder/               # Автоматические реакции
├── trivy/
│   ├── trivy.yaml               # Конфигурация Trivy
│   └── .trivyignore             # Игнорируемые CVE
├── grafana/
│   ├── dashboards/              # 10 преднастроенных дашбордов
│   └── provisioning/            # Datasources (Prometheus, Loki)
├── prometheus/
│   ├── prometheus.yml           # Конфиг скрейпинга
│   ├── alert.rules.yml          # Правила алертинга
│   └── alertmanager.yml         # Маршрутизация алертов
├── loki/
│   ├── loki-config.yml          # Конфигурация Loki
│   └── promtail-config.yml      # Конфигурация Promtail
├── telegraf/
│   └── telegraf.conf            # Сбор метрик (system, Lynis, OpenSCAP, Trivy, network)
├── dashboard/
│   ├── backend/                 # FastAPI backend (JWT, RBAC, SQLAlchemy)
│   └── frontend/                # React + TailwindCSS frontend
├── scripts/
│   ├── scanning/                # Lynis, OpenSCAP, ART, Trivy, network scan
│   ├── parsing/                 # Парсеры отчетов
│   ├── monitoring/              # Health checks
│   ├── setup/                   # Скрипты настройки
│   ├── testing/                 # Тестирование
│   ├── backup/                  # Backup
│   └── utils/                   # Утилиты
├── k8s/
│   ├── base/                    # Kustomize base
│   └── overlays/                # dev / staging / prod
├── argocd/                      # GitOps deployment
└── reports/                     # Результаты сканирований
    ├── lynis/
    ├── openscap/
    └── trivy/
```

---

## Метрики

### Агрегированные метрики

| Метрика | Описание |
|---------|----------|
| `security_scanners_lynis_score` | Lynis hardening score (0-100) |
| `security_scanners_lynis_warnings` | Количество warnings |
| `security_scanners_lynis_suggestions` | Количество suggestions |
| `security_scanners_openscap_score` | OpenSCAP compliance score (0-100) |
| `security_scanners_openscap_pass_count` | Количество passed rules |
| `security_scanners_openscap_fail_count` | Количество failed rules |
| `trivy_trivy_vulnerabilities_critical` | Critical уязвимости по образам |
| `trivy_trivy_vulnerabilities_high` | High уязвимости по образам |
| `trivy_trivy_vulnerabilities_total` | Всего уязвимостей по образам |
| `falco_events` | Falco runtime-события (по priority и rule) |
| `network_scan_hosts_total` | Обнаруженные хосты в сети |
| `network_scan_open_ports_total` | Открытые порты |

### Детальные метрики

- `security_scanners_lynis_test_result` -- детали Lynis тестов (labels: host, test_id, type, description)
- `security_scanners_openscap_rule_result` -- детали OpenSCAP правил (labels: host, rule_id, severity, title)

---

## Безопасность

### Изменение паролей Grafana

```bash
# Через CLI
docker exec grafana grafana-cli admin reset-admin-password <new_password>

# Или через .env перед первым запуском
GF_ADMIN_PASSWORD=your_secure_password
```

### Настройка firewall (опционально)

```bash
# Разрешить только локальный доступ
sudo ufw allow from 127.0.0.1 to any port 3000
sudo ufw allow from 127.0.0.1 to any port 9090
```

---

## Чеклист развертывания

- [ ] Docker и Docker Compose установлены
- [ ] Репозиторий склонирован
- [ ] `.env` файл создан и пароли изменены
- [ ] Образы собраны (`docker compose build`)
- [ ] Сервисы запущены (`docker compose up -d`)
- [ ] Все контейнеры работают (`docker compose ps`)
- [ ] Сканирование выполнено (`./scripts/scanning/run_hardening_suite.sh`)
- [ ] Trivy сканирование выполнено (`python3 scripts/scan_all_images.py`)
- [ ] Метрики видны в Telegraf (`curl http://localhost:9091/metrics`)
- [ ] Метрики видны в Prometheus (`curl http://localhost:9090`)
- [ ] Grafana доступна (`http://localhost:3000`)
- [ ] Все 10 дашбордов отображают данные
- [ ] Пароль Grafana изменен

---

Последнее обновление: Февраль 2026
