# 🛡️ Test-Hard: Security Hardening Scanner

## Основная задача проекта

**Автоматическое сканирование безопасности Linux контейнеров с визуализацией результатов**

### Workflow

```
1. Docker поднимает 4 тестовых контейнера:
   └─ Debian 12, Ubuntu 22.04, Fedora 40, CentOS Stream 9

2. Security сканирование:
   ├─ Lynis → security hardening audit
   └─ OpenSCAP → compliance checking

3. Сбор метрик:
   └─ Telegraf → парсит отчёты → метрики

4. Хранение и визуализация:
   ├─ Prometheus → собирает метрики
   └─ Grafana → дашборды и графики
```

---

## 🚀 Запуск (3 простых шага)

### 1. Подготовка (один раз)

```bash
# Клонировать (если ещё не сделано)
git clone <repo>
cd test-hard

# Создать конфигурацию
cp .env.example .env
nano .env  # ВАЖНО: измените GF_ADMIN_PASSWORD!

# Запустить мониторинг stack
docker compose up -d prometheus grafana telegraf alertmanager docker-proxy

# Проверить что всё запустилось
docker compose ps
```

### 2. Запуск сканирования

```bash
# Основная команда:
./scripts/run_hardening_suite.sh
```

**Что происходит**:
- Поднимаются 4 target контейнера (Debian, Ubuntu, Fedora, CentOS)
- Собираются образы сканеров (Lynis, OpenSCAP)
- Запускается Lynis audit для каждого контейнера
- Запускается OpenSCAP compliance check
- Отчёты сохраняются в `./reports/`
- Метрики автоматически парсятся Telegraf
- Данные отправляются в Prometheus

**Время**: ~5-10 минут

### 3. Просмотр результатов

```bash
# Открыть Grafana
open http://localhost:3000

# Логин: admin
# Пароль: из .env (GF_ADMIN_PASSWORD)

# Prometheus (сырые метрики)
open http://localhost:9090

# Alertmanager (алерты)
open http://localhost:9093
```

---

## 📊 Где смотреть результаты

### 1. Локальные отчёты (детальные)

```bash
# Структура отчётов
reports/
├── fedora/
│   ├── lynis-report.json      # ← Детальный JSON
│   └── openscap/
│       └── report.arf         # ← XML отчёт
├── debian/
│   └── ...
├── centos/
│   └── ...
└── ubuntu/
    └── ...

# Быстрый просмотр Lynis score
cat reports/fedora/lynis-report.json | jq '.general.hardening_index'

# Посмотреть warnings
cat reports/fedora/lynis-report.json | jq '.warnings[].message'

# Посмотреть suggestions
cat reports/fedora/lynis-report.json | jq '.suggestions[].suggestion'
```

### 2. Prometheus (метрики)

http://localhost:9090

**Основные метрики**:

```promql
# Lynis Security Score (0-100)
lynis_score{host="fedora"}

# Количество warnings
lynis_warnings_count{host="fedora"}

# Количество suggestions
lynis_suggestions_count{host="fedora"}

# OpenSCAP провальные проверки
openscap_fail_count{host="fedora"}

# OpenSCAP успешные проверки
openscap_pass_count{host="fedora"}
```

**Полезные запросы**:

```promql
# Все хосты с low security score
lynis_score < 70

# Топ хостов с проблемами
topk(5, lynis_warnings_count + lynis_suggestions_count)

# Процент успешных OpenSCAP проверок
(openscap_pass_count / 
 (openscap_pass_count + openscap_fail_count)) * 100
```

### 3. Grafana (визуализация)

http://localhost:3000

**Дашборды**:
1. Security Hardening Overview
   - Lynis scores по всем хостам
   - Тренды изменений
   - Топ проблем
   - OpenSCAP compliance

2. System Metrics
   - CPU, Memory, Disk
   - Network
   - Processes

**Навигация**:
- Dashboards → Browse → выбрать дашборд
- Explore → для ad-hoc запросов
- Alerting → текущие алерты

---

## 🔁 Регулярное использование

### Ежедневный workflow

```bash
# 1. Запустить сканирование
./scripts/run_hardening_suite.sh

# 2. Дождаться завершения (~5-10 мин)

# 3. Проверить Grafana
open http://localhost:3000

# 4. Проверить алерты
open http://localhost:9093

# 5. Если есть проблемы - детали в отчётах
cat reports/fedora/lynis-report.json | jq '.warnings'
```

### Автоматизация (cron)

