# Часто задаваемые вопросы (FAQ)

## Общие вопросы

### Что такое test-hard?

test-hard -- автоматизированная платформа для security hardening, runtime-безопасности и мониторинга контейнеров. Включает security-сканирование (OpenSCAP, Lynis), runtime-защиту (Falco + Falcosidekick), сканирование образов (Trivy), сетевое сканирование (nmap), мониторинг (Prometheus, Grafana, 10 дашбордов), централизованное логирование (Loki + Promtail), атомарные тесты (Atomic Red Team) и сбор метрик безопасности через Telegraf.

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

* Podman 4.0+
* podman-compose 1.0+
* 2 CPU, 4 GB RAM, 10 GB disk

**Рекомендуемые:**

* Podman 5.0+
* podman-compose 1.2+
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

### Можно ли запустить без Podman?

Да, есть возможность нативной установки. См. [NATIVE-INSTALLATION.md](NATIVE-INSTALLATION.md).

## Использование

### Как запустить сканирование?

```bash
# Сканирование тестовых контейнеров
make scan

# Сканирование реального хоста
./scripts/scanning/scan-remote-host.sh user@host

# Сканирование production контейнера
podman exec container-name lynis audit system
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
4. Пересоберите: `podman-compose restart grafana`

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

### Podman съедает всю память

**Решение:**

1. Ограничить ресурсы в podman-compose.yml (уже настроено)
2. Очистить неиспользуемые ресурсы:

```bash
podman system prune -a
podman volume prune
```

3. На Windows проверить ресурсы Podman машины:

```bash
podman machine inspect
```

### Ошибка "denied" при pull образов из GHCR

При запуске `podman-compose up` появляется ошибка:

```
Error response from daemon: denied
```

**Причина:** Образы `openscap-scanner`, `lynis-scanner` и `telegraf` используют unified image из GitHub Container Registry (`ghcr.io/alexbergh/test-hard`), который может быть приватным.

**Решение 1 — Авторизоваться в GHCR:**

```bash
# Создайте Personal Access Token на GitHub с правами read:packages
# https://github.com/settings/tokens

echo $GITHUB_TOKEN | podman login ghcr.io -u YOUR_USERNAME --password-stdin
```

**Решение 2 — Собрать образ локально:**

```bash
# В корне проекта
podman build -t ghcr.io/alexbergh/test-hard:latest .

# Затем запустить как обычно
podman-compose up -d
```

**Решение 3 — Использовать dev-конфигурацию с локальной сборкой:**

```bash
podman-compose -f podman-compose.dev.yml up -d --build
```

### Контейнеры не запускаются

**Проверьте:**

```bash
# Логи конкретного сервиса
podman-compose logs <service>

# Проверка конфигурации
podman-compose config

# Проверка портов
ss -tlnp | grep -E '3000|9090|9091|9093'
```

### Скрипт не имеет прав на выполнение

```bash
chmod +x scripts/**/*.sh
# или
find scripts -name "*.sh" -exec chmod +x {} \;
```

### Ошибка "Permission denied" при доступе к Podman

**Используйте rootless Podman (рекомендуется):**

* Podman Socket Proxy
* sudo с ограниченными правами
* Rootless Podman (по умолчанию)

См. [USER-SETUP.md](USER-SETUP.md).

## Security

### Безопасно ли использовать в production?

Да, при соблюдении рекомендаций:

* Измените пароли по умолчанию
* Используйте Podman Socket Proxy
* Настройте TLS/SSL
* Ограничьте сетевой доступ
* Регулярно обновляйте компоненты

См. [SECURITY.md](SECURITY.md).

### Как защитить Podman socket?

Используется Podman Socket Proxy:

* Только чтение
* Ограниченные API endpoints
* Нет доступа к VOLUMES, NETWORKS

Настроено по умолчанию в podman-compose.yml.

### Atomic Red Team безопасен?

По умолчанию тесты запускаются в **dry-run режиме** - не вносят изменений.

Для реальных тестов:

```bash
ATOMIC_DRY_RUN=false podman-compose up
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
3. Перезапустите: `podman-compose restart alertmanager`

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
    - podman-compose up -d
    - sleep 30
    - make scan
    - podman-compose logs --tail=100
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

1. Создайте Containerfile в `containers/`
2. Добавьте в podman-compose.yml
3. Обновите парсеры если нужно
4. Добавьте тесты
5. Обновите документацию

## Производительность

### Как ускорить сканирование?

1. Используйте BuildKit cache
2. Запускайте сканеры параллельно
3. Оптимизируйте Podman образы
4. Используйте SSD диски

См. [PODMAN_OPTIMIZATIONS.md](PODMAN_OPTIMIZATIONS.md).

### Как уменьшить использование ресурсов?

1. Настройте resource limits в podman-compose.yml
2. Уменьшите retention period в Prometheus
3. Отключите ненужные сканеры
4. Используйте меньше target контейнеров

## Дополнительно

### Где найти логи?

```bash
# Все логи
podman-compose logs

# Конкретный сервис
podman-compose logs prometheus

# Follow режим
podman-compose logs -f grafana

# Loki logs (если включен)
curl http://localhost:3100/loki/api/v1/query?query={job="podman"}
```

### Как обновить платформу?

```bash
git pull origin main
podman-compose pull
podman-compose build
podman-compose up -d
```

### Есть ли готовые дашборды?

Да, в `grafana/dashboards/` находятся 10 преднастроенных дашбордов:

* Security Overview -- общий обзор безопасности
* Security Monitoring -- метрики сканеров в динамике
* Security Issues Details -- таблицы проблем Lynis/OpenSCAP
* Host Compliance -- соответствие по хостам
* Falco Runtime Security -- runtime-события Falco
* Container Image Security -- уязвимости образов Trivy
* Network Security Monitoring -- трафик, пакеты, ошибки, TCP
* Network Discovery -- хосты, порты, сервисы
* System Resources -- CPU, память, диск, сеть
* Logs Analysis -- анализ логов через Loki

### Поддерживается ли Windows/macOS?

Да, через Podman:

* Windows 10/11 + Podman Machine
* macOS (Intel/Apple Silicon) + Podman Machine

**Важно для Windows:** Запустите Podman API на TCP:

```bash
podman machine ssh "podman system service --time=0 tcp:0.0.0.0:2375 &"
```

И используйте `tcp://host.containers.internal:2375` для подключения из контейнеров.

**Но:** нативное сканирование только для Linux/BSD.

## Нужна помощь?

1. Проверьте документацию в `docs/`
2. Поищите в [Issues](https://github.com/alexbergh/test-hard/issues)
3. Создайте новый issue с меткой `question`
4. Читайте [CONTRIBUTING.md](../CONTRIBUTING.md)

---

**Не нашли ответ?** Создайте [новый issue](https://github.com/alexbergh/test-hard/issues/new).

Последнее обновление: Март 2026
