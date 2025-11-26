# Руководство по устранению неполадок

Комплексное руководство по решению типичных проблем в test-hard.

## Содержание

* [Проблемы с Docker](#проблемы-с-docker)
* [Проблемы с Grafana](#проблемы-с-grafana)
* [Проблемы с Prometheus](#проблемы-с-prometheus)
* [Проблемы с Telegraf](#проблемы-с-telegraf)
* [Проблемы со сканированием](#проблемы-со-сканированием)
* [Проблемы с сетью](#проблемы-с-сетью)
* [Проблемы с производительностью](#проблемы-с-производительностью)
* [Проблемы с безопасностью](#проблемы-с-безопасностью)

---

## Проблемы с Docker

### Контейнеры не запускаются

**Симптомы:**

```bash
docker compose up -d
# Контейнеры падают или не запускаются
```

**Диагностика:**

```bash
# Проверить логи
docker compose logs

# Проверить статус
docker compose ps

# Проверить конфигурацию
docker compose config
```

**Решения:**

1. **Порты заняты:**

   ```bash
   # Проверить занятые порты
   ss -tlnp | grep -E '3000|9090|9091|9093'
   
   # Изменить порты в .env
   echo "GRAFANA_HOST_PORT=3001" >> .env
   ```

2. **Недостаточно ресурсов:**

   ```bash
   # Проверить ресурсы
   docker system df
   
   # Очистить
   docker system prune -a
   ```

3. **Проблемы с сетью:**

   ```bash
   # Пересоздать сеть
   docker compose down
   docker network prune
   docker compose up -d
   ```

---

### Docker съедает всю память

**Симптомы:**

* Система тормозит
* OOM (Out of Memory) ошибки
* Контейнеры перезапускаются

**Решение:**

1. **Проверить использование:**

   ```bash
   docker stats
   ```

2. **Ограничения уже установлены в docker-compose.yml:**

   ```yaml
   services:
     prometheus:
       mem_limit: 2g
       mem_reservation: 1g
   ```

3. **Уменьшить retention в Prometheus:**

   ```yaml
   # prometheus/prometheus.yml
   --storage.tsdb.retention.time=15d  # было 30d
   --storage.tsdb.retention.size=5GB  # было 10GB
   ```

4. **Настроить Docker daemon:**

   ```json
   # /etc/docker/daemon.json
   {
     "log-driver": "json-file",
     "log-opts": {
       "max-size": "10m",
       "max-file": "3"
     }
   }
   ```

---

### Permission denied при доступе к Docker

**Симптомы:**

```
Got permission denied while trying to connect to the Docker daemon socket
```

**НЕ ДЕЛАЙТЕ:**

```bash
# НЕ добавляйте пользователя в docker group!
sudo usermod -aG docker $USER  # НЕБЕЗОПАСНО!
```

**Правильное решение:**

1. **Используйте Docker Socket Proxy (уже настроен):**

   ```yaml
   # docker-compose.yml
   docker-proxy:
     image: tecnativa/docker-socket-proxy
     environment:
       - CONTAINERS=1
       - IMAGES=1
       - INFO=1
   ```

2. **Или используйте sudo с ограниченными правами:**

   ```bash
   # /etc/sudoers.d/scanner
   scanner ALL=(ALL) NOPASSWD: /usr/bin/docker
   ```

---

## Проблемы с Grafana

### "No data" в дашбордах

**Симптомы:**

* Дашборды пустые
* Сообщение "No data"
* Графики не отображаются

**Диагностика:**

1. **Проверить Telegraf:**

   ```bash
   # Есть ли метрики?
   curl http://localhost:9091/metrics | grep security_scanners
   
   # Telegraf работает?
   docker compose logs telegraf
   ```

2. **Проверить Prometheus:**

   ```bash
   # Prometheus scraping Telegraf?
   curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets'
   
   # Есть ли метрики в Prometheus?
   curl http://localhost:9090/api/v1/label/__name__/values | grep security
   ```

3. **Проверить Grafana datasource:**

   ```bash
   # Войти в Grafana
   # Configuration → Data Sources → Prometheus
   # Нажать "Test" - должно быть зеленым
   ```

**Решения:**

1. **Перезапустить Telegraf:**

   ```bash
   docker compose restart telegraf
   sleep 10
   ```

2. **Запустить сканирование:**

   ```bash
   # Метрики появляются после первого скана
   make scan
   # или
   ./scripts/scanning/run_hardening_suite.sh
   ```

3. **Проверить Telegraf конфигурацию:**

   ```bash
   # Проверить inputs
   docker exec telegraf telegraf --test --config /etc/telegraf/telegraf.conf
   ```

---

### Не могу войти в Grafana

**Симптомы:**

* "Invalid username or password"
* Страница входа не загружается

**Решения:**

1. **Проверить credentials:**

   ```bash
   # По умолчанию admin/admin
   # Проверьте .env если изменяли
   cat .env | grep GF_ADMIN
   ```

2. **Сбросить пароль:**

   ```bash
   docker compose exec grafana grafana-cli admin reset-admin-password admin
   ```

3. **Проверить доступность:**

   ```bash
   curl http://localhost:3000/api/health
   # Должно вернуть: {"database":"ok"}
   ```

---

## Проблемы с Prometheus

### High memory usage

**Симптомы:**

* Prometheus использует >2GB RAM
* Система тормозит

**Решения:**

1. **Уменьшить retention:**

   ```yaml
   # prometheus/prometheus.yml
   --storage.tsdb.retention.time=15d
   --storage.tsdb.retention.size=5GB
   ```

2. **Уменьшить scrape frequency:**

   ```yaml
   # prometheus/prometheus.yml
   global:
     scrape_interval: 30s  # было 15s
   ```

3. **Удалить старые данные:**

   ```bash
   docker compose down
   rm -rf prometheus-data/*
   docker compose up -d
   ```

---

### Метрики не собираются

**Симптомы:**

* Targets в состоянии "DOWN"
* Gaps в графиках

**Диагностика:**

```bash
# Проверить targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job, health}'
```

**Решения:**

1. **Проверить сетевые имена:**

   ```yaml
   # prometheus/prometheus.yml
   static_configs:
     - targets: ['telegraf:9091']  # не localhost!
   ```

2. **Перезапустить Prometheus:**

   ```bash
   docker compose restart prometheus
   ```

---

## Проблемы с Telegraf

### Telegraf не собирает метрики

**Симптомы:**

```bash
curl http://localhost:9091/metrics
# Пустой ответ или мало метрик
```

**Диагностика:**

```bash
# Тест конфигурации
docker compose exec telegraf telegraf --test

# Проверить логи
docker compose logs telegraf | tail -50
```

**Решения:**

1. **Проверить inputs:**

   ```bash
   # telegraf/telegraf.conf
   [[inputs.exec]]
     commands = [
       "/scripts/parsing/parse_lynis_report.py /reports/lynis/lynis-report.json"
     ]
   ```

2. **Проверить наличие отчетов:**

   ```bash
   ls -la reports/lynis/
   ls -la reports/openscap/
   ```

3. **Запустить сканирование:**

   ```bash
   make scan
   ```

---

## Проблемы со сканированием

### Lynis не запускается

**Симптомы:**

```
Error: Cannot access /hostfs
```

**Решение:**

```yaml
# docker-compose.yml - проверить volumes
volumes:
  - /:/hostfs:ro  # Read-only access к хост системе
```

---

### OpenSCAP fails

**Симптомы:**

```
ERROR: Unable to load XCCDF document
```

**Решения:**

1. **Проверить профиль:**

   ```bash
   # Список доступных профилей
   docker compose exec openscap-scanner \
     oscap info /usr/share/xml/scap/ssg/content/ssg-ubuntu2004-ds.xml
   ```

2. **Использовать другой профиль:**

   ```bash
   export OPENSCAP_PROFILE="xccdf_org.ssgproject.content_profile_cis_level1_server"
   make scan
   ```

---

### SSH сканирование не работает

**Симптомы:**

```
Permission denied (publickey)
```

**Решения:**

1. **Проверить SSH ключ:**

   ```bash
   ssh -i ~/.ssh/scanner_key user@host whoami
   ```

2. **Скопировать ключ:**

   ```bash
   ssh-copy-id -i ~/.ssh/scanner_key.pub user@host
   ```

3. **Проверить права:**

   ```bash
   chmod 600 ~/.ssh/scanner_key
   chmod 644 ~/.ssh/scanner_key.pub
   ```

---

## Проблемы с сетью

### Не могу получить доступ к дашбордам

**Симптомы:**

* Connection refused
* Timeout

**Диагностика:**

```bash
# Проверить порты
docker compose ps

# Проверить файрвол
sudo ufw status

# Проверить доступность
curl -v http://localhost:3000
```

**Решения:**

1. **Открыть порты:**

   ```bash
   sudo ufw allow 3000/tcp   # Grafana
   sudo ufw allow 9090/tcp   # Prometheus
   ```

2. **Проверить binding:**

   ```yaml
   # docker-compose.yml
   ports:
     - "3000:3000"  # не "127.0.0.1:3000:3000"
   ```

---

### DNS не работает внутри контейнеров

**Симптомы:**

```
Could not resolve host
```

**Решение:**

```yaml
# docker-compose.yml
services:
  prometheus:
    dns:
      - 8.8.8.8
      - 8.8.4.4
```

---

## Проблемы с производительностью

### Медленное сканирование

**Причины и решения:**

1. **Слишком много targets:**

   ```yaml
   # Уменьшить количество контейнеров
   # docker-compose.yml
   deploy:
     replicas: 2  # было 5
   ```

2. **Медленный диск:**

   ```bash
   # Использовать tmpfs для reports
   # docker-compose.yml
   tmpfs:
     - /reports
   ```

3. **Параллелизация:**

   ```bash
   # Запускать сканеры параллельно
   ./scripts/scanning/run_lynis.sh &
   ./scripts/scanning/run_openscap.sh &
   wait
   ```

---

### Build занимает много времени

**Решения:**

1. **Использовать BuildKit:**

   ```bash
   export DOCKER_BUILDKIT=1
   docker compose build
   ```

2. **Использовать cache:**

   ```dockerfile
   # Используйте RUN --mount=type=cache
   RUN --mount=type=cache,target=/var/cache/apt \
       apt-get update && apt-get install -y package
   ```

3. **Multi-stage builds уже используются:**

   ```dockerfile
   FROM python:3.11-slim as builder
   # ...
   FROM python:3.11-slim
   COPY --from=builder /app /app
   ```

---

## Проблемы с безопасностью

### Atomic Red Team тесты вносят изменения

**Симптомы:**

* Файлы создаются/изменяются
* Процессы запускаются

**Решение:**

По умолчанию **dry-run включен:**

```yaml
# docker-compose.yml
environment:
  - ATOMIC_DRY_RUN=true
```

Для реальных тестов (ТОЛЬКО в изолированных окружениях):

```bash
ATOMIC_DRY_RUN=false docker compose up atomic-test
```

---

### Подозрительная активность в логах

**Что делать:**

1. **Проверить Loki logs:**

   ```bash
   # Через Grafana Explore
   {job="docker"} |= "error"
   ```

2. **Проверить Prometheus alerts:**

   ```bash
   curl http://localhost:9090/api/v1/alerts
   ```

3. **Проверить Alertmanager:**

   ```bash
   curl http://localhost:9093/api/v2/alerts
   ```

---

## Диагностические команды

### Быстрая проверка здоровья

```bash
# Все в одном
./scripts/monitoring/health_check.sh

# Или вручную:
curl -sf http://localhost:9090/-/healthy && echo "Prometheus OK"
curl -sf http://localhost:3000/api/health && echo "Grafana OK"
curl -sf http://localhost:9091/metrics > /dev/null && echo "Telegraf OK"
curl -sf http://localhost:9093/-/healthy && echo "Alertmanager OK"
```

---

### Сбор диагностики

```bash
# Создать diagnostic bundle
mkdir -p diagnostics
docker compose ps > diagnostics/ps.txt
docker compose logs > diagnostics/logs.txt
docker stats --no-stream > diagnostics/stats.txt
docker system df > diagnostics/df.txt
cp docker-compose.yml diagnostics/
cp .env diagnostics/env.txt

tar czf diagnostics-$(date +%Y%m%d).tar.gz diagnostics/
```

---

## Полный сброс

Если ничего не помогает:

```bash
# WARNING: Удалит все данные!

# Остановить и удалить все
docker compose down -v

# Очистить Docker
docker system prune -a --volumes

# Пересоздать
docker compose up -d --build

# Подождать
sleep 60

# Запустить сканирование
make scan
```

---

## Получение помощи

Если проблема не решается:

1. **Проверьте документацию:**
   * [FAQ](FAQ.md)
   * [DEPLOYMENT.md](DEPLOYMENT.md)
   * [SECURITY.md](SECURITY.md)

2. **Создайте issue:**
   * [GitHub Issues](https://github.com/alexbergh/test-hard/issues)
   * Приложите диагностику
   * Опишите шаги воспроизведения

3. **Укажите:**
   * Версию Docker/Docker Compose
   * OS и версию
   * Логи ошибок
   * Конфигурацию (без секретов!)

---

**Обновлено:** 24.11.2025
