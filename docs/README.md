# Документация test-hard

Добро пожаловать в документацию платформы security hardening & monitoring.

## Структура документации

### Начало работы

Для быстрого старта и первоначальной настройки:

- **[Быстрый старт](QUICKSTART.md)** - развертывание за 5-10 минут
- **[Полное руководство по развертыванию](DEPLOYMENT.md)** - детальная инструкция
- **[Troubleshooting](TROUBLESHOOTING.md)** - решение типичных проблем
- **[FAQ](FAQ.md)** - часто задаваемые вопросы

### Безопасность

Документация по security аспектам платформы:

- **[Политика безопасности](SECURITY.md)** - security features, alerts, best practices
- **[Настройка пользователей (полная)](USER-SETUP.md)** - детальное руководство по созданию безопасных пользователей
- **[Настройка пользователей (краткая)](QUICK-USER-SETUP.md)** - быстрая справка по безопасности

### Сканирование и мониторинг

Руководства по сканированию систем:

- **[Сканирование реальных хостов](REAL-HOSTS-SCANNING.md)** - как сканировать production серверы, VM и Docker контейнеры
- **[Централизованное логирование](LOGGING.md)** - настройка и использование Loki + Promtail

### Docker и развертывание

Оптимизация и работа с Docker:

- **[Docker оптимизации](DOCKER_OPTIMIZATIONS.md)** - multi-stage builds, BuildKit cache, метрики
- **[Docker Quick Start](DOCKER_QUICK_START.md)** - быстрое руководство по оптимизированным образам

### Установка

Альтернативные методы установки:

- **[Нативная установка](NATIVE-INSTALLATION.md)** - установка без Docker на bare metal

## Быстрая навигация

### По задачам

| Задача | Документ |
|--------|----------|
| Быстро развернуть платформу | [QUICKSTART.md](QUICKSTART.md) |
| Настроить production окружение | [DEPLOYMENT.md](DEPLOYMENT.md) |
| Создать безопасного пользователя | [USER-SETUP.md](USER-SETUP.md) |
| Сканировать реальные серверы | [REAL-HOSTS-SCANNING.md](REAL-HOSTS-SCANNING.md) |
| Настроить логирование | [LOGGING.md](LOGGING.md) |
| Оптимизировать Docker образы | [DOCKER_OPTIMIZATIONS.md](DOCKER_OPTIMIZATIONS.md) |
| Установить без Docker | [NATIVE-INSTALLATION.md](NATIVE-INSTALLATION.md) |

### По компонентам

| Компонент | Где описан |
|-----------|------------|
| OpenSCAP | [QUICKSTART.md](QUICKSTART.md), [REAL-HOSTS-SCANNING.md](REAL-HOSTS-SCANNING.md) |
| Lynis | [QUICKSTART.md](QUICKSTART.md), [REAL-HOSTS-SCANNING.md](REAL-HOSTS-SCANNING.md) |
| Atomic Red Team | [QUICKSTART.md](QUICKSTART.md), [SECURITY.md](SECURITY.md) |
| Prometheus | [DEPLOYMENT.md](DEPLOYMENT.md), [SECURITY.md](SECURITY.md) |
| Grafana | [QUICKSTART.md](QUICKSTART.md), [DEPLOYMENT.md](DEPLOYMENT.md) |
| Telegraf | [DEPLOYMENT.md](DEPLOYMENT.md) |
| Loki | [LOGGING.md](LOGGING.md) |

## Архитектура платформы

```
┌─────────────────────────────────────────────────────────┐
│                    test-hard Platform                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Security Scanners          Monitoring Stack             │
│  ├── OpenSCAP               ├── Prometheus              │
│  ├── Lynis                  ├── Grafana                 │
│  └── Atomic Red Team        ├── Alertmanager            │
│                              └── Telegraf                │
│                                                          │
│  Logging                    Docker Security              │
│  ├── Loki                   └── Socket Proxy            │
│  └── Promtail                                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Режимы работы

Платформа поддерживает три режима сканирования:

1. **Тестовые контейнеры** (по умолчанию) - для демонстрации и разработки
2. **Реальные хосты через SSH** - для production серверов и VM
3. **Production Docker контейнеры** - через Docker API

Подробнее: [REAL-HOSTS-SCANNING.md](REAL-HOSTS-SCANNING.md)

## Требования

### Минимальные

- Docker 20.10+
- Docker Compose v2.0+
- 2 CPU cores
- 4 GB RAM
- 10 GB disk space

### Рекомендуемые

- Docker 24.0+
- Docker Compose v2.20+
- 4 CPU cores
- 8 GB RAM
- 50 GB disk space

## Поддержка

### Документация

- Читайте документацию в этой директории
- [CONTRIBUTING.md](../CONTRIBUTING.md) - как внести вклад
- [GitHub Issues](https://github.com/alexbergh/test-hard/issues) - сообщить о проблеме

### Сообщество

- Задавайте вопросы через GitHub Issues
- Присылайте Pull Requests

## Обновления

Документация регулярно обновляется. Последнее обновление: 24.11.2025

## Лицензия

Проект распространяется под лицензией MIT. См. [LICENSE](../LICENSE).

---

**Полезные команды:**

```bash
# Показать все доступные команды
make help

# Запустить платформу
make up

# Проверить статус
make status

# Запустить сканирование
make scan

# Посмотреть логи
make logs
```
