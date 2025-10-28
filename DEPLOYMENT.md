# 🚀 Развертывание Security Monitoring Suite

## 📋 Требования

### Системные требования:
- **OS**: Linux/macOS
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **RAM**: минимум 4GB
- **Disk**: минимум 10GB свободного места

### Проверка требований:
```bash
docker --version
docker compose version
```

---

## 🔧 Установка на новом хосте

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
# - scanners/
# - telegraf/
# - prometheus/
# - grafana/
# - scripts/
```

### Шаг 3: Создание директорий для отчетов

```bash
# Директории уже должны существовать в репозитории
ls -la reports/
# reports/lynis/
# reports/openscap/
```

### Шаг 4: Сборка образов

```bash
# Полная сборка всех сервисов
docker compose build --no-cache

# Или сборка отдельных сканеров
docker compose build --no-cache lynis-scanner openscap-scanner
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
# Проверка Prometheus
curl http://localhost:9090/-/healthy

# Проверка Telegraf
curl http://localhost:9091/metrics

# Проверка Grafana
curl http://localhost:3000/api/health
```

---

## 🔍 Запуск сканирования

### Полное сканирование всех хостов:

```bash
./scripts/run_hardening_suite.sh
```

### Проверка результатов:

```bash
# Проверка сгенерированных отчетов
ls -lh reports/lynis/
ls -lh reports/openscap/

# Проверка метрик в файлах
cat reports/lynis/target-fedora_metrics.prom
cat reports/openscap/target-fedora_metrics.prom
```

---

## 📊 Доступ к дашбордам

### Grafana:
```
URL: http://localhost:3000
Login: admin
Password: admin
```

### Дашборды:
1. **Security Monitoring Dashboard**
   - URL: http://localhost:3000/d/security-monitoring/security-monitoring-dashboard
   - Показывает: общие score, warnings, failures

2. **Security Issues Details Dashboard**
   - URL: http://localhost:3000/d/security-issues-details/security-issues-details
   - Показывает: детальные таблицы проблем

### Prometheus:
```
URL: http://localhost:9090
```

### Telegraf Metrics:
```
URL: http://localhost:9091/metrics
```

---

## 🔧 Проверка метрик

### 1. Проверка в Telegraf:
```bash
curl -s http://localhost:9091/metrics | grep security_scanners | head -20
```

### 2. Проверка в Prometheus:
```bash
# Lynis метрики
curl -s "http://localhost:9090/api/v1/query?query=security_scanners_lynis_score" | jq '.data.result'

# OpenSCAP метрики
curl -s "http://localhost:9090/api/v1/query?query=security_scanners_openscap_score" | jq '.data.result'

# Детальные метрики
curl -s "http://localhost:9090/api/v1/query?query=security_scanners_lynis_test_result" | jq '.data.result | length'
```

---

## 🐛 Troubleshooting

### Проблема: "No data" в Grafana

**Решение 1: Проверить метрики в Prometheus**
```bash
curl http://localhost:9090/api/v1/label/__name__/values | jq '.data[]' | grep security_scanners
```

**Решение 2: Перезапустить Telegraf**
```bash
docker compose restart telegraf
sleep 20
curl http://localhost:9091/metrics | grep security_scanners
```

**Решение 3: Проверить datasource в Grafana**
- Открыть: http://localhost:3000/connections/datasources
- Проверить что Prometheus datasource активен
- Test & Save

### Проблема: Сканеры не генерируют метрики

**Решение: Проверить логи**
```bash
# Логи Lynis
docker logs lynis-scanner

# Логи OpenSCAP
docker logs openscap-scanner

# Проверить файлы метрик
ls -lh reports/lynis/
ls -lh reports/openscap/
```

### Проблема: Контейнеры не запускаются

**Решение: Полная очистка и перезапуск**
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

---

## 🔄 Обновление системы

### Обновление из репозитория:
```bash
# Получить последние изменения
git pull origin main

# Пересобрать измененные сервисы
docker compose build --no-cache