```bash
# Добавить в crontab для автоматического сканирования
crontab -e

# Каждый день в 2:00 ночи
0 2 * * * cd /path/to/test-hard && ./scripts/run_hardening_suite.sh

# Или каждые 6 часов
0 */6 * * * cd /path/to/test-hard && ./scripts/run_hardening_suite.sh
```

---

## 🎯 Интерпретация результатов

### Lynis Score

| Диапазон | Оценка | Действия |
|----------|--------|----------|
| **90-100** | 🟢 Отлично | Всё в порядке, продолжайте мониторинг |
| **70-89** | 🟡 Хорошо | Исправить критичные warnings |
| **50-69** | 🟠 Средне | Требуется security hardening |
| **< 50** | 🔴 Плохо | Срочно требуется исправление |

### OpenSCAP Statuses

- **pass** ✅ - Проверка пройдена успешно
- **fail** ❌ - Проверка провалена, требуется исправление
- **error** ⚠️ - Ошибка при проверке (нужно разобраться)
- **unknown** ❓ - Неизвестный статус
- **notchecked** ⏭️ - Проверка была пропущена

### Приоритеты исправления

**1. Критично** (исправить немедленно):
- Lynis warnings с высокой важностью
- OpenSCAP `fail` по security policies
- Score < 50

**2. Важно** (исправить в течение недели):
- Lynis suggestions
- OpenSCAP errors
- Score 50-69

**3. Желательно** (по возможности):
- Оптимизации
- Best practices
- Score 70-89

---

## 🛠️ Команды

### Основное

```bash
# Полное сканирование
./scripts/run_hardening_suite.sh

# Через Makefile
make hardening-suite

# Запустить всё сразу
make up

# Только мониторинг
make monitor
```

### Управление

```bash
# Проверка здоровья
make health

# Логи
make logs
docker compose logs -f telegraf
docker compose logs -f prometheus

# Остановка
make down

# Перезапуск
make restart
```

### Очистка

```bash
# Удалить старые отчёты
make clean

# Удалить всё (включая volumes)
docker compose down -v
```

### Отдельные сканеры

```bash
# Только OpenSCAP
docker compose run --rm openscap-scanner

# Только Lynis
docker compose run --rm lynis-scanner

# Пересобрать сканеры
docker compose build openscap-scanner lynis-scanner
```

---

## 🔍 Troubleshooting

### Проблема: Метрики не появляются в Prometheus

**Решение**:

```bash
# 1. Проверить Telegraf
curl http://localhost:9091/metrics

# Должны быть lynis_* и openscap_* метрики

# 2. Проверить targets в Prometheus
open http://localhost:9090/targets
# telegraf должен быть UP

# 3. Проверить логи
docker compose logs telegraf

# 4. Перезапустить
docker compose restart telegraf prometheus
```

### Проблема: Сканеры не запускаются

**Решение**:

```bash
# 1. Проверить docker-proxy
docker compose ps docker-proxy
docker compose logs docker-proxy

# 2. Пересобрать сканеры
docker compose build openscap-scanner lynis-scanner

# 3. Запустить вручную для debug
docker compose run --rm openscap-scanner
docker compose run --rm lynis-scanner

# 4. Проверить reports директорию
ls -la reports/
chmod 777 reports/  # если проблемы с правами
```

### Проблема: Grafana не показывает данные

**Решение**:

1. Configuration → Data Sources → Prometheus
2. URL должен быть: `http://prometheus:9090`
3. Нажать "Save & Test" → должно быть зелёное ✓
4. Если ошибка - проверить что Prometheus запущен:
   ```bash
   docker compose ps prometheus
   curl http://localhost:9090/-/healthy
   ```

### Проблема: Отчёты не сохраняются

**Решение**:

```bash
# Проверить директорию
ls -la reports/

# Создать если нет
mkdir -p reports
chmod 777 reports

# Проверить volume mounting
docker compose config | grep reports

# Должно быть:
# - ./reports:/reports
```

---

## 📈 Что дальше

### 1. Исправить найденные проблемы

```bash
# Посмотреть рекомендации Lynis
cat reports/fedora/lynis-report.json | jq '.suggestions[].suggestion'

# Применить исправления в контейнерах
# Повторить сканирование
./scripts/run_hardening_suite.sh

# Проверить улучшение score
```

### 2. Настроить алерты

Отредактировать `prometheus/alertmanager.yml`:

```yaml
receivers:
  - name: 'security-team'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK'
        channel: '#security-alerts'
    email_configs:
      - to: 'security@company.com'
```

