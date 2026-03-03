# Руководство по устранению неполадок

Комплексное руководство по решению типичных проблем в test-hard.

## Содержание

* [Проблемы с Podman](#проблемы-с-podman)
* [Проблемы с Grafana](#проблемы-с-grafana)
* [Проблемы с Prometheus](#проблемы-с-prometheus)
* [Проблемы с Telegraf](#проблемы-с-telegraf)
* [Проблемы со сканированием](#проблемы-со-сканированием)
* [Проблемы с сетью](#проблемы-с-сетью)
* [Проблемы с производительностью](#проблемы-с-производительностью)
* [Проблемы с Falco / Falcosidekick](#проблемы-с-falco--falcosidekick)
* [Проблемы с Trivy](#проблемы-с-trivy)
* [Проблемы с безопасностью](#проблемы-с-безопасностью)

---

## Проблемы с Podman

### Контейнеры не запускаются

**Симптомы:**

```bash
podman-compose up -d
# Контейнеры падают или не запускаются
```

**Диагностика:**

```bash
# Проверить логи
podman-compose logs

# Проверить статус
podman-compose ps

# Проверить конфигурацию
podman-compose config
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
   podman system df
   
   # Очистить
   podman system prune -a
   ```

3. **Проблемы с сетью:**

   ```bash
   # Пересоздать сеть
   podman-compose down
   podman network prune
   podman-compose up -d
   ```

---

### Podman съедает всю память

**Симптомы:**

* Система тормозит
* OOM (Out of Memory) ошибки
* Контейнеры перезапускаются

**Решение:**

1. **Проверить использование:**

   ```bash
   podman stats
   ```

2. **Ограничения уже установлены в podman-compose.yml:**

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

4. **На Windows проверить ресурсы Podman машины:**

   ```bash
   podman machine inspect
   # Увеличить память при необходимости
   podman machine stop
   podman machine set --memory 8192
   podman machine start
   ```

---

### Permission denied при доступе к Podman

**Симптомы:**

```
Got permission denied while trying to connect to the Podman socket
```

**Решение:**

Podman по умолчанию работает в rootless режиме:

1. **Используйте Podman Socket Proxy (уже настроен):**

   ```yaml
   # podman-compose.yml
   podman-proxy:
     image: tecnativa/docker-socket-proxy
     environment:
       - CONTAINERS=1
       - IMAGES=1
       - INFO=1
   ```

2. **Или используйте sudo с ограниченными правами:**

   ```bash
   # /etc/sudoers.d/scanner
   scanner ALL=(ALL) NOPASSWD: /usr/bin/podman
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
   podman-compose logs telegraf
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
   podman-compose restart telegraf
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
   podman exec telegraf telegraf --test --config /etc/telegraf/telegraf.conf
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
   podman exec grafana grafana-cli admin reset-admin-password admin
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
   podman-compose down
   rm -rf prometheus-data/*
   podman-compose up -d
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
   podman-compose restart prometheus
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
podman exec telegraf telegraf --test

# Проверить логи
podman-compose logs telegraf | tail -50
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
# podman-compose.yml - проверить volumes
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
   podman-compose exec openscap-scanner \
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
podman-compose ps

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
   # podman-compose.yml
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
# podman-compose.yml
services:
  prometheus:
    dns:
      - 8.8.8.8
      - 8.8.4.4
```

---

## Проблемы с Falco / Falcosidekick

### Falco Runtime Security дашборд пуст

**Симптомы:**

* Панели показывают 0 или "No data"
* При этом Prometheus содержит метрики `falco_events`

**Диагностика:**

```bash
# Проверить здоровье Falcosidekick
curl http://localhost:2801/healthz

# Проверить метрики в Prometheus
curl -s "http://localhost:9090/api/v1/query?query=falco_events"

# Проверить логи Falcosidekick
podman-compose logs falcosidekick --tail 20
```

**Решения:**

1. **Перезапустить Grafana с очисткой кэша:**

   ```bash
   podman-compose restart grafana
   ```

2. **Отправить тестовые события:**

   ```bash
   python3 scripts/send_falco_events.py
   ```

3. **Пересоздать volume Grafana (крайняя мера):**

   ```bash
   podman-compose down grafana
   podman volume rm test-hard_grafana-data
   podman-compose up -d grafana
   ```

---

### Falcosidekick не пересылает события

**Симптомы:**

* `falcosidekick_outputs` метрика не растет
* Логи Loki не содержат Falco-событий

**Решение:**

```bash
# Проверить конфигурацию outputs
podman exec falcosidekick cat /etc/falcosidekick/config.yaml

# Проверить доступность Loki из контейнера
podman exec falcosidekick wget -qO- http://loki:3100/ready
```

---

## Проблемы с Trivy

### Trivy метрики не появляются в Prometheus

**Симптомы:**

* `trivy_trivy_vulnerabilities_total` отсутствует в Prometheus
* Container Image Security дашборд пуст

**Диагностика:**

```bash
# Проверить наличие .prom файлов
ls reports/trivy/*_metrics.prom

# Проверить логи Telegraf на ошибки парсинга
podman logs telegraf --tail 20 2>&1 | grep -i "trivy\|error"
```

**Решения:**

1. **Проблема с CRLF:** Файлы `.prom`, созданные на Windows, могут иметь `\r\n` переносы. Telegraf ожидает Unix LF (`\n`). Ошибка в логах: `unknown metric type "gauge\r"`.

   ```bash
   # Исправить переносы строк
   python3 scripts/fix_prom_metrics.py
   ```

2. **Пересканировать образы:**

   ```bash
   python3 scripts/scan_all_images.py
   ```

3. **Проверить формат метрик:** Файлы должны использовать отдельные метрики по серьезности (`trivy_vulnerabilities_critical`, `trivy_vulnerabilities_high`, и т.д.), а не labels `severity="critical"`.

---

## Проблемы с производительностью

### Медленное сканирование

**Причины и решения:**

1. **Слишком много targets:**

   ```yaml
   # Уменьшить количество контейнеров
   # podman-compose.yml
   deploy:
     replicas: 2  # было 5
   ```

2. **Медленный диск:**

   ```bash
   # Использовать tmpfs для reports
   # podman-compose.yml
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

1. **Использовать Buildah cache:**

   ```bash
   # Podman использует Buildah с поддержкой cache mounts
   podman-compose build
   ```

2. **Использовать cache:**

   ```containerfile
   # Используйте RUN --mount=type=cache
   RUN --mount=type=cache,target=/var/cache/apt \
       apt-get update && apt-get install -y package
   ```

3. **Multi-stage builds уже используются:**

   ```containerfile
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
# podman-compose.yml
environment:
  - ATOMIC_DRY_RUN=true
```

Для реальных тестов (ТОЛЬКО в изолированных окружениях):

```bash
ATOMIC_DRY_RUN=false podman-compose up atomic-test
```

---

### Подозрительная активность в логах

**Что делать:**

1. **Проверить Loki logs:**

   ```bash
   # Через Grafana Explore
   {job="podman"} |= "error"
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
podman-compose ps > diagnostics/ps.txt
podman-compose logs > diagnostics/logs.txt
podman stats --no-stream > diagnostics/stats.txt
podman system df > diagnostics/df.txt
cp podman-compose.yml diagnostics/
cp .env diagnostics/env.txt

tar czf diagnostics-$(date +%Y%m%d).tar.gz diagnostics/
```

---

## Полный сброс

Если ничего не помогает:

```bash
# WARNING: Удалит все данные!

# Остановить и удалить все
podman-compose down -v

# Очистить Podman
podman system prune -a --volumes

# Пересоздать
podman-compose up -d --build

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
   * Версию Podman/podman-compose
   * OS и версию
   * Логи ошибок
   * Конфигурацию (без секретов!)

---

**Обновлено:** Март 2026