# Перезапустить
docker compose down
docker compose up -d
```

### Обновление только сканеров:
```bash
docker compose build --no-cache lynis-scanner openscap-scanner
docker compose up -d lynis-scanner openscap-scanner
```

---

## 📈 Мониторинг

### Проверка ресурсов:
```bash
# Использование ресурсов контейнерами
docker stats

# Размер volumes
docker system df -v
```

### Логи сервисов:
```bash
# Все логи
docker compose logs -f

# Конкретный сервис
docker compose logs -f telegraf
docker compose logs -f prometheus
docker compose logs -f grafana
```

---

## 🗑️ Очистка

### Остановка всех сервисов:
```bash
docker compose down
```

### Полная очистка (включая volumes):
```bash
docker compose down -v
rm -rf reports/lynis/*
rm -rf reports/openscap/*
```

---

## 📝 Структура проекта

```
test-hard/
├── docker-compose.yml           # Основная конфигурация
├── scanners/
│   ├── lynis/
│   │   ├── Dockerfile
│   │   └── entrypoint.sh        # Генерирует метрики
│   └── openscap/
│       ├── Dockerfile
│       └── entrypoint-new.sh    # Генерирует метрики
├── telegraf/
│   └── telegraf.conf            # Конфигурация Telegraf
├── prometheus/
│   └── prometheus.yml           # Конфигурация Prometheus
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/         # Datasource конфигурация
│   │   └── dashboards/          # Dashboard provisioning
│   └── dashboards/
│       ├── security-monitoring.json
│       └── security-issues-details.json
├── reports/
│   ├── lynis/                   # Lynis отчеты и метрики
│   └── openscap/                # OpenSCAP отчеты и метрики
└── scripts/
    └── run_hardening_suite.sh   # Скрипт запуска сканирования
```

---

## 🎯 Метрики

### Агрегированные метрики:
- `security_scanners_lynis_score` - Lynis hardening score (0-100)
- `security_scanners_lynis_warnings` - Количество warnings
- `security_scanners_lynis_suggestions` - Количество suggestions
- `security_scanners_openscap_score` - OpenSCAP compliance score (0-100)
- `security_scanners_openscap_pass_count` - Количество passed rules
- `security_scanners_openscap_fail_count` - Количество failed rules

### Детальные метрики:
- `security_scanners_lynis_test_result` - Детали Lynis тестов
  - Labels: host, test_id, type, description
- `security_scanners_openscap_rule_result` - Детали OpenSCAP правил
  - Labels: host, rule_id, severity, title

---

## 🔐 Безопасность

### Изменение паролей Grafana:
```bash
# Через CLI
docker exec grafana grafana-cli admin reset-admin-password <new_password>

# Или через UI после первого входа
```

### Настройка firewall (опционально):
```bash
# Разрешить только локальный доступ
sudo ufw allow from 127.0.0.1 to any port 3000
sudo ufw allow from 127.0.0.1 to any port 9090
```

---

## 📞 Поддержка

- **Репозиторий**: https://github.com/alexbergh/test-hard
- **Issues**: https://github.com/alexbergh/test-hard/issues

---

## ✅ Чеклист развертывания

- [ ] Docker и Docker Compose установлены
- [ ] Репозиторий склонирован
- [ ] Образы собраны (`docker compose build --no-cache`)
- [ ] Сервисы запущены (`docker compose up -d`)
- [ ] Все контейнеры работают (`docker compose ps`)
- [ ] Сканирование выполнено (`./scripts/run_hardening_suite.sh`)
- [ ] Метрики видны в Telegraf (`curl http://localhost:9091/metrics`)
- [ ] Метрики видны в Prometheus (`curl http://localhost:9090`)
- [ ] Grafana доступна (`http://localhost:3000`)
- [ ] Дашборды отображают данные
- [ ] Пароль Grafana изменен (опционально)

---

## 🎉 Готово!

После выполнения всех шагов система полностью функциональна и готова к использованию.
