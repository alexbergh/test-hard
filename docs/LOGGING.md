# Централизованное логирование с Loki

Документация по настройке и использованию централизованного логирования с Grafana Loki.

## Обзор

Платформа использует **Grafana Loki** для централизованного сбора и анализа логов:
- **Loki** - хранилище логов
- **Promtail** - агент сбора логов
- **Grafana** - визуализация и поиск

## Быстрый старт

### Запуск с logging

```bash
# Запустить все сервисы с logging
make up-with-logging

# Или только logging stack
make logging
```

### Доступ к логам

1. Откройте Grafana: http://localhost:3000
2. Перейдите в Explore
3. Выберите datasource "Loki"
4. Используйте LogQL для поиска

## Архитектура

```
┌─────────────┐
│  Containers │
└──────┬──────┘
       │ logs
       ↓
┌─────────────┐
│  Promtail   │ ← собирает логи
└──────┬──────┘
       │ push
       ↓
┌─────────────┐
│    Loki     │ ← хранит логи
└──────┬──────┘
       │ query
       ↓
┌─────────────┐
│   Grafana   │ ← визуализация
└─────────────┘
```

## Конфигурация

### Loki

Конфигурация: `loki/loki-config.yml`

**Основные настройки:**
- Retention: 31 день (744h)
- Storage: filesystem (для production используйте S3/GCS)
- Compaction: каждые 10 минут

### Promtail

Конфигурация: `loki/promtail-config.yml`

**Собирает логи из:**
- Docker контейнеров (через Docker socket)
- Системных логов `/var/log`
- Security scanner отчетов `/reports`

## Запросы LogQL

### Базовые запросы

```logql
# Все логи проекта
{compose_project="test-hard"}

# Логи конкретного сервиса
{compose_service="prometheus"}

# Логи с фильтром по тексту
{compose_service="grafana"} |= "error"

# Исключить определенные логи
{compose_service="prometheus"} != "debug"
```

### Продвинутые запросы

```logql
# Подсчет ошибок за последний час
sum(count_over_time({compose_project="test-hard"} |= "error" [1h]))

# Логи с уровнем ERROR
{compose_project="test-hard"} | json | level="ERROR"

# Rate ошибок в минуту
rate({compose_service="prometheus"} |= "error" [5m])

# Топ 10 контейнеров по количеству логов
topk(10, sum by (container) (count_over_time({compose_project="test-hard"}[1h])))
```

### Запросы для безопасности

```logql
# Логи security сканеров
{job="security_scanners"}

# Критические находки
{job="security_scanners"} |= "CRITICAL" or "HIGH"

# Lynis warnings
{container=~"lynis.*"} |= "warning"

# OpenSCAP failures
{container=~"openscap.*"} |= "fail"
```

## Дашборды

### Дашборд анализа логов

Предустановленный дашборд: `grafana/dashboards/logs-analysis.json`

**Панели:**
- All Container Logs
- Prometheus Logs
- Grafana Logs
- Security Scanner Logs

### Создание custom дашборда

1. Откройте Grafana → Dashboards → New Dashboard
2. Add panel → Select Loki datasource
3. Введите LogQL query
4. Настройте визуализацию
5. Save dashboard

## Хранение данных

### Настройка retention

Редактируйте `loki/loki-config.yml`:

```yaml
limits_config:
  retention_period: 744h  # 31 день

compactor:
  retention_enabled: true
  retention_delete_delay: 2h
```

### Мониторинг storage

```bash
# Размер Loki data
du -sh loki-data/

# Очистка старых данных
docker compose -f docker-compose.logging.yml exec loki \
  wget -O- http://localhost:3100/loki/api/v1/delete?query={job="old_job"}&start=0&end=1234567890
```

## Оповещения на основе логов

### Создание alert rules

Создайте файл `loki/alert-rules.yml`:

```yaml
groups:
  - name: security_alerts
    interval: 1m
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate({compose_project="test-hard"} |= "error" [5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"

      - alert: CriticalSecurityFinding
        expr: |
          count_over_time({job="security_scanners"} |= "CRITICAL" [5m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Critical security finding detected"
```

Добавьте в `loki/loki-config.yml`:

```yaml
ruler:
  alertmanager_url: http://alertmanager:9093
  rule_path: /etc/loki/rules
  storage:
    type: local
    local:
      directory: /loki/rules
```

## Интеграция с Prometheus

### Производные поля

Связь логов с traces/metrics через derived fields (уже настроено в `loki.yml`):

```yaml
derivedFields:
  - datasourceUid: prometheus
    matcherRegex: "traceID=(\\w+)"
    name: TraceID
    url: "$${__value.raw}"
```

## Рекомендации для Production

### 1. Используйте object storage

```yaml
# loki-config.yml для production
schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: s3  # или gcs, azure
      schema: v11

storage_config:
  aws:
    s3: s3://region/bucket-name
    s3forcepathstyle: true
```

### 2. Масштабирование

```yaml
# docker-compose.logging.yml
services:
  loki:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

### 3. Безопасность

```yaml
# Включите authentication
auth_enabled: true

# Используйте TLS
server:
  http_tls_config:
    cert_file: /etc/loki/tls/cert.pem
    key_file: /etc/loki/tls/key.pem
```

### 4. Мониторинг Loki

Loki экспортирует метрики на `/metrics`:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'loki'
    static_configs:
      - targets: ['loki:3100']
```

## Устранение неполадок

### Promtail не отправляет логи

```bash
# Проверить статус Promtail
docker compose -f docker-compose.logging.yml logs promtail

# Проверить targets
curl http://localhost:9080/targets

# Проверить positions
docker compose -f docker-compose.logging.yml exec promtail cat /tmp/positions.yaml
```

### Loki не принимает логи

```bash
# Проверить health
curl http://localhost:3100/ready

# Проверить metrics
curl http://localhost:3100/metrics | grep loki_ingester

# Логи Loki
docker compose -f docker-compose.logging.yml logs loki
```

### Медленные запросы

```logql
# Используйте фильтры для уменьшения объема
{compose_service="prometheus"} |= "error" [1h]

# Вместо
{compose_project="test-hard"} [24h]
```

### Нет логов в Grafana

1. Проверьте datasource: Configuration → Data Sources → Loki
2. Test connection
3. Проверьте, что Promtail работает: `docker ps | grep promtail`
4. Проверьте, что логи собираются: `curl http://localhost:9080/metrics`

## Резервное копирование и восстановление

### Резервное копирование

```bash
# Backup Loki data
docker run --rm -v test-hard_loki-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/loki-backup-$(date +%Y%m%d).tar.gz /data
```

### Восстановление

```bash
# Restore Loki data
docker run --rm -v test-hard_loki-data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/loki-backup-YYYYMMDD.tar.gz -C /
```

## Полезные ссылки

- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [LogQL Documentation](https://grafana.com/docs/loki/latest/logql/)
- [Promtail Configuration](https://grafana.com/docs/loki/latest/clients/promtail/configuration/)
- [Best Practices](https://grafana.com/docs/loki/latest/best-practices/)

## Примеры использования

### Отладка проблем развертывания

```logql
# Логи за последние 5 минут с ошибками
{compose_project="test-hard"} |= "error" [5m]

# Логи конкретного контейнера
{container="prometheus"} [1h]
```

### Мониторинг безопасности

```logql
# Все security findings
{job="security_scanners"}

# Только критические
{job="security_scanners"} |~ "CRITICAL|HIGH"
```

### Анализ производительности

```logql
# Медленные запросы
{compose_service="prometheus"} |= "slow query" [1h]

# Rate логов (индикатор нагрузки)
rate({compose_project="test-hard"}[5m])
```
