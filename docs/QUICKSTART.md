# Руководство быстрого старта

## Быстрый запуск на новом хосте

### 1. Клонирование и запуск (5-10 минут)

```bash
# Клонировать репозиторий
git clone https://github.com/alexbergh/test-hard.git
cd test-hard

# (опционально) настроить учетные данные Grafana
cp .env.example .env
nano .env  # изменить GF_ADMIN_PASSWORD

# Собрать и запустить все сервисы
docker compose build --no-cache
docker compose up -d
```

### 2. Запуск сканирования (2-5 минут)

```bash
# Запустить полное сканирование (Lynis, OpenSCAP, Atomic Red Team)
./scripts/scanning/run_hardening_suite.sh

# Сканировать все контейнерные образы (Trivy)
python3 scripts/scan_all_images.py

# Отправить Falco-события для всех контейнеров
python3 scripts/send_falco_events.py

# Запустить сетевое сканирование
docker exec telegraf python3 /opt/test-hard/scripts/scanning/run_network_scan.py \
  --targets 172.19.0.0/24 --scan-type quick --output /var/lib/network-scan
```

### 3. Проверка результатов

```bash
# Проверить что метрики созданы
ls -lh reports/lynis/
ls -lh reports/openscap/
ls -lh reports/trivy/

# Проверить метрики в Telegraf
curl http://localhost:9091/metrics | grep security_scanners | head -10

# Проверить метрики в Prometheus
curl "http://localhost:9090/api/v1/query?query=security_scanners_lynis_score"
curl "http://localhost:9090/api/v1/query?query=trivy_trivy_vulnerabilities_total"
curl "http://localhost:9090/api/v1/query?query=falco_events"
```

### 4. Открыть дашборды

**Grafana:** <http://localhost:3000> (admin / admin)

| Дашборд | URL |
|---------|-----|
| Security Overview | <http://localhost:3000/d/security-overview> |
| Security Monitoring | <http://localhost:3000/d/security-monitoring> |
| Security Issues Details | <http://localhost:3000/d/security-issues-details> |
| Host Compliance | <http://localhost:3000/d/host-compliance> |
| Falco Runtime Security | <http://localhost:3000/d/falco-runtime-security> |
| Container Image Security | <http://localhost:3000/d/container-image-security> |
| Network Security Monitoring | <http://localhost:3000/d/network-security-monitoring> |
| Network Discovery | <http://localhost:3000/d/network-discovery> |
| System Resources | <http://localhost:3000/d/system-resources> |
| Logs Analysis | <http://localhost:3000/d/logs-analysis> |

**Локальный дашборд:** <http://localhost:3001> (веб-интерфейс управления сканированиями)

---

## Одной командой

```bash
git clone https://github.com/alexbergh/test-hard.git && \
cd test-hard && \
docker compose build --no-cache && \
docker compose up -d && \
sleep 30 && \
./scripts/scanning/run_hardening_suite.sh && \
echo "Готово! Grafana: http://localhost:3000 (admin/admin), Dashboard: http://localhost:3001"
```

---

## Проверка что все работает

```bash
# Все контейнеры должны быть UP
docker compose ps

# Grafana должна быть healthy
curl http://localhost:3000/api/health

# Prometheus должен быть healthy
curl http://localhost:9090/-/healthy

# Falcosidekick должен быть healthy
curl http://localhost:2801/healthz

# Telegraf должен отдавать метрики
curl -s http://localhost:9091/metrics | grep -c security_scanners
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
docker compose logs -f falcosidekick
```

---

## Ожидаемые результаты

### Метрики

- **Lynis**: 4 хоста x (score + warnings + suggestions) = 12 агрегированных метрик + ~63 детальных
- **OpenSCAP**: 1 хост x (score + pass + fail) = 3 агрегированные метрики + ~4 детальных
- **Trivy**: 17 образов x (critical + high + medium + low + total + packages) = 102 метрики
- **Falco**: ~400 событий по 20 контейнерам (target, infra, scanner)
- **Network**: 18 хостов, 6 открытых портов, 4 сервиса
- **System**: CPU, память, диск, сеть -- ~50 метрик

### Дашборды Grafana

1. **Security Overview** -- общий обзор безопасности
2. **Security Monitoring** -- метрики сканеров в динамике
3. **Security Issues Details** -- детальные таблицы проблем Lynis/OpenSCAP
4. **Host Compliance** -- соответствие по каждому хосту
5. **Falco Runtime Security** -- runtime-события, правила, приоритеты
6. **Container Image Security** -- уязвимости образов Trivy
7. **Network Security Monitoring** -- bandwidth, packets, errors, TCP states
8. **Network Discovery** -- обнаруженные хосты, порты, сервисы
9. **System Resources** -- CPU, память, диск, сеть, процессы
10. **Logs Analysis** -- анализ логов через Loki

---

## Требования

- Docker 20.10+
- Docker Compose 2.0+
- 4 GB RAM (рекомендуется 8 GB)
- 10 GB disk space
- Linux / macOS / Windows (WSL2)

---

## Полная документация

См. [DEPLOYMENT.md](DEPLOYMENT.md) для детальной инструкции с troubleshooting и настройкой безопасности.

---

Последнее обновление: Февраль 2026
