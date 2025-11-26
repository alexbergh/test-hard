# Часто задаваемые вопросы (FAQ)

## Общие вопросы

### Что такое test-hard?

test-hard - это автоматизированная платформа для security hardening и мониторинга контейнеров. Она включает security сканирование (OpenSCAP, Lynis), мониторинг (Prometheus, Grafana), атомарные тесты (Atomic Red Team) и сбор метрик безопасности через Telegraf.

### Для кого предназначен проект?

* DevOps инженеры
* Security специалисты
* System administrators
* Разработчики, заботящиеся о безопасности

### Какие Linux дистрибутивы поддерживаются?

Сканирование поддерживает:

* Debian / Ubuntu
* Fedora
* CentOS Stream
* ALT Linux
* RHEL-based системы
* BSD системы (ограниченная поддержка)

## Установка и настройка

### Какие требования для запуска?

**Минимальные:**

* Docker 20.10+
* Docker Compose v2.0+
* 2 CPU, 4 GB RAM, 10 GB disk

**Рекомендуемые:**

* Docker 24.0+
* Docker Compose v2.20+
* 4 CPU, 8 GB RAM, 50 GB disk

### Как быстро развернуть платформу?

```bash
git clone https://github.com/alexbergh/test-hard.git
cd test-hard
make up
```

См. [QUICKSTART.md](QUICKSTART.md) для подробностей.

### Нужно ли менять пароли по умолчанию?

**Да!** Для production обязательно:

```bash
cp .env.example .env
nano .env  # Измените GF_ADMIN_PASSWORD
```

См. [SECURITY.md](SECURITY.md) для деталей.

### Можно ли запустить без Docker?

Да, есть возможность нативной установки. См. [NATIVE-INSTALLATION.md](NATIVE-INSTALLATION.md).

## Использование

### Как запустить сканирование?

```bash
# Сканирование тестовых контейнеров
make scan

# Сканирование реального хоста
./scripts/scanning/scan-remote-host.sh user@host

# Сканирование production контейнера
docker exec container-name lynis audit system
```

См. [REAL-HOSTS-SCANNING.md](REAL-HOSTS-SCANNING.md).

### Где посмотреть результаты?

**Grafana:** <http://localhost:3000>

* Дашборды с визуализацией метрик
* Login: admin / admin (измените!)

**Prometheus:** <http://localhost:9090>

* Сырые метрики
* Queries и alerts

**Отчеты:**

* HTML: `reports/openscap/*.html`
* JSON: `reports/lynis/*.json`

### Как часто запускать сканирование?

**Рекомендации:**

* Development: по запросу
* Staging: ежедневно
* Production: еженедельно или после изменений

Можно настроить через cron или CI/CD.

### Как добавить свой дашборд в Grafana?

1. Создайте дашборд в UI
2. Export → Save JSON
3. Поместите в `grafana/dashboards/`
4. Пересоберите: `docker compose restart grafana`

## Troubleshooting

### Grafana показывает "No data"

**Причины:**

1. Telegraf не собирает метрики
2. Prometheus не scraping Telegraf
3. Сканирование еще не запускалось

**Решение:**

```bash
# Проверить Telegraf
curl http://localhost:9091/metrics | grep security

# Проверить Prometheus
curl http://localhost:9090/api/v1/label/__name__/values | grep security

# Запустить сканирование
make scan
```

