# Локальная сборка Docker образа

Данная инструкция описывает процесс локальной сборки unified Docker образа для проекта test-hard.

## Когда нужна локальная сборка?

- Ошибка `denied` при pull образов из GHCR
- Нет доступа к GitHub Container Registry
- Необходимость внести изменения в образ
- Работа в изолированной среде без интернета

## Требования

- Docker 20.10+ (рекомендуется 24.0+)
- Docker Compose v2.0+
- Git
- Минимум 2 GB свободного места на диске

## Быстрая сборка

```bash
# Клонировать репозиторий (если еще не сделано)
git clone https://github.com/alexbergh/test-hard.git
cd test-hard

# Собрать unified image
docker build -t ghcr.io/alexbergh/test-hard:latest .

# Запустить платформу
docker compose up -d
```

## Пошаговая инструкция

### 1. Проверка окружения

```bash
# Проверить версию Docker
docker --version

# Проверить версию Docker Compose
docker compose version

# Проверить доступное место
docker system df
```

### 2. Сборка образа

```bash
# Стандартная сборка
docker build -t ghcr.io/alexbergh/test-hard:latest .

# Сборка с отключенным кэшем (при проблемах)
docker build --no-cache -t ghcr.io/alexbergh/test-hard:latest .

# Сборка с указанием платформы (для Apple Silicon)
docker build --platform linux/amd64 -t ghcr.io/alexbergh/test-hard:latest .
```

### 3. Проверка образа

```bash
# Проверить что образ создан
docker images | grep test-hard

# Проверить размер образа
docker image inspect ghcr.io/alexbergh/test-hard:latest --format='{{.Size}}' | numfmt --to=iec

# Проверить доступные команды
docker run --rm ghcr.io/alexbergh/test-hard:latest --help
```

### 4. Запуск платформы

```bash
# Запуск всех сервисов
docker compose up -d

# Проверка статуса
docker compose ps

# Просмотр логов
docker compose logs -f
```

## Использование docker-compose.dev.yml

Для разработки рекомендуется использовать dev-конфигурацию, которая автоматически собирает образ:

```bash
# Сборка и запуск в одну команду
docker compose -f docker-compose.dev.yml up -d --build

# Пересборка после изменений
docker compose -f docker-compose.dev.yml build --no-cache
docker compose -f docker-compose.dev.yml up -d
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
docker tag ghcr.io/alexbergh/test-hard:latest ghcr.io/alexbergh/test-hard:v1.0.0

# Тег для локального использования
docker tag ghcr.io/alexbergh/test-hard:latest test-hard:local
```

## Оптимизация сборки

### Использование BuildKit

```bash
# Включить BuildKit для ускорения сборки
DOCKER_BUILDKIT=1 docker build -t ghcr.io/alexbergh/test-hard:latest .
```

### Многоэтапная сборка с кэшем

```bash
# Использовать кэш из registry (если доступен)
docker build \
  --cache-from ghcr.io/alexbergh/test-hard:latest \
  -t ghcr.io/alexbergh/test-hard:latest .
```

## Устранение неполадок

### Ошибка "no space left on device"

```bash
# Очистить неиспользуемые ресурсы
docker system prune -a

# Очистить build cache
docker builder prune
```

### Ошибка при сборке на Apple Silicon

```bash
# Использовать эмуляцию amd64
docker build --platform linux/amd64 -t ghcr.io/alexbergh/test-hard:latest .
```

### Медленная сборка

```bash
# Проверить что BuildKit включен
export DOCKER_BUILDKIT=1

# Использовать параллельную сборку
docker build --parallel -t ghcr.io/alexbergh/test-hard:latest .
```

### Проверка содержимого образа

```bash
# Запустить shell в контейнере
docker run --rm -it ghcr.io/alexbergh/test-hard:latest /bin/bash

# Проверить установленные инструменты
docker run --rm ghcr.io/alexbergh/test-hard:latest which oscap lynis telegraf
```

## Структура Dockerfile

Unified image включает:

- **OpenSCAP** — сканер безопасности
- **Lynis** — аудит безопасности Linux
- **Telegraf** — сбор и отправка метрик
- **Вспомогательные скрипты** — парсеры, entrypoints

## См. также

- [QUICKSTART.md](QUICKSTART.md) — быстрый старт
- [DEPLOYMENT.md](DEPLOYMENT.md) — развертывание
- [DOCKER_OPTIMIZATIONS.md](DOCKER_OPTIMIZATIONS.md) — оптимизация Docker
- [FAQ.md](FAQ.md) — часто задаваемые вопросы
