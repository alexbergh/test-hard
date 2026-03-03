# Локальная сборка образа

Данная инструкция описывает процесс локальной сборки unified образа для проекта test-hard с использованием Podman.

## Когда нужна локальная сборка?

- Ошибка `denied` при pull образов из GHCR
- Нет доступа к GitHub Container Registry
- Необходимость внести изменения в образ
- Работа в изолированной среде без интернета

## Требования

- Podman 4.0+ (рекомендуется 5.0+)
- podman-compose 1.0+
- Git
- Минимум 2 GB свободного места на диске

## Быстрая сборка

```bash
# Клонировать репозиторий (если еще не сделано)
git clone https://github.com/alexbergh/test-hard.git
cd test-hard

# Собрать unified image
podman build -t ghcr.io/alexbergh/test-hard:latest .

# Запустить платформу
podman-compose up -d
```

## Пошаговая инструкция

### 1. Проверка окружения

```bash
# Проверить версию Podman
podman --version

# Проверить версию podman-compose
podman-compose version

# Проверить доступное место
podman system df
```

### 2. Сборка образа

```bash
# Стандартная сборка
podman build -t ghcr.io/alexbergh/test-hard:latest .

# Сборка с отключенным кэшем (при проблемах)
podman build --no-cache -t ghcr.io/alexbergh/test-hard:latest .

# Сборка с указанием платформы (для Apple Silicon)
podman build --platform linux/amd64 -t ghcr.io/alexbergh/test-hard:latest .
```

### 3. Проверка образа

```bash
# Проверить что образ создан
podman images | grep test-hard

# Проверить размер образа
podman image inspect ghcr.io/alexbergh/test-hard:latest --format='{{.Size}}'

# Проверить доступные команды
podman run --rm ghcr.io/alexbergh/test-hard:latest --help
```

### 4. Запуск платформы

```bash
# Запуск всех сервисов
podman-compose up -d

# Проверка статуса
podman-compose ps

# Просмотр логов
podman-compose logs -f
```

## Использование podman-compose.dev.yml

Для разработки рекомендуется использовать dev-конфигурацию, которая автоматически собирает образ:

```bash
# Сборка и запуск в одну команду
podman-compose -f podman-compose.dev.yml up -d --build

# Пересборка после изменений
podman-compose -f podman-compose.dev.yml build --no-cache
podman-compose -f podman-compose.dev.yml up -d
```

## Сборка с использованием Makefile

```bash
# Сборка образа
make build

# Сборка и запуск
make up

# Полная пересборка
make rebuild
```

## Тегирование образов

```bash
# Добавить дополнительный тег
podman tag ghcr.io/alexbergh/test-hard:latest ghcr.io/alexbergh/test-hard:v1.0.0

# Тег для локального использования
podman tag ghcr.io/alexbergh/test-hard:latest test-hard:local
```

## Оптимизация сборки

### Использование Buildah cache

```bash
# Podman использует Buildah для сборки с поддержкой cache mounts
podman build -t ghcr.io/alexbergh/test-hard:latest .
```

### Многоэтапная сборка с кэшем

```bash
# Использовать кэш из registry (если доступен)
podman build \
  --cache-from ghcr.io/alexbergh/test-hard:latest \
  -t ghcr.io/alexbergh/test-hard:latest .
```

## Устранение неполадок

### Ошибка "no space left on device"

```bash
# Очистить неиспользуемые ресурсы
podman system prune -a

# Очистить build cache
podman system prune --all --volumes
```

### Ошибка при сборке на Apple Silicon

```bash
# Использовать эмуляцию amd64
podman build --platform linux/amd64 -t ghcr.io/alexbergh/test-hard:latest .
```

### Медленная сборка

```bash
# Podman использует Buildah с поддержкой cache mounts
# Проверьте .containerignore для уменьшения build context
podman build -t ghcr.io/alexbergh/test-hard:latest .
```

### Проверка содержимого образа

```bash
# Запустить shell в контейнере
podman run --rm -it ghcr.io/alexbergh/test-hard:latest /bin/bash

# Проверить установленные инструменты
podman run --rm ghcr.io/alexbergh/test-hard:latest which oscap lynis telegraf
```

## Структура Containerfile

Unified image включает:

- **OpenSCAP** — сканер безопасности
- **Lynis** — аудит безопасности Linux
- **Telegraf** — сбор и отправка метрик
- **Вспомогательные скрипты** — парсеры, entrypoints

## См. также

- [QUICKSTART.md](QUICKSTART.md) — быстрый старт
- [DEPLOYMENT.md](DEPLOYMENT.md) — развертывание
- [PODMAN_OPTIMIZATIONS.md](PODMAN_OPTIMIZATIONS.md) -- оптимизация Podman
- [FAQ.md](FAQ.md) — часто задаваемые вопросы

---

Последнее обновление: Март 2026
