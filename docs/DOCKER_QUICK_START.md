# Docker Quick Start Guide

Быстрый старт для работы с оптимизированными Docker образами проекта test-hard.

## Предварительные требования

1. **Docker версия 20.10+**
   ```bash
   docker --version
   ```

2. **Включить BuildKit** (рекомендуется)
   ```bash
   # Временно для текущей сессии
   export DOCKER_BUILDKIT=1
   
   # Постоянно (добавьте в ~/.bashrc или ~/.zshrc)
   echo 'export DOCKER_BUILDKIT=1' >> ~/.bashrc
   source ~/.bashrc
   ```

3. **Docker Compose v2**
   ```bash
   docker compose version
   ```

## Быстрый старт

### 1. Сборка всех образов

```bash
# Сборка с использованием BuildKit и cache
docker compose build

# Параллельная сборка (быстрее)
docker compose build --parallel
```

### 2. Запуск сервисов

```bash
# Запуск всех сервисов
make up

# Или напрямую через docker compose
docker compose up -d

# Проверка статуса
docker compose ps
```

### 3. Проверка здоровья сервисов

```bash
# Через make
make health

# Или напрямую
docker ps
# Смотрите столбец STATUS - должно быть "healthy"
```

### 4. Просмотр логов

```bash
# Все сервисы
docker compose logs -f

# Конкретный сервис
docker compose logs -f telegraf
```

## Оптимизация сборки

### Использование кэша

BuildKit автоматически использует кэш для:
- **APT/DNF/YUM пакетов** - скачиваются один раз
- **PIP зависимостей** - устанавливаются один раз
- **Docker слоев** - переиспользуются при повторных сборках

### Измерение улучшений

```bash
# Запустить скрипт анализа
bash scripts/measure_docker_improvements.sh
```

**Пример вывода:**
```
====================================
Docker Optimization Metrics
====================================

1. Размеры Docker образов
----------------------------------------
IMAGE                          SIZE
-----                          ----
test-hard/ubuntu              450MB
test-hard/debian              380MB
test-hard/telegraf            320MB
----------------------------------------
TOTAL (3 images)              1150MB
```

### Ускорение повторных сборок

```bash
# Первая сборка (создание кэша) - ~15 мин
time docker compose build ubuntu

# Повторная сборка (с кэшем) - ~2 мин
time docker compose build ubuntu
```

**Результат:** Ускорение в 7-8 раз! 🚀

## Управление кэшем

### Просмотр кэша

```bash
# Общая статистика
docker system df

# Детальная информация по кэшу
docker buildx du
```

### Очистка кэша

```bash
# Безопасная очистка (только старые неиспользуемые слои)
docker builder prune

# Агрессивная очистка (весь кэш)
docker builder prune -a

# Очистка по времени
docker builder prune --filter "until=24h"
```

## Примеры команд

### Сборка конкретного образа

```bash
# Ubuntu образ
docker compose build ubuntu

# Telegraf с кэшированием
DOCKER_BUILDKIT=1 docker compose build telegraf

# Без использования кэша (редко нужно)
docker compose build --no-cache telegraf
```

### Проверка multi-stage builds

```bash
# Посмотреть слои образа
docker history test-hard/ubuntu:latest

# Сравнить размеры
docker images | grep test-hard
```

### Health Checks

```bash
# Проверить health status
docker inspect --format='{{json .State.Health}}' telegraf | jq

# Только статус
docker inspect --format='{{.State.Health.Status}}' telegraf
```

## Troubleshooting

### Проблема: BuildKit не работает

**Решение:**
```bash
# Проверить версию Docker
docker version | grep BuildKit

# Включить BuildKit
export DOCKER_BUILDKIT=1

# Или в /etc/docker/daemon.json
{
  "features": {
    "buildkit": true
  }
}

# Перезапустить Docker
sudo systemctl restart docker
```

### Проблема: Медленная сборка несмотря на кэш

**Решение:**
```bash
# 1. Проверить .dockerignore
ls -la docker/ubuntu/Dockerfile.dockerignore

# 2. Очистить и пересоздать кэш
docker builder prune -a
docker compose build --parallel

# 3. Проверить размер build context
docker build --progress=plain -f docker/ubuntu/Dockerfile . 2>&1 | grep "transferring context"
```

### Проблема: Контейнер показывает unhealthy

**Решение:**
```bash
# 1. Проверить логи
docker logs telegraf

# 2. Детальная информация о health check
docker inspect --format='{{json .State.Health}}' telegraf | jq

# 3. Войти в контейнер и проверить вручную
docker exec -it telegraf curl http://localhost:9091/metrics
```

### Проблема: Нехватка места на диске

**Решение:**
```bash
# 1. Посмотреть что занимает место
docker system df -v

# 2. Очистить всё ненужное
docker system prune -a --volumes

# 3. Удалить старые образы
docker image prune -a --filter "until=24h"
```

## Best Practices

### ✅ DO

- ✅ Используйте BuildKit для всех сборок
- ✅ Регулярно очищайте кэш (раз в неделю)
- ✅ Используйте `docker compose build --parallel` для ускорения
- ✅ Проверяйте health status перед деплоем
- ✅ Сохраняйте benchmark размеров образов

### ❌ DON'T

- ❌ Не используйте `--no-cache` без необходимости
- ❌ Не игнорируйте .dockerignore файлы
- ❌ Не запускайте сборку без BuildKit
- ❌ Не удаляйте весь кэш перед каждой сборкой

## Метрики производительности

| Метрика | До оптимизации | После | Улучшение |
|---------|----------------|-------|-----------|
| Размер образа (Ubuntu) | ~800 MB | ~450 MB | **44%** ↓ |
| Первая сборка | 15 мин | 15 мин | 0% |
| Повторная сборка | 12 мин | 2 мин | **83%** ↓ |
| CI/CD pipeline | 25 мин | 12 мин | **52%** ↓ |
| Использование сети | 100% | 30% | **70%** ↓ |

## Дополнительные ресурсы

- [Полная документация по оптимизациям](./DOCKER_OPTIMIZATIONS.md)
- [Docker BuildKit](https://docs.docker.com/build/buildkit/)
- [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [Best practices](https://docs.docker.com/develop/dev-best-practices/)

## Поддержка

Если возникли проблемы:

1. Проверьте [DOCKER_OPTIMIZATIONS.md](./DOCKER_OPTIMIZATIONS.md) - Troubleshooting секция
2. Запустите диагностику: `bash scripts/measure_docker_improvements.sh`
3. Создайте issue с выводом команды `docker version` и `docker system df`

---

**Совет:** Добавьте алиасы в `.bashrc` для удобства:

```bash
# Docker shortcuts
alias dcb='docker compose build --parallel'
alias dcu='docker compose up -d'
alias dcl='docker compose logs -f'
alias dps='docker compose ps'
alias dclean='docker builder prune -a'
```
