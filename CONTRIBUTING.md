# Руководство по внесению вклада в test-hard

Спасибо за ваш интерес к проекту! Мы приветствуем любой вклад в развитие платформы.

## Содержание

- [Кодекс поведения](#кодекс-поведения)
- [С чего начать](#с-чего-начать)
- [Процесс внесения изменений](#процесс-внесения-изменений)
- [Стиль кода](#стиль-кода)
- [Тестирование](#тестирование)
- [Документация](#документация)
- [Сообщения коммитов](#сообщения-коммитов)

## Кодекс поведения

Участвуя в проекте, вы соглашаетесь соблюдать наш кодекс поведения. Пожалуйста, будьте уважительны ко всем участникам.

## С чего начать

### Предварительные требования

- Docker и Docker Compose
- Python 3.8+
- Git
- Базовые знания Bash

### Настройка окружения

1. Форкните репозиторий
2. Склонируйте ваш форк:
```bash
git clone https://github.com/ваш-username/test-hard.git
cd test-hard
```

3. Установите зависимости:
```bash
make setup
# или
python3 -m pip install -r requirements.txt
./scripts/install-deps.sh
```

4. Установите pre-commit hooks:
```bash
python3 -m pip install pre-commit
pre-commit install
```

5. Создайте ветку для ваших изменений:
```bash
git checkout -b feature/ваша-фича
```

## Процесс внесения изменений

### 1. Выберите задачу

- Проверьте [Issues](https://github.com/alexbergh/test-hard/issues)
- Ищите метки `good first issue` или `help wanted`
- Или предложите свою идею, создав новый issue

### 2. Разработка

- Работайте в отдельной ветке
- Делайте небольшие, логичные коммиты
- Пишите понятный код с комментариями
- Следуйте стилю существующего кода

### 3. Тестирование

Перед созданием Pull Request убедитесь, что:

```bash
# Запустить все тесты
make test

# Запустить линтеры
make lint

# Запустить валидацию
make validate

# Проверить функциональность
make up
./scripts/test-core-functionality.sh
```

### 4. Pull Request

1. Убедитесь, что ваш код актуален:
```bash
git fetch upstream
git rebase upstream/main
```

2. Отправьте изменения:
```bash
git push origin feature/ваша-фича
```

3. Создайте Pull Request через GitHub
4. Заполните шаблон PR
5. Дождитесь review

## Стиль кода

### Python

- Следуйте [PEP 8](https://pep8.org/)
- Максимальная длина строки: 120 символов
- Используйте type hints где возможно
- Документируйте функции docstrings

```python
def parse_report(filepath: str) -> dict:
    """
    Parse security scan report.
    
    Args:
        filepath: Path to report file
        
    Returns:
        Dictionary with parsed metrics
    """
    pass
```

### Bash

- Используйте `set -euo pipefail` в начале скриптов
- Цитируйте переменные: `"$variable"`
- Используйте `[[` вместо `[` для условий
- Добавляйте комментарии к сложной логике
- Используйте shellcheck для проверки

```bash
#!/bin/bash
set -euo pipefail

# Function description
function do_something() {
    local input="$1"
    
    if [[ -z "$input" ]]; then
        echo "[ERROR] Input is required"
        return 1
    fi
    
    echo "[OK] Processing: $input"
}
```

### YAML

- Отступ: 2 пробела
- Используйте дефисы для списков
- Цитируйте строки с специальными символами

```yaml
version: '3.8'
services:
  scanner:
    image: scanner:latest
    environment:
      - LOG_LEVEL=info
```

### Markdown

- Одна пустая строка между разделами
- Используйте заголовки в правильной иерархии
- Добавляйте примеры кода в блоках с указанием языка

## Тестирование

### Типы тестов

1. **Unit тесты** - в `tests/unit/`
2. **Integration тесты** - в `tests/integration/`
3. **E2E тесты** - в `tests/e2e/`
4. **Shell тесты** - в `tests/shell/`

### Запуск тестов

```bash
# Все тесты
pytest tests/

# Только unit тесты
pytest tests/unit/

# С покрытием
pytest --cov=scripts tests/

# Shell тесты
bats tests/shell/*.bats
```

### Написание тестов

```python
import pytest
from scripts.parse_lynis_report import parse_report

def test_parse_valid_report():
    """Test parsing valid Lynis report."""
    result = parse_report("tests/fixtures/lynis_valid.log")
    assert result["hardening_index"] > 0
    assert result["tests_executed"] > 0

def test_parse_invalid_file():
    """Test handling of invalid file."""
    with pytest.raises(FileNotFoundError):
        parse_report("nonexistent.log")
```

## Документация

### Обновление документации

- Документация находится в `docs/`
- Используйте русский язык
- Добавляйте примеры использования
- Обновляйте README.md при добавлении новых возможностей

### Структура документа

```markdown
# Заголовок

Краткое описание.

## Установка

Шаги установки...

## Использование

Примеры использования...

## Конфигурация

Параметры конфигурации...

## Устранение неполадок

Типичные проблемы...
```

## Сообщения коммитов

Используйте [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Типы

- `feat:` - новая функция
- `fix:` - исправление бага
- `docs:` - изменения в документации
- `style:` - форматирование, отсутствующие точки с запятой и т.д.
- `refactor:` - рефакторинг кода
- `perf:` - улучшение производительности
- `test:` - добавление тестов
- `chore:` - обновление задач сборки, конфигураций и т.д.
- `ci:` - изменения в CI/CD
- `security:` - исправления безопасности

### Примеры

```bash
feat(scanner): add OpenSCAP profile selection

Added support for selecting different OpenSCAP profiles
through environment variable OPENSCAP_PROFILE.

Closes #123
```

```bash
fix(telegraf): correct metrics collection interval

Fixed issue where Telegraf was collecting metrics too frequently,
causing high CPU usage.

Fixes #456
```

```bash
docs(readme): update installation instructions

Updated Docker version requirements and added
troubleshooting section for common issues.
```

## Проверка перед PR

Перед созданием Pull Request проверьте:

- [ ] Код соответствует стилю проекта
- [ ] Добавлены/обновлены тесты
- [ ] Все тесты проходят
- [ ] Обновлена документация (если нужно)
- [ ] Коммиты следуют конвенции
- [ ] Pre-commit hooks проходят
- [ ] Нет конфликтов с main веткой

## Контрибьюторы

Список контрибьюторов: [CONTRIBUTORS.md](CONTRIBUTORS.md)

## Вопросы?

Если у вас есть вопросы:

1. Проверьте [документацию](docs/)
2. Поищите в [Issues](https://github.com/alexbergh/test-hard/issues)
3. Создайте новый issue с меткой `question`

---

Спасибо за ваш вклад в развитие репозитория!
