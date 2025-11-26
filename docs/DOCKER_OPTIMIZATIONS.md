# Docker оптимизации

Документация по внедренным Docker оптимизациям в проект test-hard.

## Содержание

* [Обзор](#обзор)
* [Внедренные фичи](#внедренные-фичи)
* [Ожидаемые улучшения](#ожидаемые-улучшения)
* [Использование](#использование)
* [Тестирование](#тестирование)

## Обзор

В проект внедрены продвинутые Docker-фичи для оптимизации размера образов, скорости сборки и безопасности:

1. **Специфичные .dockerignore файлы**
2. **HEALTHCHECK в Dockerfile**
3. **Multi-stage builds**
4. **BuildKit cache mounts**
5. **Оптимизированный CI/CD**

## Внедренные фичи

### 1. Специфичные .dockerignore файлы

Каждый Dockerfile теперь имеет свой `.dockerignore` файл, что минимизирует build context.

**Структура:**

```
docker/ubuntu/Dockerfile.dockerignore
docker/debian/Dockerfile.dockerignore
scanners/lynis/Dockerfile.dockerignore
scanners/openscap/Dockerfile.dockerignore
telegraf/Dockerfile.dockerignore
```

**Преимущества:**

* Уменьшение размера build context
* Ускорение передачи файлов в Docker daemon
* Предотвращение утечки секретов

### 2. HEALTHCHECK

Добавлены health checks в `telegraf/Dockerfile`:

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:9091/metrics || exit 1
```

**Преимущества:**

* Автоматическое определение состояния контейнера
* Интеграция с оркестраторами (Docker Swarm, K8s)
* Улучшенный мониторинг

### 3. Multi-stage builds

Все основные Dockerfile рефакторены с использованием multi-stage builds.

**Пример (Ubuntu):**

```dockerfile
# syntax=docker/dockerfile:1.4

# Stage 1: Builder
FROM ubuntu:22.04 AS builder
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv
RUN python3 -m venv /opt/venv
RUN /opt/venv/bin/pip install atomic-operator attrs click pyyaml

# Stage 2: Runtime
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y sudo python3 curl wget
COPY --from=builder /opt/venv /opt/venv
```

**Обновленные образы:**

* `docker/ubuntu/Dockerfile`
* `docker/debian/Dockerfile`
* `docker/fedora/Dockerfile`
* `docker/centos/Dockerfile`
* `docker/altlinux/Dockerfile`
* `docker/astra/Dockerfile`
* `docker/redos/Dockerfile`

**Преимущества:**

* Уменьшение размера финального образа на 40-70%
* Исключение build-зависимостей из production образа
* Повышение безопасности

### 4. BuildKit cache mounts

Все Dockerfile используют cache mounts для ускорения сборки:

**Для APT (Debian/Ubuntu):**

```dockerfile
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y python3
```

**Для DNF (Fedora/CentOS):**

```dockerfile
RUN --mount=type=cache,target=/var/cache/dnf,sharing=locked \
    dnf install -y python3
```

**Для PIP:**

```dockerfile
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install atomic-operator attrs click pyyaml
```

**Преимущества:**

* Кэширование пакетов между сборками
* Ускорение повторных сборок в 3-5 раз
* Экономия трафика

### 5. Оптимизированный CI/CD

GitHub Actions workflows обновлены для использования BuildKit:

**Ключевые изменения:**

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3
  with:
    driver-opts: |
      image=moby/buildkit:latest
      network=host

- name: Cache Docker layers
  uses: actions/cache@v3
  with:
    path: /tmp/.buildx-cache
    key: ${{ runner.os }}-buildx-${{ hashFiles('**/Dockerfile*') }}-${{ github.sha }}

- name: Build Docker images
  env:
    DOCKER_BUILDKIT: 1
    BUILDKIT_PROGRESS: plain
  run: docker compose build --parallel --build-arg BUILDKIT_INLINE_CACHE=1
```

**Преимущества:**

* Кэширование слоев между CI запусками
* Параллельная сборка образов
* Детальный прогресс сборки

## Ожидаемые улучшения

### Размер образов

| Образ | До оптимизации | После оптимизации | Экономия |
|-------|----------------|-------------------|----------|
| Ubuntu | ~800 MB | ~400-500 MB | 40-50% |
| Debian | ~700 MB | ~350-450 MB | 40-50% |
| Fedora | ~900 MB | ~450-550 MB | 45-50% |
| CentOS | ~850 MB | ~450-550 MB | 45-50% |

### Скорость сборки

| Сценарий | До оптимизации | После оптимизации | Улучшение |
|----------|----------------|-------------------|-----------|
| Первая сборка | 15-20 мин | 15-20 мин | 0% |
| Повторная сборка (без изменений) | 10-15 мин | 2-3 мин | 80% |
| Повторная сборка (с изменениями) | 12-18 мин | 4-6 мин | 65% |
| CI/CD pipeline | 25-30 мин | 12-15 мин | 50% |

### CI/CD

* **Экономия GitHub Actions минут:** ~50%
* **Ускорение feedback loop:** 2x
* **Снижение network traffic:** 60-70%

## Использование

### Локальная сборка

```bash
# Включить BuildKit (если не установлено глобально)
export DOCKER_BUILDKIT=1

# Сборка всех образов
docker compose build

# Сборка с параллелизацией
docker compose build --parallel

# Сборка конкретного образа
docker compose build ubuntu

# Проверка размера образов
docker images | grep test-hard
```

### Очистка кэша

```bash
# Очистка build cache (освобождает место)
docker builder prune

# Агрессивная очистка (все слои)
docker builder prune -a

# Очистка с указанием возраста
docker builder prune --filter "until=24h"
```

### Просмотр статистики кэша

```bash
# Статистика использования кэша
docker buildx du

# Детальная информация
docker system df -v
```

## Тестирование

### Проверка multi-stage builds

```bash
# Сборка Ubuntu образа
docker build -f docker/ubuntu/Dockerfile -t test-ubuntu .

# Проверка размера
docker images test-ubuntu

# Проверка слоев
docker history test-ubuntu
```

### Проверка HEALTHCHECK

```bash
# Запуск telegraf
docker compose up -d telegraf

# Проверка health status
docker ps
# Столбец STATUS покажет "healthy" или "unhealthy"

# Детальная информация
docker inspect --format='{{json .State.Health}}' telegraf | jq
```

### Проверка cache mounts

```bash
# Первая сборка (создание кэша)
time docker build -f docker/ubuntu/Dockerfile .

# Вторая сборка (использование кэша)
time docker build -f docker/ubuntu/Dockerfile .
# Должна быть значительно быстрее
```

### Сравнение размеров

```bash
# До оптимизации (если есть старая версия)
docker images | grep -E "test-hard.*(ubuntu|debian|fedora)" 

# Подсчет общего размера
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | \
  grep test-hard | \
  awk '{print $3}' | \
  sed 's/MB//' | \
  awk '{sum+=$1} END {print "Total:", sum, "MB"}'
```

## Дополнительные ресурсы

- [Docker BuildKit Documentation](https://docs.docker.com/build/buildkit/)
- [Multi-stage builds best practices](https://docs.docker.com/build/building/multi-stage/)
- [BuildKit cache mounts](https://docs.docker.com/build/guide/mounts/)
- [HEALTHCHECK instruction](https://docs.docker.com/engine/reference/builder/#healthcheck)

## Troubleshooting

### BuildKit не работает

```bash
# Проверка версии Docker
docker version

# Включение BuildKit
export DOCKER_BUILDKIT=1

# Или в daemon.json
{
  "features": {
    "buildkit": true
  }
}
```

### Кэш не используется

```bash
# Очистка и пересборка
docker builder prune -a
docker compose build --no-cache

# Проверка .dockerignore
cat docker/ubuntu/Dockerfile.dockerignore
```

### Ошибки при multi-stage build

```bash
# Проверка синтаксиса
docker build --check -f docker/ubuntu/Dockerfile .

# Сборка с детальным выводом
BUILDKIT_PROGRESS=plain docker build -f docker/ubuntu/Dockerfile .
```

## Changelog

### 2024-11-21

* Добавлены специфичные .dockerignore файлы для всех Dockerfile
* Добавлен HEALTHCHECK в telegraf/Dockerfile
* Внедрены multi-stage builds для всех основных образов
* Добавлены BuildKit cache mounts (apt, dnf, yum, pip)
* Оптимизированы GitHub Actions workflows для использования BuildKit
* Обновлена документация

## Следующие шаги

1. **Мониторинг производительности:** Отслеживать метрики сборки в CI/CD
2. **Дальнейшая оптимизация:** Рассмотреть использование distroless базовых образов
3. **Secret management:** Внедрить `--mount=type=secret` для приватных зависимостей
4. **Registry caching:** Настроить pull-through cache для Docker Hub
