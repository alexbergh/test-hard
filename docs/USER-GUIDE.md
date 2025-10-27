# Test-Hard: Security Hardening Scanner - User Guide

## 📖 Что делает этот проект

**Test-Hard** - автоматизированная система для проверки security hardening контейнеров.

### Процесс работы

```
┌─────────────────────────────────────────────────────────┐
│  1. Запуск 4 тестовых контейнеров                       │
│     • Debian 12                                         │
│     • Ubuntu 22.04                                      │
│     • Fedora 40                                         │
│     • CentOS Stream 9                                   │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  2. Security сканирование                               │
│     • Lynis (system hardening audit)                    │
│     • OpenSCAP (security compliance)                    │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  3. Сбор метрик                                         │
│     • Telegraf парсит результаты                        │
│     • Prometheus собирает метрики                       │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  4. Визуализация                                        │
│     • Grafana показывает дашборды                       │
│     • Alertmanager шлёт уведомления                     │
└─────────────────────────────────────────────────────────┘
```

---

## Быстрый старт

### Шаг 1: Подготовка

```bash
# Клонировать репозиторий
git clone <repo-url>
cd test-hard

# Создать .env файл
cp .env.example .env

# Отредактировать (ВАЖНО: изменить пароли!)
nano .env
```

### Шаг 2: Запуск мониторинга

```bash
# Запустить Prometheus, Grafana, Telegraf
docker compose up -d prometheus grafana telegraf alertmanager docker-proxy

# Проверить, что всё работает
docker compose ps
```

### Шаг 3: Запуск сканирования

```bash
# Запустить полное сканирование
./scripts/run_hardening_suite.sh
```

Это автоматически:
1. Поднимет 4 тестовых контейнера
2. Соберёт образы сканеров
3. Запустит OpenSCAP проверки
4. Запустит Lynis аудит
5. Сохранит отчёты в `./reports/`

### Шаг 4: Просмотр результатов

```bash
# Открыть Grafana
open http://localhost:3000

# Логин: admin
# Пароль: из вашего .env файла (GF_ADMIN_PASSWORD)
```

---

## Доступ к сервисам

| Сервис | URL | Описание |
|--------|-----|----------|
| **Grafana** | http://localhost:3000 | Дашборды и визуализация |
| **Prometheus** | http://localhost:9090 | Метрики и alerts |
| **Alertmanager** | http://localhost:9093 | Управление алертами |
| **Telegraf** | http://localhost:9091/metrics | Сырые метрики |

### Дефолтные креды

- **Grafana**: admin / (из .env GF_ADMIN_PASSWORD)
- **Prometheus**: без аутентификации
- **Alertmanager**: без аутентификации

---

## Что проверяется

### Lynis Scanner

**Проверяет**:
- System hardening (закалка системы)
- File permissions
- Security updates
- Network configuration
- Running services
- Kernel hardening
- Authentication settings

**Метрики**:
```
lynis_score                  # Общий балл (0-100)
lynis_warnings_count         # Количество предупреждений
lynis_suggestions_count      # Количество рекомендаций
lynis_tests_performed        # Выполнено тестов
```

### OpenSCAP Scanner

**Проверяет**:
- Security compliance (SCAP standards)
- CVE vulnerabilities
- Configuration issues
- Security policies

**Метрики**:
```
openscap_pass_count          # Успешные проверки
openscap_fail_count          # Провальные проверки
openscap_error_count         # Ошибки
openscap_unknown_count       # Неизвестные статусы
```

---

## 📁 Структура отчётов

После запуска сканирования отчёты сохраняются в `./reports/`:

```
reports/
├── fedora/
│   ├── lynis-report.json           # Lynis отчёт для Fedora
│   └── openscap/
│       └── report.arf              # OpenSCAP отчёт
├── debian/
│   ├── lynis-report.json
│   └── openscap/
│       └── report.arf
├── centos/
│   └── ...
└── ubuntu/
    └── ...
```

---

## Основные команды

### Запуск сканирования

```bash
# Полное сканирование (рекомендуется)
./scripts/run_hardening_suite.sh

# Или через Makefile
make hardening-suite

# Только OpenSCAP
docker compose run --rm openscap-scanner

# Только Lynis
docker compose run --rm lynis-scanner
```

### Управление сервисами

```bash
# Запустить всё (targets + scanners + monitoring)
make up

# Запустить только мониторинг
make monitor

# Запустить только targets и scanners
make up-targets

# Остановить всё
make down

# Перезапустить
make restart

# Посмотреть логи
make logs
```

### Проверка здоровья

```bash
# Проверить статус всех сервисов
make health

# Результат:
# ✓ Prometheus healthy
# ✓ Grafana healthy
# ✓ Telegraf healthy
```

### Очистка отчётов

