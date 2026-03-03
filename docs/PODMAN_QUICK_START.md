# Руководство быстрого старта Podman

Быстрый старт для работы с оптимизированными Podman образами проекта test-hard.

## Предварительные требования

1. **Podman версия 4.0+**

   ```bash
   podman --version
   ```

2. **Podman Compose**

   ```bash
   pip install podman-compose
   podman-compose version
   ```

### Linux

```bash
# Включить и запустить сокет
systemctl --user enable --now podman.socket

# Проверить статус
systemctl --user status podman.socket
```

### Windows

1. **Установить Podman Desktop** или **Podman CLI** через winget:

   ```powershell
   winget install RedHat.Podman
   ```

2. **Инициализировать и запустить Podman машину:**

   ```powershell
   podman machine init
   podman machine start
   ```

3. **Запустить Podman API на TCP** (для доступа из контейнеров):

   ```powershell
   # Запуск API на TCP порту 2375
   podman machine ssh "podman system service --time=0 tcp:0.0.0.0:2375 &"
   ```

4. **Добавить Podman в PATH** (если не добавлен автоматически):

   ```powershell
   $env:Path = "C:\Users\$env:USERNAME\AppData\Local\Programs\Podman;" + $env:Path
   ```

**Важно для Windows:** Контейнеры используют `host.containers.internal:2375` для доступа к Podman API вместо `podman-proxy`.

## Быстрый старт

### 1. Сборка всех образов

```bash
# Сборка всех образов
podman-compose build

# Сборка конкретного образа
podman build -f containers/ubuntu/Containerfile -t test-ubuntu .
```

### 2. Запуск сервисов

```bash
# Запуск всех сервисов
make up

# Или напрямую через podman-compose
podman-compose up -d

# Проверка статуса
podman-compose ps
```

### 3. Проверка здоровья сервисов

```bash
# Через make
make health

# Или напрямую
podman ps
# Смотрите столбец STATUS - должно быть "healthy"
```

### 4. Просмотр логов

```bash
# Все сервисы
podman-compose logs -f

# Конкретный сервис
podman-compose logs -f telegraf
```

## Оптимизация сборки

### Использование кэша

Buildah автоматически использует кэш для:

* **APT/DNF/YUM пакетов** - скачиваются один раз
* **PIP зависимостей** - устанавливаются один раз
* **Слоев образов** - переиспользуются при повторных сборках

### Измерение улучшений

```bash
# Запустить скрипт анализа
bash scripts/monitoring/measure_podman_improvements.sh
```

**Пример вывода:**

```
====================================
Podman Optimization Metrics
====================================

1. Размеры Podman образов
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
time podman build -f containers/ubuntu/Containerfile -t test-ubuntu .

# Повторная сборка (с кэшем) - ~2 мин
time podman build -f containers/ubuntu/Containerfile -t test-ubuntu .
```

**Результат:** Ускорение в 7-8 раз

## Управление кэшем

### Просмотр кэша

```bash
# Общая статистика
podman system df

# Детальная информация
podman system df -v
```

### Очистка кэша

```bash
# Безопасная очистка (только неиспользуемые ресурсы)
podman system prune

# Агрессивная очистка (все неиспользуемые ресурсы и volumes)
podman system prune -a --volumes

# Очистка только образов
podman image prune -a
```

## Примеры команд

### Сборка конкретного образа

```bash
# Ubuntu образ
podman build -f containers/ubuntu/Containerfile -t test-ubuntu .

# Telegraf
podman-compose build telegraf

# Без использования кэша (редко нужно)
podman-compose build --no-cache telegraf
```

### Проверка multi-stage builds

```bash
# Посмотреть слои образа
podman history test-hard/ubuntu:latest

# Сравнить размеры
podman images | grep test-hard
```

### Health Checks

```bash
# Проверить health status
podman inspect --format='{{json .State.Health}}' telegraf | jq

# Только статус
podman inspect --format='{{.State.Health.Status}}' telegraf
```

## Troubleshooting

