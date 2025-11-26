# План реорганизации scripts/

## Текущая структура

Все 20 скриптов находятся в одной директории `scripts/`, что затрудняет навигацию.

## Предлагаемая структура

```
scripts/
├── setup/              # Установка и настройка
│   ├── install-deps.sh
│   └── setup-secure-user.sh
│
├── scanning/           # Скрипты сканирования
│   ├── run_lynis.sh
│   ├── run_openscap.sh
│   ├── run_atomic_red_team_test.sh
│   ├── run_atomic_red_team_suite.py
│   ├── run_hardening_suite.sh
│   ├── run_all_checks.sh
│   └── scan-remote-host.sh
│
├── parsing/            # Парсеры отчетов
│   ├── parse_lynis_log.py
│   ├── parse_lynis_report.py
│   ├── parse_openscap_report.py
│   └── parse_atomic_red_team_result.py
│
├── monitoring/         # Мониторинг и проверки
│   ├── health_check.sh
│   └── measure_docker_improvements.sh
│
├── backup/             # Backup и восстановление
│   └── backup.sh
│
├── testing/            # Тестирование
│   ├── test-core-functionality.sh
│   ├── run_shell_tests.sh
│   └── verify_fixes.sh
│
└── utils/              # Утилиты
    └── bump-version.sh
```

## План миграции

### Фаза 1: Создание структуры (не нарушает работу)

1. Создать новые подкаталоги
2. Скопировать (не перемещать) файлы в новые места
3. Обновить пути в скриптах
4. Создать символические ссылки в корне scripts/

### Фаза 2: Обновление ссылок

1. Обновить Makefile
2. Обновить docker-compose файлы
3. Обновить документацию
4. Обновить CI/CD

### Фаза 3: Финализация

1. Удалить старые файлы из корня scripts/
2. Удалить символические ссылки
3. Обновить README

## Карта миграции файлов

### setup/ (2 файла)

* `install-deps.sh` → `setup/install-deps.sh`
* `setup-secure-user.sh` → `setup/setup-secure-user.sh`

### scanning/ (7 файлов)

* `run_lynis.sh` → `scanning/run_lynis.sh`
* `run_openscap.sh` → `scanning/run_openscap.sh`
* `run_atomic_red_team_test.sh` → `scanning/run_atomic_red_team_test.sh`
* `run_atomic_red_team_suite.py` → `scanning/run_atomic_red_team_suite.py`
* `run_hardening_suite.sh` → `scanning/run_hardening_suite.sh`
* `run_all_checks.sh` → `scanning/run_all_checks.sh`
* `scan-remote-host.sh` → `scanning/scan-remote-host.sh`

### parsing/ (4 файла)

* `parse_lynis_log.py` → `parsing/parse_lynis_log.py`
* `parse_lynis_report.py` → `parsing/parse_lynis_report.py`
* `parse_openscap_report.py` → `parsing/parse_openscap_report.py`
* `parse_atomic_red_team_result.py` → `parsing/parse_atomic_red_team_result.py`

### monitoring/ (2 файла)

* `health_check.sh` → `monitoring/health_check.sh`
* `measure_docker_improvements.sh` → `monitoring/measure_docker_improvements.sh`

### backup/ (1 файл)

* `backup.sh` → `backup/backup.sh`

### testing/ (3 файла)

* `test-core-functionality.sh` → `testing/test-core-functionality.sh`
* `run_shell_tests.sh` → `testing/run_shell_tests.sh`
* `verify_fixes.sh` → `testing/verify_fixes.sh`

### utils/ (1 файл)

* `bump-version.sh` → `utils/bump-version.sh`

## Автоматизация миграции

Создан скрипт `scripts/reorganize.sh` для автоматической реорганизации.

## Обратная совместимость

На переходный период (1-2 релиза) сохраняются:

1. Символические ссылки в корне scripts/
2. Предупреждения об устаревших путях
3. Автоматическое перенаправление

## Обновление зависимых файлов

### Makefile

Обновить пути:

```makefile
scan:
    ./scripts/scanning/run_hardening_suite.sh

health:
    ./scripts/monitoring/health_check.sh
```

### docker-compose.yml

Обновить volume mount при необходимости.

### Документация

Обновить все ссылки на скрипты в:

* README.md
* docs/*.md

## Преимущества реорганизации

1. **Улучшенная навигация** — легко найти нужный скрипт
2. **Логическая группировка** — скрипты сгруппированы по назначению
3. **Масштабируемость** — легко добавлять новые скрипты
4. **Документация** — каждая категория может иметь свой README
5. **Тестирование** — проще организовать тесты для каждой категории

## Внедрение

**Рекомендуется** выполнить реорганизацию в отдельном PR с тщательным тестированием.

**Не рекомендуется** смешивать реорганизацию с другими изменениями.
