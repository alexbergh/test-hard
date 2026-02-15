# Документация test-hard

Центральная страница документации платформы security hardening, runtime-безопасности и мониторинга контейнеров.

## Структура документации

### Начало работы

- **[Быстрый старт](QUICKSTART.md)** -- развертывание за 5-10 минут
- **[Полное руководство по развертыванию](DEPLOYMENT.md)** -- детальная инструкция с troubleshooting
- **[Troubleshooting](TROUBLESHOOTING.md)** -- решение типичных проблем
- **[FAQ](FAQ.md)** -- часто задаваемые вопросы

### Безопасность

- **[Политика безопасности](SECURITY.md)** -- security features, alerts, best practices
- **[Настройка пользователей (полная)](USER-SETUP.md)** -- детальное руководство по созданию безопасных пользователей
- **[Настройка пользователей (краткая)](QUICK-USER-SETUP.md)** -- быстрая справка по безопасности

### Сканирование и мониторинг

- **[Сканирование реальных хостов](REAL-HOSTS-SCANNING.md)** -- сканирование production серверов, VM и Docker контейнеров
- **[Централизованное логирование](LOGGING.md)** -- настройка и использование Loki + Promtail

### Docker и развертывание

- **[Docker оптимизации](DOCKER_OPTIMIZATIONS.md)** -- multi-stage builds, BuildKit cache, метрики
- **[Docker Quick Start](DOCKER_QUICK_START.md)** -- быстрое руководство по оптимизированным образам
- **[Локальная сборка образа](LOCAL-BUILD.md)** -- сборка unified Docker образа без доступа к GHCR

### Установка

- **[Нативная установка](NATIVE-INSTALLATION.md)** -- установка без Docker на bare metal / VM / BSD

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
| Собрать образ локально | [LOCAL-BUILD.md](LOCAL-BUILD.md) |

### По компонентам

| Компонент | Где описан |
|-----------|------------|
| OpenSCAP | [QUICKSTART.md](QUICKSTART.md), [REAL-HOSTS-SCANNING.md](REAL-HOSTS-SCANNING.md) |
| Lynis | [QUICKSTART.md](QUICKSTART.md), [REAL-HOSTS-SCANNING.md](REAL-HOSTS-SCANNING.md) |
| Atomic Red Team | [QUICKSTART.md](QUICKSTART.md), [SECURITY.md](SECURITY.md) |
| Falco / Falcosidekick | [QUICKSTART.md](QUICKSTART.md), [DEPLOYMENT.md](DEPLOYMENT.md), [SECURITY.md](SECURITY.md) |
| Trivy | [QUICKSTART.md](QUICKSTART.md), [DEPLOYMENT.md](DEPLOYMENT.md) |
| Prometheus | [DEPLOYMENT.md](DEPLOYMENT.md), [SECURITY.md](SECURITY.md) |
| Grafana | [QUICKSTART.md](QUICKSTART.md), [DEPLOYMENT.md](DEPLOYMENT.md) |
| Telegraf | [DEPLOYMENT.md](DEPLOYMENT.md) |
| Loki / Promtail | [LOGGING.md](LOGGING.md) |
| Web Dashboard | [../dashboard/README.md](../dashboard/README.md) |

## Архитектура платформы

```
+---------------------------------------------------------------+
|                      test-hard Platform                        |
+---------------------------------------------------------------+
|                                                               |
|  Security Scanners        Runtime Security                    |
|  +-- OpenSCAP             +-- Falco (syscall monitoring)      |
|  +-- Lynis                +-- Falcosidekick (event routing)   |
|  +-- Atomic Red Team      +-- Falco Exporter (Prometheus)     |
|  +-- Trivy (images)       +-- Falco Responder (auto-actions)  |
|                                                               |
|  Monitoring Stack         Logging                             |
|  +-- Prometheus           +-- Loki                            |
|  +-- Grafana (10 dashb.)  +-- Promtail                        |
|  +-- Alertmanager                                             |
|  +-- Telegraf             Docker Security                     |
|                           +-- Socket Proxy                    |
|  Web Dashboard                                                |
|  +-- FastAPI backend      Network Scanning                    |
|  +-- React frontend       +-- nmap host/port discovery        |
|                                                               |
+---------------------------------------------------------------+
```

## Режимы работы

Платформа поддерживает три режима сканирования:

1. **Тестовые контейнеры** (по умолчанию) -- для демонстрации и разработки
2. **Реальные хосты через SSH** -- для production серверов и VM
3. **Production Docker контейнеры** -- через Docker API

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

- [GitHub Issues](https://github.com/alexbergh/test-hard/issues) -- сообщить о проблеме
- [CONTRIBUTING.md](../CONTRIBUTING.md) -- как внести вклад

## Лицензия

Проект распространяется под лицензией MIT. См. [LICENSE](../LICENSE).

---

**Полезные команды:**

```bash
make help       # показать все доступные команды
make up         # запустить платформу
make status     # проверить статус
make scan       # запустить сканирование
make logs       # посмотреть логи
```

---

Последнее обновление: Февраль 2026
