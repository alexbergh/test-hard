# Единый Docker образ test-hard

## Обзор изменений

Проект был переработан для использования **единого Docker образа** вместо раздельных пакетов для каждого сканера.

### До изменений:
- 5 отдельных пакетов в GitHub Container Registry:
  - `test-hard/telegraf`
  - `test-hard/lynis-scanner`
  - `test-hard/openscap-scanner`
  - `test-hard/lynis`
  - `test-hard/openscap`

### После изменений:
- 1 единый образ: **`ghcr.io/alexbergh/test-hard`**

## Преимущества

1. **Упрощенное управление версиями** - одна версия для всех компонентов
2. **Меньше места** - общие слои переиспользуются (Docker layer caching)
3. **Консистентность** - все компоненты используют одинаковые зависимости
4. **Проще CI/CD** - один workflow вместо нескольких
5. **Удобнее использовать** - единая точка входа через entrypoint

## Использование

### Быстрый старт

```bash
# Собрать образ
make build

# Запустить Lynis сканер
make run-lynis

# Запустить OpenSCAP сканер
make run-openscap

# Запустить все сканеры
make run-all

# Запустить Atomic Red Team тесты
make run-atomic
```

### Docker Compose

```bash
# Запустить все сервисы (используют единый образ)
make up

# Только сканеры
make up-targets
```

### Прямое использование Docker

```bash
# Показать справку
docker run ghcr.io/alexbergh/test-hard help

# Запустить Lynis сканирование
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/reports:/opt/test-hard/reports \
  ghcr.io/alexbergh/test-hard scan-lynis

# Запустить OpenSCAP сканирование
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/reports:/opt/test-hard/reports \
  ghcr.io/alexbergh/test-hard scan-openscap

# Запустить все сканеры
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/reports:/opt/test-hard/reports \
  ghcr.io/alexbergh/test-hard scan-all

# Запустить Atomic Red Team
docker run --rm \
  -v $(pwd)/art-storage:/var/lib/hardening/art-storage \
  ghcr.io/alexbergh/test-hard atomic --dry-run

# Парсинг отчетов
docker run --rm \
  -v $(pwd)/reports:/reports \
  ghcr.io/alexbergh/test-hard parse-lynis /reports/lynis.json
```

## Доступные команды

Единый образ поддерживает следующие команды через entrypoint:

### Сканеры
- `lynis [args]` - Прямой запуск Lynis
- `openscap [args]` - Прямой запуск OpenSCAP
- `scan-lynis` - Lynis с настройками по умолчанию
- `scan-openscap` - OpenSCAP с настройками по умолчанию
- `scan-all` - Все сканеры последовательно
- `atomic [args]` - Atomic Red Team тесты

### Парсеры
- `parse-lynis <file>` - Парсинг Lynis отчета в Prometheus формат
- `parse-openscap <file>` - Парсинг OpenSCAP отчета в Prometheus формат
- `parse-atomic <file>` - Парсинг результатов Atomic Red Team

### Утилиты
- `bash` - Интерактивная bash оболочка
- `help` - Показать справку

## Архитектура образа

Образ использует **multi-stage build** для оптимизации размера:

1. **Base stage** - Debian 12 slim с базовыми зависимостями
2. **Lynis stage** - Установка Lynis из APT
3. **OpenSCAP stage** - Установка OpenSCAP из Fedora
4. **Final stage** - Объединение всех компонентов

### Что включено

- **Lynis** - Security auditing tool
- **OpenSCAP** - Security compliance scanner
- **Python 3** + зависимости (atomic-operator, PyYAML, etc.)
- **Docker CLI** - для сканирования контейнеров
- **Все скрипты** из `scripts/` директории
- **Atomic Red Team** сценарии

## Миграция

Если вы использовали старые образы, обновите docker-compose.yml:

```yaml
# Было:
services:
  lynis-scanner:
    build: ./scanners/lynis
    image: test-hard/lynis-scanner:latest

# Стало:
services:
  lynis-scanner:
    build: .
    image: ghcr.io/alexbergh/test-hard:latest
    command: scan-lynis
```

## CI/CD

GitHub Actions автоматически собирает и публикует образ при:
- Push в `main` или `develop` ветки
- Создании тега `v*`
- Pull request в `main`

Образ подписывается с помощью **Cosign** для обеспечения целостности.

## Разработка

### Локальная сборка

```bash
# Сборка
docker build -t test-hard:dev .

# Тестирование
docker run --rm test-hard:dev help
docker run --rm test-hard:dev scan-lynis
```

### Отладка

```bash
# Запуск интерактивной оболочки
docker run --rm -it test-hard:dev bash

# Проверка установленных компонентов
docker run --rm test-hard:dev lynis --version
docker run --rm test-hard:dev oscap --version
```

## Troubleshooting

### Ошибка "command not found"

Убедитесь, что используете правильный entrypoint:
```bash
docker run ghcr.io/alexbergh/test-hard help
```

### Проблемы с доступом к Docker socket

Проверьте права на `/var/run/docker.sock`:
```bash
ls -la /var/run/docker.sock
# Должно быть: srw-rw---- root docker
```

### Образ слишком большой

Образ оптимизирован с помощью multi-stage build. Размер ~500-700 MB включает:
- Все сканеры (Lynis, OpenSCAP)
- Python окружение
- SCAP контент для различных дистрибутивов

## Changelog

### v1.1.0 - Unified Image Release

- ✅ Создан единый Docker образ для всех компонентов
- ✅ Multi-stage build для оптимизации размера
- ✅ Универсальный entrypoint с множественными командами
- ✅ Обновлен GitHub Actions workflow
- ✅ Обновлен docker-compose.yml
- ✅ Добавлены Makefile команды (build, push, run-*)
- ✅ SBOM генерация через Anchore
- ✅ Cosign signing для безопасности

## Ссылки

- GitHub Repository: https://github.com/alexbergh/test-hard
- Container Registry: https://ghcr.io/alexbergh/test-hard
- Documentation: https://github.com/alexbergh/test-hard/tree/main/docs
