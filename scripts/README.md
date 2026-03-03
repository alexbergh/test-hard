# Scripts Directory

Скрипты проекта организованы по категориям для улучшения навигации.

## Структура

```
scripts/
├── scanning/       # Сканирование: Lynis, OpenSCAP, ART, Trivy, nmap, SSH
├── parsing/        # Парсеры отчетов в Prometheus-формат
├── monitoring/     # Health checks и измерение Podman-метрик
├── setup/          # Установка зависимостей и настройка пользователей
├── testing/        # Тестирование функциональности
├── backup/         # Backup конфигурации и данных
├── utils/          # Утилиты (bump-version)
├── send_falco_events.py    # Генерация Falco-событий для всех контейнеров
├── scan_all_images.py      # Сканирование всех образов через Trivy
├── fix_prom_metrics.py     # Исправление формата .prom файлов Trivy
└── reorganize.sh           # Скрипт реорганизации директорий
```

## Корневые скрипты

Некоторые скрипты находятся в корне `scripts/` (не в подкаталогах):

- `send_falco_events.py` -- генерация Falco runtime-событий для всех 20 контейнеров проекта
- `scan_all_images.py` -- сканирование всех контейнерных образов через trivy-server
- `fix_prom_metrics.py` -- регенерация Trivy `.prom` файлов с правильным форматом (Unix LF)
- `parse_lynis_report.py`, `parse_openscap_report.py`, `parse_atomic_red_team_result.py` -- парсеры (symlinks на `parsing/`)

## Использование

```bash
# Полное сканирование (Lynis + OpenSCAP + ART)
./scripts/scanning/run_hardening_suite.sh

# Сканирование образов Trivy
python3 scripts/scan_all_images.py

# Генерация Falco-событий
python3 scripts/send_falco_events.py

# Health check всех сервисов
./scripts/monitoring/health_check.sh
```