### 3. Добавить свои контейнеры

В `docker-compose.yml`:

```yaml
services:
  target-myapp:
    image: mycompany/myapp:latest
    container_name: target-myapp
    command: ["sleep", "infinity"]
```

В `scripts/run_hardening_suite.sh`:

```bash
targets=(
  target-fedora
  target-debian
  target-centos
  target-ubuntu
  target-myapp  # ← добавить
)
```

### 4. CI/CD интеграция

Используйте новую CI/CD инфраструктуру (v1.0.0):

```bash
# GitHub Actions автоматически:
# - Запускает тесты
# - Проверяет код
# - Сканирует безопасность
# - Деплоит

# См. документацию:
# - docs/CI-CD.md
# - .github/workflows/ci.yml
```

---

## 📚 Документация

**Для быстрого старта**:
- `QUICK-USAGE.md` ← Самое краткое
- `USER-GUIDE.md` ← Полное руководство
- **README-SECURITY-SCANNING.md** ← Этот файл

**Для разработчиков**:
- `README.md` - Обзор проекта
- `docs/CI-CD.md` - CI/CD pipeline
- `docs/METRICS.md` - Метрики reference

**Справочники**:
- `TROUBLESHOOTING.md` - Решение проблем
- `SECURITY.md` - Security practices
- `CHANGELOG.md` - История изменений

---

## ✅ Checklist для регулярного use case

### Ежедневно
- [ ] Запустить `./scripts/run_hardening_suite.sh`
- [ ] Проверить Grafana дашборд (5 минут)
- [ ] Проверить наличие critical alerts

### Еженедельно
- [ ] Проанализировать тренды (улучшается ли security score?)
- [ ] Исправить топ-5 критичных проблем
- [ ] Обновить baseline метрик

### Ежемесячно
- [ ] Full security review
- [ ] Backup конфигураций и отчётов
- [ ] Обновить Docker образы
- [ ] Review и update security policies

---

## 💡 Pro Tips

### Быстрый анализ

```bash
# Все scores одной командой
for host in fedora debian centos ubuntu; do
  score=$(cat reports/$host/lynis-report.json | jq '.general.hardening_index' 2>/dev/null || echo "N/A")
  echo "$host: $score"
done

# Топ warnings по всем хостам
cat reports/*/lynis-report.json | \
  jq -r '.warnings[].message' | \
  sort | uniq -c | sort -rn | head -10
```

### Сравнение результатов

```bash
# Сохранить текущий score
for host in fedora debian centos ubuntu; do
  cat reports/$host/lynis-report.json | \
    jq '.general.hardening_index' > /tmp/before_$host.txt
done

# После hardening: сравнить
./scripts/run_hardening_suite.sh

for host in fedora debian centos ubuntu; do
  before=$(cat /tmp/before_$host.txt)
  after=$(cat reports/$host/lynis-report.json | jq '.general.hardening_index')
  echo "$host: $before → $after ($(echo "$after - $before" | bc))"
done
```

### Export для отчётов

```bash
# Экспорт метрик из Prometheus
curl -G 'http://localhost:9090/api/v1/query' \
  --data-urlencode 'query=lynis_score' | jq > metrics_snapshot.json

# Создать CSV для Excel
echo "host,lynis_score,warnings,suggestions" > report.csv
for host in fedora debian centos ubuntu; do
  score=$(cat reports/$host/lynis-report.json | jq '.general.hardening_index')
  warns=$(cat reports/$host/lynis-report.json | jq '.warnings | length')
  suggs=$(cat reports/$host/lynis-report.json | jq '.suggestions | length')
  echo "$host,$score,$warns,$suggs" >> report.csv
done
```

---

## 🎯 Ваш основной workflow

```bash
# ============================================
# Ежедневный security check (5 минут)
# ============================================

# 1. Запустить сканирование (фоном)
./scripts/run_hardening_suite.sh &

# 2. Пока идёт сканирование - проверить вчерашние результаты
open http://localhost:3000

# 3. После завершения (~5-10 мин) - обновить дашборд (F5)

# 4. Если есть alerts - посмотреть детали
open http://localhost:9093

# 5. Если нужны детали - смотреть JSON отчёты
cat reports/fedora/lynis-report.json | jq '.warnings'

# ГОТОВО! ✅
```

---

**🛡️ Test-Hard - Security Scanning Made Easy**

Вопросы? См. `TROUBLESHOOTING.md` или `USER-GUIDE.md`
