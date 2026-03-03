# Podman оптимизации

Документация по внедренным Podman оптимизациям в проект test-hard.

## Содержание

* [Обзор](#обзор)
* [Внедренные фичи](#внедренные-фичи)
* [Ожидаемые улучшения](#ожидаемые-улучшения)
* [Использование](#использование)
* [Тестирование](#тестирование)

## Обзор

В проект внедрены продвинутые Podman-фичи для оптимизации размера образов, скорости сборки и безопасности:

1. **Специфичные .containerignore файлы**
2. **HEALTHCHECK в Containerfile**
3. **Multi-stage builds**
4. **Buildah cache mounts**
5. **Оптимизированный CI/CD**

## Внедренные фичи

### 1. Специфичные .containerignore файлы

Каждый Containerfile теперь имеет свой `.containerignore` файл, что минимизирует build context.

**Структура:**

```
containers/ubuntu/.containerignore
containers/debian/.containerignore
scanners/lynis/.containerignore
scanners/openscap/.containerignore
telegraf/.containerignore
```

**Преимущества:**

* Уменьшение размера build context
* Ускорение передачи файлов в Podman
* Предотвращение утечки секретов

### 2. HEALTHCHECK

Добавлены health checks в `telegraf/Containerfile`:

```containerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:9091/metrics || exit 1
```

**Преимущества:**

* Автоматическое определение состояния контейнера
* Интеграция с оркестраторами (Podman pods, K8s)
* Улучшенный мониторинг

### 3. Multi-stage builds

Все основные Containerfile рефакторены с использованием multi-stage builds.

**Пример (Ubuntu):**

```containerfile
# syntax=containers/containerfile:1.4

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

* `containers/ubuntu/Containerfile`
* `containers/debian/Containerfile`
* `containers/fedora/Containerfile`
* `containers/centos/Containerfile`
* `containers/altlinux/Containerfile`
* `containers/astra/Containerfile`
* `containers/redos/Containerfile`

**Преимущества:**

* Уменьшение размера финального образа на 40-70%
* Исключение build-зависимостей из production образа
* Повышение безопасности

### 4. Buildah cache mounts

Все Containerfile используют cache mounts для ускорения сборки:

**Для APT (Debian/Ubuntu):**

```containerfile
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y python3
```

**Для DNF (Fedora/CentOS):**

```containerfile
RUN --mount=type=cache,target=/var/cache/dnf,sharing=locked \
    dnf install -y python3
```

**Для PIP:**

```containerfile
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install atomic-operator attrs click pyyaml
```

**Преимущества:**

* Кэширование пакетов между сборками
* Ускорение повторных сборок в 3-5 раз
* Экономия трафика

### 5. Оптимизированный CI/CD

GitHub Actions workflows обновлены для использования Buildah:

**Ключевые изменения:**

```yaml
- name: Set up Podman Buildx
  uses: docker/setup-buildx-action@v3
  with:
    driver-opts: |
      image=moby/buildkit:latest
      network=host

- name: Cache Podman layers
  uses: actions/cache@v3
  with:
    path: /tmp/.buildx-cache
    key: ${{ runner.os }}-buildx-${{ hashFiles('**/Containerfile*') }}-${{ github.sha }}

- name: Build Podman images
  env:
    BUILDAH_FORMAT: docker
    BUILDKIT_PROGRESS: plain
  run: podman-compose build --parallel --build-arg BUILDKIT_INLINE_CACHE=1
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
# Сборка всех образов
podman-compose build

# Сборка конкретного образа
podman build -f containers/ubuntu/Containerfile -t test-ubuntu .

# Проверка размера образов
podman images | grep test-hard
```

### Очистка кэша

```bash
# Очистка build cache (освобождает место)
podman system prune

# Агрессивная очистка (все слои)
podman system prune -a --volumes

# Очистка только образов
podman image prune -a
```

### Просмотр статистики кэша

```bash
# Статистика использования диска
podman system df

# Детальная информация
podman system df -v
```

## Тестирование

### Проверка multi-stage builds

```bash
# Сборка Ubuntu образа
podman build -f containers/ubuntu/Containerfile -t test-ubuntu .

# Проверка размера
podman images test-ubuntu

# Проверка слоев
podman history test-ubuntu
```

### Проверка HEALTHCHECK

```bash
# Запуск telegraf
podman-compose up -d telegraf

# Проверка health status
podman ps
# Столбец STATUS покажет "healthy" или "unhealthy"

# Детальная информация
podman inspect --format='{{json .State.Health}}' telegraf | jq
```

### Проверка cache mounts

```bash
# Первая сборка (создание кэша)
time podman build -f containers/ubuntu/Containerfile .

# Вторая сборка (использование кэша)
time podman build -f containers/ubuntu/Containerfile .
# Должна быть значительно быстрее
```

### Сравнение размеров

```bash
# До оптимизации (если есть старая версия)
podman images | grep -E "test-hard.*(ubuntu|debian|fedora)" 

# Подсчет общего размера
podman images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | \
  grep test-hard | \
  awk '{print $3}' | \
  sed 's/MB//' | \
  awk '{sum+=$1} END {print "Total:", sum, "MB"}'
```

## Дополнительные ресурсы

* [Podman Documentation](https://docs.podman.io/)
* [Buildah Documentation](https://buildah.io/)
* [Multi-stage builds best practices](https://docs.podman.io/en/latest/markdown/podman-build.1.html)
* [Containerfile reference](https://github.com/containers/common/blob/main/docs/Containerfile.5.md)

## Troubleshooting

### Podman не работает (Linux)

```bash
# Проверка версии Podman
podman version

# Проверка статуса сервиса
systemctl --user status podman.socket

# Запуск сокета
systemctl --user enable --now podman.socket
```

### Podman не работает (Windows)

```powershell
# Проверка статуса машины
podman machine list

# Запуск машины
podman machine start

# Запуск API на TCP (для доступа из контейнеров)
podman machine ssh "podman system service --time=0 tcp:0.0.0.0:2375 &"
```

**Важно:** На Windows контейнеры используют `host.containers.internal:2375` для доступа к Podman API.

### Кэш не используется

```bash
# Очистка и пересборка
podman system prune -a
podman-compose build --no-cache

# Проверка .containerignore
cat containers/ubuntu/.containerignore
```

### Ошибки при multi-stage build

```bash
# Сборка с детальным выводом
podman build --log-level=debug -f containers/ubuntu/Containerfile .
```

## Changelog

### 2026-03-02

* Миграция с Podman на Podman
* Обновлены все команды и примеры для Podman
* Добавлены ссылки на документацию Podman/Buildah

### 2025-11-21

* Добавлены специфичные .containerignore файлы для всех Containerfile
* Добавлен HEALTHCHECK в telegraf/Containerfile
* Внедрены multi-stage builds для всех основных образов
* Добавлены Buildah cache mounts (apt, dnf, yum, pip)
* Оптимизированы GitHub Actions workflows
* Обновлена документация

## Следующие шаги

1. **Мониторинг производительности:** Отслеживать метрики сборки в CI/CD
2. **Дальнейшая оптимизация:** Рассмотреть использование distroless базовых образов
3. **Secret management:** Внедрить `--mount=type=secret` для приватных зависимостей
4. **Registry caching:** Настроить pull-through cache для container registries
