# Индекс документации Test-Hard

## Для быстрого старта

Если вы **впервые** используете проект:

1. **START HERE**: [FINAL-SUMMARY-FOR-USER.md](FINAL-SUMMARY-FOR-USER.md)
   - Что это за проект
   - Что изменилось
   - Как использовать

2. **QUICK START**: [QUICK-USAGE.md](QUICK-USAGE.md)
   - 3 шага для запуска
   - Основные команды
   - 5 минут чтения

3. **MAIN GUIDE**: [README-SECURITY-SCANNING.md](README-SECURITY-SCANNING.md)
   - Полное руководство по security scanning
   - Workflow
   - Интерпретация результатов
   - 15 минут чтения

---

## 📖 Документация по категориям

### Для пользователей (Security Scanning)

| Документ | Описание | Когда читать |
|----------|----------|--------------|
| [FINAL-SUMMARY-FOR-USER.md](FINAL-SUMMARY-FOR-USER.md) | Итоговая сводка для пользователя | **ПЕРВЫМ** |
| [QUICK-USAGE.md](QUICK-USAGE.md) | Быстрая инструкция (3 шага) | Для быстрого старта |
| [README-SECURITY-SCANNING.md](README-SECURITY-SCANNING.md) | Полное руководство пользователя | Основная документация |
| [USER-GUIDE.md](USER-GUIDE.md) | Детальное руководство | Если нужны все детали |
| [QUICKSTART.md](QUICKSTART.md) | 5-минутный quick start | Альтернативный quick start |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Решение проблем | Если что-то не работает |
| [SECURITY.md](SECURITY.md) | Security best practices | Для production |

### Для разработчиков (Development)

| Документ | Описание | Когда читать |
|----------|----------|--------------|
| [README.md](README.md) | Общий обзор проекта | Первое знакомство с проектом |
| [docs/CI-CD.md](docs/CI-CD.md) | CI/CD pipeline guide | Если работаете с CI/CD |
| [docs/DEVOPS-IMPROVEMENTS.md](docs/DEVOPS-IMPROVEMENTS.md) | DevOps аудит и улучшения | Для понимания архитектуры |
| [docs/METRICS.md](docs/METRICS.md) | Полный список метрик | Reference для метрик |

### Для DevOps (Deployment)

| Документ | Описание | Когда читать |
|----------|----------|--------------|
| [k8s/README.md](k8s/README.md) | Kubernetes deployment | Если деплоите в k8s |
| [docker-compose.yml](docker-compose.yml) | Base configuration | Всегда |
| [docker-compose.dev.yml](docker-compose.dev.yml) | Development overrides | Для dev окружения |
| [docker-compose.staging.yml](docker-compose.staging.yml) | Staging config | Для staging |
| [docker-compose.prod.yml](docker-compose.prod.yml) | Production config | Для production |

### Технические отчёты

| Документ | Описание | Когда читать |
|----------|----------|--------------|
| [PHASE1-COMPLETE.md](PHASE1-COMPLETE.md) | Отчёт завершения Phase 1 | Детали реализации |
| [FILES-CREATED.md](FILES-CREATED.md) | Список всех файлов | Для навигации по проекту |
| [README-UPDATES.md](README-UPDATES.md) | Объявление обновлений | Что нового в v1.0.0 |
| [SUMMARY.md](SUMMARY.md) | Краткая сводка | Executive summary |
| [CHANGELOG.md](CHANGELOG.md) | История изменений | Все изменения по версиям |

---

## 🗺Навигация по задачам

### Я хочу...

#### ...запустить security сканирование
→ [README-SECURITY-SCANNING.md](README-SECURITY-SCANNING.md)  
→ [QUICK-USAGE.md](QUICK-USAGE.md)

#### ...понять что изменилось в v1.0.0
→ [FINAL-SUMMARY-FOR-USER.md](FINAL-SUMMARY-FOR-USER.md)  
→ [README-UPDATES.md](README-UPDATES.md)

#### ...настроить CI/CD
→ [docs/CI-CD.md](docs/CI-CD.md)  
→ [.github/workflows/ci.yml](.github/workflows/ci.yml)

#### ...задеплоить в Kubernetes
→ [k8s/README.md](k8s/README.md)  
→ [k8s/base/](k8s/base/)

#### ...решить проблему
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md)  
→ [USER-GUIDE.md](USER-GUIDE.md) (раздел Troubleshooting)

