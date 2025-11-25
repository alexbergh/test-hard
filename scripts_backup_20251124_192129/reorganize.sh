#!/bin/bash
# Script to reorganize scripts/ directory structure
# Run with: bash scripts/reorganize.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

error() {
    echo "[ERROR] $*" >&2
    exit 1
}

# Check if we're in the right directory
if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    error "Must be run from project root or scripts directory"
fi

log "Starting scripts reorganization..."

# Create new directory structure
log "Creating directory structure..."
mkdir -p "$SCRIPT_DIR/setup"
mkdir -p "$SCRIPT_DIR/scanning"
mkdir -p "$SCRIPT_DIR/parsing"
mkdir -p "$SCRIPT_DIR/monitoring"
mkdir -p "$SCRIPT_DIR/backup"
mkdir -p "$SCRIPT_DIR/testing"
mkdir -p "$SCRIPT_DIR/utils"

# Backup current structure
BACKUP_DIR="$PROJECT_ROOT/scripts_backup_$(date +%Y%m%d_%H%M%S)"
log "Creating backup at $BACKUP_DIR"
cp -r "$SCRIPT_DIR" "$BACKUP_DIR"

# Move files to new locations
log "Moving files to new structure..."

# setup/
mv "$SCRIPT_DIR/install-deps.sh" "$SCRIPT_DIR/setup/" 2>/dev/null || true
mv "$SCRIPT_DIR/setup-secure-user.sh" "$SCRIPT_DIR/setup/" 2>/dev/null || true

# scanning/
mv "$SCRIPT_DIR/run_lynis.sh" "$SCRIPT_DIR/scanning/" 2>/dev/null || true
mv "$SCRIPT_DIR/run_openscap.sh" "$SCRIPT_DIR/scanning/" 2>/dev/null || true
mv "$SCRIPT_DIR/run_atomic_red_team_test.sh" "$SCRIPT_DIR/scanning/" 2>/dev/null || true
mv "$SCRIPT_DIR/run_atomic_red_team_suite.py" "$SCRIPT_DIR/scanning/" 2>/dev/null || true
mv "$SCRIPT_DIR/run_hardening_suite.sh" "$SCRIPT_DIR/scanning/" 2>/dev/null || true
mv "$SCRIPT_DIR/run_all_checks.sh" "$SCRIPT_DIR/scanning/" 2>/dev/null || true
mv "$SCRIPT_DIR/scan-remote-host.sh" "$SCRIPT_DIR/scanning/" 2>/dev/null || true

# parsing/
mv "$SCRIPT_DIR/parse_lynis_log.py" "$SCRIPT_DIR/parsing/" 2>/dev/null || true
mv "$SCRIPT_DIR/parse_lynis_report.py" "$SCRIPT_DIR/parsing/" 2>/dev/null || true
mv "$SCRIPT_DIR/parse_openscap_report.py" "$SCRIPT_DIR/parsing/" 2>/dev/null || true
mv "$SCRIPT_DIR/parse_atomic_red_team_result.py" "$SCRIPT_DIR/parsing/" 2>/dev/null || true

# monitoring/
mv "$SCRIPT_DIR/health_check.sh" "$SCRIPT_DIR/monitoring/" 2>/dev/null || true
mv "$SCRIPT_DIR/measure_docker_improvements.sh" "$SCRIPT_DIR/monitoring/" 2>/dev/null || true

# backup/
mv "$SCRIPT_DIR/backup.sh" "$SCRIPT_DIR/backup/" 2>/dev/null || true

# testing/
mv "$SCRIPT_DIR/test-core-functionality.sh" "$SCRIPT_DIR/testing/" 2>/dev/null || true
mv "$SCRIPT_DIR/run_shell_tests.sh" "$SCRIPT_DIR/testing/" 2>/dev/null || true
mv "$SCRIPT_DIR/verify_fixes.sh" "$SCRIPT_DIR/testing/" 2>/dev/null || true

# utils/
mv "$SCRIPT_DIR/bump-version.sh" "$SCRIPT_DIR/utils/" 2>/dev/null || true

# Create symbolic links for backward compatibility
log "Creating symbolic links for backward compatibility..."
cd "$SCRIPT_DIR"

# setup/
ln -sf setup/install-deps.sh install-deps.sh 2>/dev/null || true
ln -sf setup/setup-secure-user.sh setup-secure-user.sh 2>/dev/null || true

# scanning/
ln -sf scanning/run_lynis.sh run_lynis.sh 2>/dev/null || true
ln -sf scanning/run_openscap.sh run_openscap.sh 2>/dev/null || true
ln -sf scanning/run_atomic_red_team_test.sh run_atomic_red_team_test.sh 2>/dev/null || true
ln -sf scanning/run_atomic_red_team_suite.py run_atomic_red_team_suite.py 2>/dev/null || true
ln -sf scanning/run_hardening_suite.sh run_hardening_suite.sh 2>/dev/null || true
ln -sf scanning/run_all_checks.sh run_all_checks.sh 2>/dev/null || true
ln -sf scanning/scan-remote-host.sh scan-remote-host.sh 2>/dev/null || true