```bash
# Удалить старые отчёты
make clean

# Будет создана пустая директория reports/
```

---

## Метрики в Prometheus

### Просмотр метрик

Откройте http://localhost:9090 и попробуйте эти запросы:

#### Lynis метрики

```promql
# Общий security score по всем хостам
lynis_score

# Хосты с низким score (< 70)
lynis_score < 70

# Количество предупреждений
lynis_warnings_count

# Топ хостов с наибольшим числом проблем
topk(5, lynis_warnings_count + lynis_suggestions_count)
```

#### OpenSCAP метрики

```promql
# Провальные проверки
openscap_fail_count

# Процент успешных проверок
(openscap_pass_count / 
 (openscap_pass_count + openscap_fail_count)) * 100

# Хосты с критичными проблемами (> 10 fails)
openscap_fail_count > 10
```

#### System метрики (Telegraf)

```promql
# CPU usage
cpu_usage_idle
100 - cpu_usage_idle  # CPU load

# Memory
mem_used_percent

# Disk
disk_used_percent
```

---

## 🎨 Grafana Dashboards

### Импорт дашбордов

1. Откройте Grafana: http://localhost:3000
2. Логин с admin credentials
3. Перейдите в Dashboards → Browse
4. Дашборды должны быть автоматически загружены из `./grafana/dashboards/`

### Основные дашборды

**Security Hardening Overview**:
- Lynis scores по всем хостам
- OpenSCAP compliance статус
- Trending (динамика изменений)
- Top issues (топ проблем)

**System Metrics**:
- CPU, Memory, Disk usage
- Network traffic
- Running processes

---

## 🔔 Alerting

### Настроенные алерты

**Критичные**:
- `LynisScoreLow` - Lynis score < 60
- `OpenSCAPHighFailures` - Более 20 провальных проверок
- `TelegrafDown` - Telegraf не отвечает
- `PrometheusDown` - Prometheus не работает

**Предупреждения**:
- `LynisScoreMedium` - Lynis score < 70
- `OpenSCAPMediumFailures` - 10-20 провальных проверок
- `HighWarningsCount` - Более 15 предупреждений Lynis

### Просмотр алертов

```bash
# Открыть Alertmanager
open http://localhost:9093

# Или в Prometheus
open http://localhost:9090/alerts
```

### Настройка уведомлений

Отредактируйте `prometheus/alertmanager.yml`:

```yaml
receivers:
  - name: 'default-receiver'
    # Добавьте свой Slack webhook
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#security-alerts'
    
    # Или email
    email_configs:
      - to: 'security-team@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'
```

---

## 🔧 Настройка

### Изменить целевые контейнеры

Отредактируйте `docker-compose.yml`:

```yaml
services:
  # Добавить новый target
  target-rocky:
    image: rockylinux:9
    container_name: target-rocky
    command: ["sleep", "infinity"]
```

И обновите `scripts/run_hardening_suite.sh`:

```bash
targets=(
  target-fedora
  target-debian
  target-centos
  target-ubuntu
  target-rocky  # Добавьте сюда
)
```

### Изменить частоту сканирования

Для автоматического регулярного сканирования добавьте в crontab:

```bash
# Сканировать каждый день в 2:00 ночи
0 2 * * * cd /path/to/test-hard && ./scripts/run_hardening_suite.sh

# Сканировать каждый час
0 * * * * cd /path/to/test-hard && ./scripts/run_hardening_suite.sh
```

### Retention (хранение метрик)

По умолчанию Prometheus хранит метрики 30 дней.

Изменить в `.env`:

```bash
PROMETHEUS_RETENTION_TIME=90d    # 90 дней
PROMETHEUS_RETENTION_SIZE=20GB   # 20 ГБ
```

---

## 🐛 Troubleshooting

### Проблема: Сканеры не запускаются

```bash
# Проверить логи
docker compose logs openscap-scanner
docker compose logs lynis-scanner

# Проверить docker-proxy
docker compose logs docker-proxy

# Пересобрать образы
docker compose build openscap-scanner lynis-scanner
```

### Проблема: Метрики не появляются в Prometheus

```bash
# Проверить Telegraf
curl http://localhost:9091/metrics

# Проверить targets в Prometheus
open http://localhost:9090/targets

# Проверить логи Telegraf
docker compose logs telegraf
```

### Проблема: Grafana не показывает данные

1. Проверьте datasource: Configuration → Data Sources → Prometheus
2. URL должен быть: `http://prometheus:9090`
3. Нажмите "Test" - должно быть зелёное "Data source is working"

### Проблема: Отчёты не сохраняются

```bash
# Проверить права на директорию
ls -la reports/

# Создать директорию
mkdir -p reports
chmod 777 reports

# Пересоздать volume
docker compose down -v
make clean
make up
```

---

## Пример workflow

### Ежедневное использование

