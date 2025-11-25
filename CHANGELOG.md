# Changelog

Все значимые изменения в проекте документируются в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/),
и проект придерживается [Semantic Versioning](https://semver.org/lang/ru/).

## [Unreleased]

### Added
- Добавлен `.editorconfig` для единообразия стиля кода
- Добавлен `CONTRIBUTING.md` с полным руководством для контрибьюторов
- Добавлен `docs/TROUBLESHOOTING.md` с решением типичных проблем (600+ строк)
- Добавлен `docs/FAQ.md` с 50+ часто задаваемыми вопросами
- Добавлен `.secrets.example` как шаблон для управления секретами
- Добавлен `.yamllint.yml` для проверки YAML файлов
- Добавлен `.markdownlint.yaml` для проверки Markdown документации
- Добавлена реорганизация `scripts/` по категориям (7 подкаталогов)
- Добавлен yamllint в CI pipeline
- Добавлен markdownlint в pre-commit hooks
- Добавлено 20+ новых make targets (backup, security, status, metrics, diagnostics и др.)
- Улучшен `.gitattributes` с правильными настройками для всех типов файлов

### Changed
- Реорганизована структура `scripts/` на подкаталоги по назначению
- Улучшен `.gitignore` с 40+ новыми правилами
- Обновлен `Makefile` - исправлены пути после реорганизации scripts/
- Обновлен `.pre-commit-config.yaml` для использования новых конфигураций
- Улучшена документация с центральной страницей `docs/README.md`

### Fixed
- Исправлены конфликтующие атрибуты в `.gitattributes` (text vs binary для .sh)

## [1.0.0] - 2025-11-24

### Added
- Первый стабильный релиз платформы test-hard
- Полная интеграция Docker Compose для запуска всех компонентов
- Мониторинг с Prometheus, Grafana, Telegraf, Alertmanager
- Централизованное логирование с Loki и Promtail
- Security сканеры: Lynis, OpenSCAP, Atomic Red Team
- Парсеры отчетов в метрики Prometheus
- Готовые Grafana дашборды для визуализации
- Поддержка сканирования Docker контейнеров, remote хостов через SSH
- Health checks для всех сервисов
- Автоматизация через Makefile
- CI/CD pipeline с GitHub Actions
- Комплексная документация на русском языке

### Security
- Docker Socket Proxy для безопасного доступа к Docker API
- Resource limits для всех контейнеров
- Read-only мониторинг файловой системы
- Безопасное управление credentials через .env
- TLS/SSL рекомендации в документации

## [0.9.0] - 2025-11-01

### Added
- Docker оптимизации с BuildKit
- Multi-stage builds для уменьшения размера образов
- Специфичные .dockerignore для каждого сканера
- Measure скрипт для отслеживания улучшений

### Changed
- Обновлены все Docker образы на slim версии
- Оптимизированы CI/CD пайплайны

## [0.8.0] - 2025-10-15

### Added
- Поддержка Kubernetes с Kustomize
- ArgoCD конфигурации для GitOps
- Helm charts (экспериментально)
- Production готовые конфигурации

### Changed
- Переход на docker compose v2
- Обновление документации для production deployments

## [0.7.0] - 2025-09-20

### Added
- Централизованное логирование с Loki
- Promtail для сбора логов из контейнеров
- Grafana дашборды для логов
- Log retention политики

### Changed
- Структура docker-compose файлов
- Добавлен docker-compose.logging.yml

## [0.6.0] - 2025-08-10

### Added
- Atomic Red Team интеграция для тестирования обнаружения угроз
- Dry-run режим для безопасного тестирования
- Парсер результатов ART

### Security
- Atomic Red Team запускается только в dry-run по умолчанию
- Предупреждения о потенциальных изменениях системы

## [0.5.0] - 2025-07-15

### Added
- OpenSCAP сканер для compliance проверок
- Поддержка профилей CIS, DISA STIG, PCI-DSS
- Парсинг XCCDF отчетов
- Метрики compliance в Prometheus

### Changed
- Улучшена структура отчетов
- Добавлены примеры использования в документацию

## [0.4.0] - 2025-06-20

### Added
- Lynis сканер для security auditing
- Парсер Lynis JSON отчетов
- Метрики severity levels
- Автоматические алерты на критические находки

### Fixed
- Проблемы с правами доступа в контейнерах
- Volume mapping для сканирования хост системы

## [0.3.0] - 2025-05-10

### Added
- Grafana дашборды для визуализации метрик
- Provisioning дашбордов через конфигурацию
- Alerting rules в Prometheus
- Alertmanager для уведомлений

### Changed
- Улучшена структура метрик
- Добавлены labels для фильтрации

## [0.2.0] - 2025-04-01

### Added
- Telegraf для сбора метрик
- Python парсеры security отчетов
- Prometheus для хранения метрик
- Базовые алерты

### Changed
- Архитектура системы с использованием push модели
- Документация по интеграции компонентов

## [0.1.0] - 2025-03-01

### Added
- Начальная версия проекта
- Docker Compose setup
- Базовая документация
- Примеры конфигурации
- Target контейнеры для тестирования (Fedora, Debian, CentOS, Ubuntu)

---

## Типы изменений

- `Added` - новая функциональность
- `Changed` - изменения в существующей функциональности
- `Deprecated` - функциональность, которая будет удалена в будущих версиях
- `Removed` - удаленная функциональность
- `Fixed` - исправления багов
- `Security` - изменения, касающиеся безопасности

## Ссылки

- [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/)
- [Semantic Versioning](https://semver.org/lang/ru/)
- [Conventional Commits](https://www.conventionalcommits.org/ru/v1.0.0/)