# parsing/
ln -sf parsing/parse_lynis_log.py parse_lynis_log.py 2>/dev/null || true
ln -sf parsing/parse_lynis_report.py parse_lynis_report.py 2>/dev/null || true
ln -sf parsing/parse_openscap_report.py parse_openscap_report.py 2>/dev/null || true
ln -sf parsing/parse_atomic_red_team_result.py parse_atomic_red_team_result.py 2>/dev/null || true

# monitoring/
ln -sf monitoring/health_check.sh health_check.sh 2>/dev/null || true
ln -sf monitoring/measure_docker_improvements.sh measure_docker_improvements.sh 2>/dev/null || true

# backup/
ln -sf backup/backup.sh backup.sh 2>/dev/null || true

# testing/
ln -sf testing/test-core-functionality.sh test-core-functionality.sh 2>/dev/null || true
ln -sf testing/run_shell_tests.sh run_shell_tests.sh 2>/dev/null || true
ln -sf testing/verify_fixes.sh verify_fixes.sh 2>/dev/null || true

# utils/
ln -sf utils/bump-version.sh bump-version.sh 2>/dev/null || true

# Create README files for each category
log "Creating category README files..."

cat > "$SCRIPT_DIR/setup/README.md" << 'EOF'
# Setup Scripts

Скрипты для установки и первоначальной настройки системы.

## Файлы

- `install-deps.sh` - Установка Python зависимостей и pre-commit hooks
- `setup-secure-user.sh` - Создание безопасных пользователей для сканирования
EOF

cat > "$SCRIPT_DIR/scanning/README.md" << 'EOF'
# Scanning Scripts

Скрипты для выполнения security сканирования.

## Файлы

- `run_lynis.sh` - Запуск Lynis сканирования
- `run_openscap.sh` - Запуск OpenSCAP сканирования
- `run_atomic_red_team_test.sh` - Запуск Atomic Red Team тестов
- `run_atomic_red_team_suite.py` - Python обертка для ART тестов
- `run_hardening_suite.sh` - Запуск полного набора проверок
- `run_all_checks.sh` - Запуск всех видов сканирования
- `scan-remote-host.sh` - Сканирование удаленных хостов по SSH
EOF

cat > "$SCRIPT_DIR/parsing/README.md" << 'EOF'
# Parsing Scripts

Парсеры для обработки отчетов сканирования и конвертации в Prometheus метрики.

## Файлы

- `parse_lynis_log.py` - Парсинг Lynis логов
- `parse_lynis_report.py` - Парсинг Lynis отчетов
- `parse_openscap_report.py` - Парсинг OpenSCAP XML отчетов
- `parse_atomic_red_team_result.py` - Парсинг результатов Atomic Red Team
EOF

cat > "$SCRIPT_DIR/monitoring/README.md" << 'EOF'
# Monitoring Scripts

Скрипты для мониторинга и проверки здоровья системы.

## Файлы

- `health_check.sh` - Проверка здоровья всех сервисов
- `measure_docker_improvements.sh` - Измерение улучшений Docker сборки
EOF

cat > "$SCRIPT_DIR/backup/README.md" << 'EOF'
# Backup Scripts

Скрипты для резервного копирования и восстановления.

## Файлы

- `backup.sh` - Создание backup конфигурации и данных
EOF

cat > "$SCRIPT_DIR/testing/README.md" << 'EOF'
# Testing Scripts

Скрипты для тестирования функциональности платформы.

## Файлы

- `test-core-functionality.sh` - Тест основной функциональности
- `run_shell_tests.sh` - Запуск bats тестов
- `verify_fixes.sh` - Проверка примененных исправлений
EOF

cat > "$SCRIPT_DIR/utils/README.md" << 'EOF'
# Utility Scripts

Вспомогательные утилиты.

## Файлы

- `bump-version.sh` - Обновление версии проекта
EOF

# Update main scripts README
cat > "$SCRIPT_DIR/README.md" << 'EOF'
# Scripts Directory

Скрипты проекта организованы по категориям для улучшения навигации.

## Структура

```
scripts/
├── setup/          # Установка и настройка
├── scanning/       # Скрипты сканирования
├── parsing/        # Парсеры отчетов
├── monitoring/     # Мониторинг и health checks
├── backup/         # Backup и restore
├── testing/        # Тестирование
└── utils/          # Утилиты
```

## Обратная совместимость

В корне `scripts/` находятся символические ссылки на файлы в подкаталогах
для обеспечения обратной совместимости. Рекомендуется обновить ссылки
на новые пути.

## Использование

```bash
# Старый путь (работает через symlink)
./scripts/health_check.sh

# Новый путь (рекомендуется)
./scripts/monitoring/health_check.sh
```

## Миграция

См. [REORGANIZATION_PLAN.md](REORGANIZATION_PLAN.md) для деталей реорганизации.
EOF

log ""
log "[SUCCESS] Reorganization complete!"
log ""
log "Summary:"
log "  - Created new directory structure"
log "  - Moved files to appropriate categories"
log "  - Created symbolic links for backward compatibility"
log "  - Created README files for each category"
log "  - Backup created at: $BACKUP_DIR"
log ""
log "Next steps:"
log "  1. Test that everything works: make test"
log "  2. Update Makefile references to new paths"
log "  3. Update documentation"
log "  4. After testing, remove symbolic links (in future release)"
log ""