```bash
# Утром: Запустить сканирование
./scripts/run_hardening_suite.sh

# Дождаться завершения (~5-10 минут)
# Проверить отчёты локально
ls -lh reports/*/

# Открыть Grafana и проверить дашборд
open http://localhost:3000

# Проверить алерты
open http://localhost:9093

# Если есть проблемы - посмотреть детали в отчётах
cat reports/fedora/lynis-report.json | jq '.warnings'
```

### Continuous Monitoring

```bash
# 1. Запустить весь стек
make up

# 2. Настроить cron для регулярного сканирования
crontab -e
# Добавить:
0 */6 * * * cd /path/to/test-hard && ./scripts/run_hardening_suite.sh

# 3. Настроить алерты в alertmanager.yml

# 4. Мониторить через Grafana
```

---

## 🎓 Интерпретация результатов

### Lynis Score

| Score | Уровень | Действия |
|-------|---------|----------|
| **90-100** | Отлично | Поддерживать уровень |
| **70-89** | Хорошо | Исправить критичные issues |
| **50-69** | Средне | Требуются улучшения |
| **< 50** | Плохо | Срочно требуется hardening |

### OpenSCAP Results

| Статус | Значение |
|--------|----------|
| **pass** | Проверка пройдена |
| **fail** | Проверка провалена (требуется исправление) |
| **error** | Ошибка при проверке |
| **unknown** | ❓ Статус неизвестен |
| **notchecked** | ⏭Проверка пропущена |

### Приоритизация

1. **Критично**: `fail` в OpenSCAP + Lynis warnings с severity "high"
2. **Важно**: Lynis suggestions + `error` в OpenSCAP
3. **Желательно**: Остальные recommendations

---

## Дополнительная информация

### Документация

- `README.md` - Общий обзор проекта
- `QUICKSTART.md` - 5-минутный старт
- `SECURITY.md` - Security best practices
- `TROUBLESHOOTING.md` - Детальное решение проблем
- `docs/METRICS.md` - Полный список метрик

### Полезные ссылки

- **Lynis**: https://cisofy.com/lynis/
- **OpenSCAP**: https://www.open-scap.org/
- **Prometheus**: https://prometheus.io/docs/
- **Grafana**: https://grafana.com/docs/

---

## 🔐 Security Best Practices

1. **Изменить дефолтные пароли** в `.env`
2. **Ограничить доступ** к портам (firewall)
3. **Регулярно обновлять** Docker образы
4. **Настроить TLS** для production
5. **Backup** конфигураций и данных

---

## Checklist для регулярного использования

### Ежедневно
- [ ] Запустить `./scripts/run_hardening_suite.sh`
- [ ] Проверить дашборд в Grafana
- [ ] Проверить алерты

### Еженедельно
- [ ] Проанализировать тренды
- [ ] Исправить критичные issues
- [ ] Обновить конфигурации

### Ежемесячно
- [ ] Backup конфигураций
- [ ] Обновить Docker образы
- [ ] Review security policies
- [ ] Архивировать старые отчёты

---

## Tips & Tricks

### Быстрый просмотр результатов

```bash
# Последний Lynis score для Fedora
cat reports/fedora/lynis-report.json | jq '.general.hardening_index'

# Количество fail в OpenSCAP для всех хостов
for host in fedora debian centos ubuntu; do
  echo "$host:"
  grep -c "fail" reports/$host/openscap/*.arf || echo "0"
done

# Топ warnings из Lynis
cat reports/*/lynis-report.json | jq -r '.warnings[].message' | sort | uniq -c | sort -rn | head
```

### Экспорт метрик

```bash
# Экспорт текущих метрик из Prometheus
curl http://localhost:9090/api/v1/query?query=lynis_score > lynis_scores.json

# Экспорт за период
curl 'http://localhost:9090/api/v1/query_range?query=lynis_score&start=2024-10-20T00:00:00Z&end=2024-10-27T00:00:00Z&step=1h' > lynis_history.json
```

### Сравнение результатов

```bash
# Сравнить score до и после hardening
echo "Before: $(cat reports_old/fedora/lynis-report.json | jq '.general.hardening_index')"
echo "After:  $(cat reports/fedora/lynis-report.json | jq '.general.hardening_index')"
```

---

## Быстрая шпаргалка

```bash
# Полный цикл
make up                              # Запустить всё
./scripts/run_hardening_suite.sh     # Сканировать
make health                          # Проверить
open http://localhost:3000           # Grafana

# Повторное сканирование
./scripts/run_hardening_suite.sh

# Очистка и перезапуск
make down
make clean
make up

# Просмотр логов
make logs

# Остановка
make down
```

---

**Happy Hardening!**

Для вопросов и проблем см. `TROUBLESHOOTING.md` или откройте issue в репозитории.