#### ...понять метрики
→ [docs/METRICS.md](docs/METRICS.md)  
→ [README-SECURITY-SCANNING.md](README-SECURITY-SCANNING.md) (раздел Metrics)

#### ...улучшить безопасность
→ [SECURITY.md](SECURITY.md)  
→ [docker-compose.prod.yml](docker-compose.prod.yml)

#### ...написать тесты
→ [tests/conftest.py](tests/conftest.py)  
→ [pytest.ini](pytest.ini)

#### ...понять архитектуру
→ [docs/DEVOPS-IMPROVEMENTS.md](docs/DEVOPS-IMPROVEMENTS.md)  
→ [PHASE1-COMPLETE.md](PHASE1-COMPLETE.md)

---

## Структура проекта

```
test-hard/
│
├── 📄 Для пользователей (START HERE)
│   ├── FINAL-SUMMARY-FOR-USER.md     ← ЧИТАТЬ ПЕРВЫМ
│   ├── README-SECURITY-SCANNING.md   ← Основное руководство
│   ├── QUICK-USAGE.md                ← 3 шага
│   ├── USER-GUIDE.md                 ← Полное руководство
│   └── TROUBLESHOOTING.md            ← Решение проблем
│
├── 📄 Для разработчиков
│   ├── README.md                     ← Обзор проекта
│   ├── docs/CI-CD.md                 ← CI/CD guide
│   ├── docs/DEVOPS-IMPROVEMENTS.md   ← Архитектура
│   └── docs/METRICS.md               ← Метрики
│
├── 📄 Технические отчёты
│   ├── PHASE1-COMPLETE.md            ← Детальный отчёт
│   ├── FILES-CREATED.md              ← Список файлов
│   ├── README-UPDATES.md             ← Что нового
│   ├── SUMMARY.md                    ← Краткая сводка
│   └── CHANGELOG.md                  ← История
│
├── 🐳 Docker Compose
│   ├── docker-compose.yml            ← Base
│   ├── docker-compose.dev.yml        ← Development
│   ├── docker-compose.staging.yml    ← Staging
│   └── docker-compose.prod.yml       ← Production
│
├── ☸Kubernetes
│   ├── k8s/README.md                 ← K8s guide
│   ├── k8s/base/                     ← Base manifests
│   └── k8s/overlays/                 ← Environment overlays
│
├── 🧪 Tests
│   ├── tests/unit/                   ← Unit tests
│   ├── tests/integration/            ← Integration tests
│   └── pytest.ini                    ← Config
│
├── 🔧 Scripts
│   ├── run_hardening_suite.sh        ← MAIN SCRIPT
│   ├── parse_lynis_report.py         ← Lynis parser
│   ├── parse_openscap_report.py      ← OpenSCAP parser
│   ├── test-core-functionality.sh    ← Test script
│   └── bump-version.sh               ← Version management
│
├── Monitoring
│   ├── prometheus/                   ← Prometheus config
│   ├── grafana/                      ← Grafana dashboards
│   └── telegraf/                     ← Telegraf config
│
└── 🔐 Security
    ├── scanners/lynis/               ← Lynis scanner
    ├── scanners/openscap/            ← OpenSCAP scanner
    └── SECURITY.md                   ← Security practices
```

---

## Рекомендуемый порядок чтения

### Сценарий 1: Первый раз используете проект

1. [FINAL-SUMMARY-FOR-USER.md](FINAL-SUMMARY-FOR-USER.md) (5 мин)
2. [QUICK-USAGE.md](QUICK-USAGE.md) (3 мин)
3. [README-SECURITY-SCANNING.md](README-SECURITY-SCANNING.md) (15 мин)
4. Запустить сканирование
5. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) (если проблемы)

**Итого**: ~25 минут + запуск

### Сценарий 2: Обновились с предыдущей версии

1. [FINAL-SUMMARY-FOR-USER.md](FINAL-SUMMARY-FOR-USER.md) (5 мин)
2. [README-UPDATES.md](README-UPDATES.md) (5 мин)
3. [CHANGELOG.md](CHANGELOG.md) - Breaking Changes (2 мин)
4. Обновить `.env`
5. Перезапустить

**Итого**: ~15 минут + миграция

### Сценарий 3: Разработчик проекта

