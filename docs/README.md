# Документация test-hard

Добро пожаловать в документацию платформы Security Hardening & Monitoring!

## Основная документация

### Начало работы
- **[Quick Start Guide](QUICK-USAGE.md)** — быстрый старт за 5 минут
- **[Quickstart](QUICKSTART.md)** — детальное руководство по первому запуску
- **[User Guide](USER-GUIDE.md)** — полное руководство пользователя

### Security Scanning
- **[Security Scanning Overview](README-SECURITY-SCANNING.md)** — подробное описание security сканирования
  - OpenSCAP configuration
  - Lynis setup
  - Atomic Red Team integration
  - Metrics collection

### Устранение проблем
- **[Troubleshooting](TROUBLESHOOTING.md)** — решение типичных проблем
  - Docker networking issues
  - Grafana connectivity
  - Scanner errors
  - WSL2 specific issues

## Справочная информация

- **[Changelog](CHANGELOG.md)** — история изменений и версии
- **[Security Policy](SECURITY.md)** — политика безопасности и disclosure
- **[Summary](SUMMARY.md)** — краткое описание проекта
- **[Documentation Index](DOCUMENTATION-INDEX.md)** — полный индекс документации

## Информация для разработчиков

- **[README Updates](README-UPDATES.md)** — история обновлений README
- **[Files Created](FILES-CREATED.md)** — список созданных файлов
- **[Phase 1 Complete](PHASE1-COMPLETE.md)** — статус первой фазы разработки
- **[Final Summary](FINAL-SUMMARY-FOR-USER.md)** — итоговая сводка для пользователя

## Быстрая навигация

### По задачам

**Хочу быстро запустить:**
→ [Quick Start Guide](QUICK-USAGE.md)

**Хочу настроить security сканирование:**
→ [Security Scanning](README-SECURITY-SCANNING.md)

**У меня проблемы с запуском:**
→ [Troubleshooting](TROUBLESHOOTING.md)

**Хочу понять архитектуру:**
→ [User Guide](USER-GUIDE.md)

**Хочу интегрировать в CI/CD:**
→ [User Guide - CI/CD Section](USER-GUIDE.md#cicd)

## Диаграммы и схемы

```
┌─────────────────────────────────────────────────────────────┐
│                     test-hard Platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐   ┌──────────────┐  │
│  │  OpenSCAP    │───▶│   Telegraf   │──▶│  Prometheus  │  │
│  │   Scanner    │    │   Metrics    │   │              │  │
│  └──────────────┘    │  Collector   │   └──────┬───────┘  │
│                      │              │           │          │
│  ┌──────────────┐    │              │           │          │
│  │    Lynis     │───▶│              │           │          │
│  │   Scanner    │    └──────────────┘           │          │
│  └──────────────┘                               │          │
│                                                  ▼          │
│  ┌──────────────┐                      ┌──────────────┐    │
│  │ Atomic Red   │                      │   Grafana    │    │
│  │    Team      │                      │  Dashboards  │    │
│  └──────────────┘                      └──────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Target Containers (Multi-Distribution)      │   │
│  │   Debian  │  Ubuntu  │  Fedora  │  CentOS Stream   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Полезные ссылки

- [Основной README](../README.md)
- [GitHub Repository](https://github.com/alexbergh/test-hard)
- [Issue Tracker](https://github.com/alexbergh/test-hard/issues)

## Вклад в проект

Если вы нашли ошибку в документации или хотите её улучшить:

1. Откройте [Issue](https://github.com/alexbergh/test-hard/issues)
2. Или создайте Pull Request с изменениями

---

**Обновлено**: 2025-10-27  
**Версия документации**: 2.0