### Проблема: Podman не работает (Linux)

**Решение:**

```bash
# Проверить версию Podman
podman version

# Проверить статус сокета
systemctl --user status podman.socket

# Запустить сокет
systemctl --user enable --now podman.socket
```

### Проблема: Podman не работает (Windows)

**Решение:**

```powershell
# Проверить статус машины
podman machine list

# Запустить машину если остановлена
podman machine start

# Проверить подключение
podman info
```

### Проблема: Контейнеры не могут подключиться к Podman API (Windows)

**Решение:**

```powershell
# 1. Запустить Podman API на TCP
podman machine ssh "podman system service --time=0 tcp:0.0.0.0:2375 &"

# 2. Проверить доступность API из контейнера
podman exec <container_name> curl -s http://host.containers.internal:2375/version

# 3. При создании кластера в Dashboard использовать:
#    podman_host: tcp://host.containers.internal:2375
```

### Проблема: podman-proxy возвращает 503 (Windows)

**Причина:** На Windows сокет `/run/podman/podman.sock` недоступен напрямую из контейнеров.

**Решение:** Используйте прямое подключение к Podman API через `host.containers.internal:2375` вместо `podman-proxy`.

### Проблема: Медленная сборка несмотря на кэш

**Решение:**

```bash
# 1. Проверить .containerignore
ls -la containers/ubuntu/.containerignore

# 2. Очистить и пересоздать кэш
podman system prune -a
podman-compose build
```

### Проблема: Контейнер показывает unhealthy

**Решение:**

```bash
# 1. Проверить логи
podman logs telegraf

# 2. Детальная информация о health check
podman inspect --format='{{json .State.Health}}' telegraf | jq

# 3. Войти в контейнер и проверить вручную
podman exec -it telegraf curl http://localhost:9091/metrics
```

### Проблема: Нехватка места на диске

**Решение:**

```bash
# 1. Посмотреть что занимает место
podman system df -v

# 2. Очистить всё ненужное
podman system prune -a --volumes

# 3. Удалить старые образы
podman image prune -a
```

## Best Practices

### DO

* Регулярно очищайте кэш (раз в неделю)
* Используйте `podman-compose build` для сборки
* Проверяйте health status перед деплоем
* Сохраняйте benchmark размеров образов
* Используйте rootless режим для безопасности

### DON'T

* Не используйте `--no-cache` без необходимости
* Не игнорируйте .containerignore файлы
* Не удаляйте весь кэш перед каждой сборкой

## Метрики производительности

| Метрика | До оптимизации | После | Улучшение |
|---------|----------------|-------|-----------|
| Размер образа (Ubuntu) | ~800 MB | ~450 MB | **44%** ↓ |
| Первая сборка | 15 мин | 15 мин | 0% |
| Повторная сборка | 12 мин | 2 мин | **83%** ↓ |
| CI/CD pipeline | 25 мин | 12 мин | **52%** ↓ |
| Использование сети | 100% | 30% | **70%** ↓ |

## Дополнительные ресурсы

* [Полная документация по оптимизациям](./PODMAN_OPTIMIZATIONS.md)
* [Podman Documentation](https://docs.podman.io/)
* [Buildah Documentation](https://buildah.io/)
* [Podman Compose](https://github.com/containers/podman-compose)

## Поддержка

Если возникли проблемы:

1. Проверьте [PODMAN_OPTIMIZATIONS.md](./PODMAN_OPTIMIZATIONS.md) - Troubleshooting секция
2. Запустите диагностику: `bash scripts/monitoring/measure_podman_improvements.sh`
3. Создайте issue с выводом команды `podman version` и `podman system df`

---

**Совет:** Добавьте алиасы в `.bashrc` для удобства:

```bash
# Podman shortcuts
alias pcb='podman-compose build'
alias pcu='podman-compose up -d'
alias pcl='podman-compose logs -f'
alias pps='podman-compose ps'
alias pclean='podman system prune -a'
```

---

Последнее обновление: Март 2026