1. [README.md](README.md) (10 мин)
2. [docs/DEVOPS-IMPROVEMENTS.md](docs/DEVOPS-IMPROVEMENTS.md) (20 мин)
3. [docs/CI-CD.md](docs/CI-CD.md) (15 мин)
4. [PHASE1-COMPLETE.md](PHASE1-COMPLETE.md) (15 мин)
5. [tests/conftest.py](tests/conftest.py) - примеры тестов

**Итого**: ~60 минут

### Сценарий 4: DevOps/SRE

1. [docs/DEVOPS-IMPROVEMENTS.md](docs/DEVOPS-IMPROVEMENTS.md) (20 мин)
2. [k8s/README.md](k8s/README.md) (10 мин)
3. [docker-compose.prod.yml](docker-compose.prod.yml) (5 мин)
4. [SECURITY.md](SECURITY.md) (10 мин)
5. [docs/CI-CD.md](docs/CI-CD.md) (15 мин)

**Итого**: ~60 минут

---

## Поиск по темам

### Security
- [SECURITY.md](SECURITY.md) - Best practices
- [README-SECURITY-SCANNING.md](README-SECURITY-SCANNING.md) - Scanning guide
- [docker-compose.prod.yml](docker-compose.prod.yml) - Production security

### Monitoring
- [docs/METRICS.md](docs/METRICS.md) - All metrics
- [prometheus/](prometheus/) - Prometheus config
- [grafana/](grafana/) - Dashboards

### Testing
- [tests/](tests/) - Test suite
- [pytest.ini](pytest.ini) - Config
- [docs/CI-CD.md](docs/CI-CD.md) - CI testing

### Deployment
- [k8s/README.md](k8s/README.md) - Kubernetes
- [docker-compose.*.yml](docker-compose.yml) - Docker Compose
- [docs/CI-CD.md](docs/CI-CD.md) - CD pipeline

### Troubleshooting
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
- [USER-GUIDE.md](USER-GUIDE.md) - User guide
- Логи: `make logs` или `docker compose logs`

---

## 📞 Куда обращаться

### У меня проблема с...

**Security сканированием**:
1. [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. [README-SECURITY-SCANNING.md](README-SECURITY-SCANNING.md) - раздел Troubleshooting
3. `docker compose logs <service>`

**CI/CD**:
1. [docs/CI-CD.md](docs/CI-CD.md) - раздел Troubleshooting
2. GitHub Actions logs
3. `.github/workflows/`

**Kubernetes**:
1. [k8s/README.md](k8s/README.md) - раздел Troubleshooting
2. `kubectl logs` / `kubectl describe`

**Docker Compose**:
1. [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. `docker compose logs`
3. `docker compose config` - validate

---

## Quick Links

### Самое важное

- [Быстрый старт](QUICK-USAGE.md)
- 📖 [Основное руководство](README-SECURITY-SCANNING.md)
- 🔧 [Решение проблем](TROUBLESHOOTING.md)
- [Метрики](docs/METRICS.md)
- 🔐 [Безопасность](SECURITY.md)

### Конфигурация

- [docker-compose.yml](docker-compose.yml) - Base
- [.env.example](.env.example) - Environment vars
- [prometheus/prometheus.yml](prometheus/prometheus.yml) - Prometheus
- [grafana/](grafana/) - Grafana

### Скрипты

- [run_hardening_suite.sh](scripts/run_hardening_suite.sh) - **MAIN SCRIPT**
- [Makefile](Makefile) - Automation commands
- [bump-version.sh](scripts/bump-version.sh) - Versioning

---

## 🎓 Обучающие материалы

### Для начинающих

1. [FINAL-SUMMARY-FOR-USER.md](FINAL-SUMMARY-FOR-USER.md)
2. [QUICK-USAGE.md](QUICK-USAGE.md)
3. [README-SECURITY-SCANNING.md](README-SECURITY-SCANNING.md)

### Для продвинутых

1. [USER-GUIDE.md](USER-GUIDE.md)
2. [docs/METRICS.md](docs/METRICS.md)
3. [SECURITY.md](SECURITY.md)

### Для экспертов

1. [docs/DEVOPS-IMPROVEMENTS.md](docs/DEVOPS-IMPROVEMENTS.md)
2. [docs/CI-CD.md](docs/CI-CD.md)
3. [k8s/README.md](k8s/README.md)
4. [PHASE1-COMPLETE.md](PHASE1-COMPLETE.md)

---

**Используйте этот индекс как навигацию по документации!**

*Последнее обновление: October 27, 2024 - v1.0.0*