См. [DEPLOYMENT.md#troubleshooting](DEPLOYMENT.md#устранение-неполадок).

### Docker съедает всю память

**Решение:**

1. Ограничить ресурсы в docker-compose.yml (уже настроено)
2. Очистить неиспользуемые ресурсы:

```bash
docker system prune -a
docker volume prune
```

3. Настроить Docker daemon:

```json
{
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  }
}
```

### Контейнеры не запускаются

**Проверьте:**

```bash
# Логи конкретного сервиса
docker compose logs <service>

# Проверка конфигурации
docker compose config

# Проверка портов
ss -tlnp | grep -E '3000|9090|9091|9093'
```

### Скрипт не имеет прав на выполнение

```bash
chmod +x scripts/**/*.sh
# или
find scripts -name "*.sh" -exec chmod +x {} \;
```

### Ошибка "Permission denied" при доступе к Docker

**Не добавляйте пользователя в docker group!**

Используйте:

* Docker Socket Proxy (рекомендуется)
* sudo с ограниченными правами
* Rootless Docker

См. [USER-SETUP.md](USER-SETUP.md).

## Security

### Безопасно ли использовать в production?

Да, при соблюдении рекомендаций:

* Измените пароли по умолчанию
* Используйте Docker Socket Proxy
* Настройте TLS/SSL
* Ограничьте сетевой доступ
* Регулярно обновляйте компоненты

См. [SECURITY.md](SECURITY.md).

### Как защитить Docker socket?

Используется Docker Socket Proxy:

* Только чтение
* Ограниченные API endpoints
* Нет доступа к VOLUMES, NETWORKS

Настроено по умолчанию в docker-compose.yml.

### Atomic Red Team безопасен?

По умолчанию тесты запускаются в **dry-run режиме** - не вносят изменений.

Для реальных тестов:

```bash
ATOMIC_DRY_RUN=false docker compose up
```

**Только в изолированных тестовых окружениях!**

### Как ротировать SSH ключи?

```bash
# Автоматически
./scripts/setup/rotate-ssh-keys.sh scanner-user

# Вручную
ssh-keygen -t ed25519 -f ~/.ssh/scanner_key_new
ssh-copy-id -i ~/.ssh/scanner_key_new.pub user@host
```

См. [USER-SETUP.md](USER-SETUP.md).

## Мониторинг

### Как настроить алерты?

1. Настройте Alertmanager в `prometheus/alertmanager.yml`
2. Добавьте правила в `prometheus/alert.rules.yml`
3. Перезапустите: `docker compose restart alertmanager`

Пример:

```yaml
receivers:
  - name: 'email'
    email_configs:
      - to: 'security@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'
```

### Сколько места занимают данные?

**Примерно:**

* Prometheus data: 1-5 GB (зависит от retention)
* Grafana data: 100-500 MB
* Reports: 50-200 MB
* Loki logs: 500 MB - 2 GB

**Настройка retention:**

```yaml
# prometheus.yml
--storage.tsdb.retention.time=30d
--storage.tsdb.retention.size=10GB
```

### Как экспортировать метрики?

```bash
# Prometheus metrics
curl http://localhost:9090/api/v1/query?query=security_scanners_lynis_score

# Telegraf metrics
curl http://localhost:9091/metrics

# Export в файл
curl http://localhost:9090/api/v1/query?query=security_scanners_lynis_score > metrics.json
```

## Интеграция

### Можно ли интегрировать с Jenkins/GitLab CI?

Да! Пример для GitLab CI:

```yaml
security_scan:
  stage: security
  script:
    - docker compose up -d
    - sleep 30
    - make scan
    - docker compose logs --tail=100
  artifacts:
    paths:
      - reports/
    expire_in: 7 days
```

### Как отправить метрики в внешний Prometheus?

Используйте remote_write:

```yaml
# prometheus.yml
remote_write:
  - url: https://prometheus.example.com/api/v1/write
    basic_auth:
      username: user
      password: pass
```

### Можно ли использовать Kubernetes?

Да! Манифесты находятся в `k8s/`:

```bash
kubectl apply -f k8s/
```

См. [k8s/README.md](../k8s/README.md).

### Есть ли Ansible playbooks?

Да, в директории `playbooks/`:

```bash
ansible-playbook -i hosts.ini playbooks/scan-hosts.yml
```

## Разработка

### Как внести вклад в проект?

См. [CONTRIBUTING.md](../CONTRIBUTING.md).

### Как запустить тесты?

```bash
# Все тесты
make test

# Только unit тесты
pytest tests/unit/

# Shell тесты
bats tests/shell/*.bats

# С coverage
pytest --cov=scripts tests/
```

### Какой стиль кода использовать?

* **Python:** PEP 8, max line 120
* **Bash:** shellcheck compliant
* **YAML:** 2 spaces indent

Используйте pre-commit hooks:

```bash
pre-commit install
pre-commit run --all-files
```

### Как добавить поддержку нового дистрибутива?

1. Создайте Dockerfile в `docker/`
2. Добавьте в docker-compose.yml
3. Обновите парсеры если нужно
4. Добавьте тесты
5. Обновите документацию

## Производительность

### Как ускорить сканирование?

1. Используйте BuildKit cache
2. Запускайте сканеры параллельно
3. Оптимизируйте Docker образы
4. Используйте SSD диски

См. [DOCKER_OPTIMIZATIONS.md](DOCKER_OPTIMIZATIONS.md).

### Как уменьшить использование ресурсов?

1. Настройте resource limits в docker-compose.yml
2. Уменьшите retention period в Prometheus
3. Отключите ненужные сканеры
4. Используйте меньше target контейнеров

## Дополнительно

### Где найти логи?

```bash
# Все логи
docker compose logs

# Конкретный сервис
docker compose logs prometheus

# Follow режим
docker compose logs -f grafana

# Loki logs (если включен)
curl http://localhost:3100/loki/api/v1/query?query={job="docker"}
```

### Как обновить платформу?

```bash
git pull origin main
docker compose pull
docker compose build --pull
docker compose up -d
```

### Есть ли готовые дашборды?

Да, в `grafana/dashboards/`:

* Security Scanners Dashboard
* System Metrics Dashboard
* Logs Analysis Dashboard (Loki)

### Поддерживается ли Windows/macOS?

Да, через Docker Desktop:

* Windows 10/11 + WSL2
* macOS (Intel/Apple Silicon)

**Но:** нативное сканирование только для Linux/BSD.

## Нужна помощь?

1. Проверьте документацию в `docs/`
2. Поищите в [Issues](https://github.com/alexbergh/test-hard/issues)
3. Создайте новый issue с меткой `question`
4. Читайте [CONTRIBUTING.md](../CONTRIBUTING.md)

---

**Не нашли ответ?** Создайте [новый issue](https://github.com/alexbergh/test-hard/issues/new).
