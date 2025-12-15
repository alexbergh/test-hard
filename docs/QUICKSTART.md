# Руководство быстрого старта

## Быстрый запуск на новом хосте

### 1. Клонирование и сборка (5-10 минут)

```bash
# Клонировать репозиторий
git clone https://github.com/alexbergh/test-hard.git
cd test-hard

# Собрать все образы
docker compose build --no-cache

# Запустить все сервисы
docker compose up -d
```

### 2. Запуск сканирования (2-5 минут)

```bash
# Запустить полное сканирование
./scripts/scanning/run_hardening_suite.sh
```

### 3. Проверка результатов

```bash
# Проверить что метрики созданы
ls -lh reports/lynis/
ls -lh reports/openscap/

# Проверить метрики в Telegraf
curl http://localhost:9091/metrics | grep security_scanners | head -10

# Проверить метрики в Prometheus
curl "http://localhost:9090/api/v1/query?query=security_scanners_lynis_score"
```

### 4. Открыть дашборды

```bash
# Открыть Grafana
open http://localhost:3000

# Login: admin
# Password: admin
```

**Дашборды:**

* Security Monitoring: <http://localhost:3000/d/security-monitoring/security-monitoring-dashboard>
* Security Issues Details: <http://localhost:3000/d/security-issues-details/security-issues-details>

---

## Одной командой

```bash
git clone https://github.com/alexbergh/test-hard.git && \
cd test-hard && \
docker compose build --no-cache && \
docker compose up -d && \
sleep 30 && \
./scripts/scanning/run_hardening_suite.sh && \
echo "Готово! Открывайте http://localhost:3000 (admin/admin)"
```

---

## Проверка что всё работает

```bash
# Все контейнеры должны быть UP
docker compose ps

# Должно быть ~75 метрик
curl -s http://localhost:9091/metrics | grep -c security_scanners

# Grafana должна быть healthy
curl http://localhost:3000/api/health
```

---

## Устранение неполадок

### Перезапуск всего

```bash
docker compose down
docker compose up -d
sleep 30
./scripts/scanning/run_hardening_suite.sh
```

### Полная очистка и пересборка

```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
./scripts/scanning/run_hardening_suite.sh
```

### Проверка логов

```bash
docker compose logs -f telegraf
docker compose logs -f prometheus
docker compose logs -f grafana
```

---

## Ожидаемые результаты

### Метрики

* **Lynis**: 4 хоста × (score + warnings + suggestions) = 12 агрегированных метрик
* **Lynis детальные**: ~63 метрики (warnings + suggestions)
* **OpenSCAP**: 1 хост × (score + pass + fail) = 3 агрегированные метрики
* **OpenSCAP детальные**: ~4 метрики (failed rules)
* **Всего**: ~82 метрики

### Дашборды

1. **Security Monitoring** - показывает score и графики
2. **Security Issues Details** - показывает детальные таблицы проблем

---

## Требования

* Docker 20.10+
* Docker Compose 2.0+
* 4GB RAM
* 10GB disk space
* Linux/macOS

---

## Полная документация

См. [DEPLOYMENT.md](DEPLOYMENT.md) для детальной инструкции с troubleshooting и настройкой безопасности.

---

## Готово

После выполнения команд система готова к использованию.
