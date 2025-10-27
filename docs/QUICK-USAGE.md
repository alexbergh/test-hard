# Быстрый запуск Test-Hard

## Описание

Security hardening сканер для Linux контейнеров.

**Проверяет**: Debian, Ubuntu, Fedora, CentOS Stream  
**Сканеры**: Lynis + OpenSCAP  
**Визуализация**: Grafana + Prometheus

---

## Запуск в 3 шага

### 1. Настройка (один раз)

```bash
# Создать .env
cp .env.example .env
nano .env  # Измените GF_ADMIN_PASSWORD!

# Запустить мониторинг
docker compose up -d prometheus grafana telegraf alertmanager docker-proxy
```

### 2. Сканирование

```bash
# Запустить проверку безопасности
./scripts/run_hardening_suite.sh
```

**Выполняемые действия**:
- Запуск 4 тестовых контейнеров (Debian, Ubuntu, Fedora, CentOS)
- Запуск Lynis security audit
- Запуск OpenSCAP compliance check
- Сохранение отчётов в `./reports/`
- Отправка метрик в Prometheus

**Время выполнения**: ~5-10 минут

### 3. Просмотр результатов

```bash
# Открыть Grafana
open http://localhost:3000

# Логин: admin
# Пароль: из вашего .env (GF_ADMIN_PASSWORD)
```

---

## Результаты

### Локальные отчёты

```bash
# Просмотреть отчёты
ls -lh reports/

reports/
├── fedora/
│   ├── lynis-report.json      ← JSON отчёт Lynis
│   └── openscap/
│       └── report.arf         ← XML отчёт OpenSCAP
├── debian/
├── centos/
└── ubuntu/
```

### Метрики в Prometheus

```bash
# Открыть Prometheus
open http://localhost:9090

# Примеры запросов:
lynis_score                    # Security score (0-100)
lynis_warnings_count           # Количество предупреждений
openscap_fail_count            # Провальные проверки
```

### Дашборды Grafana

1. Откройте http://localhost:3000
2. Перейдите в Dashboards
3. Найдите "Security Hardening Overview"

**Доступные данные**:
- Lynis scores по всем хостам
- Тренды изменений
- Топ проблем безопасности
- OpenSCAP compliance статус

---

## Регулярное использование

```bash
# Каждый день/неделю
./scripts/run_hardening_suite.sh

# Проверить Grafana
open http://localhost:3000

# Проверить алерты
open http://localhost:9093
```

---

## Основные команды

```bash
# Запуск
./scripts/run_hardening_suite.sh    # Полное сканирование
make hardening-suite                # То же через Makefile
make up                             # Запустить всё

# Мониторинг
make health                         # Проверка сервисов
make logs                           # Просмотр логов

# Очистка
make clean                          # Удалить старые отчёты
make down                           # Остановить всё
```

---

## Интерпретация результатов

### Lynis Score

| Score | Статус | Что делать |
|-------|--------|-----------|
| 90-100 | Отлично | Всё хорошо |
| 70-89 | Хорошо | Исправить критичное |
| 50-69 | Средне | Требуется hardening |
| < 50 | Плохо | Срочно улучшить |

### OpenSCAP

- **pass** - Проверка пройдена
- **fail** - Требуется исправление
- **error** - Ошибка проверки

---

## Частые проблемы

### Сканеры не запускаются

```bash
# Пересобрать образы
docker compose build openscap-scanner lynis-scanner

# Проверить docker-proxy
docker compose ps docker-proxy
```

### Метрики не появляются

```bash
# Проверить Telegraf
curl http://localhost:9091/metrics

# Перезапустить
docker compose restart telegraf
```

### Grafana не показывает данные

1. Configuration → Data Sources → Prometheus
2. URL: `http://prometheus:9090`
3. Save & Test

---

## Следующие шаги

1. **Настроить автоматическое сканирование** (cron):
   ```bash
   # Добавить в crontab
   0 2 * * * cd /path/to/test-hard && ./scripts/run_hardening_suite.sh
   ```

2. **Настроить алерты** в `prometheus/alertmanager.yml`

3. **Исправить найденные проблемы** на основе рекомендаций Lynis

4. **Добавить свои контейнеры** в docker-compose.yml

---

## Полная документация

- `USER-GUIDE.md` ← Полное руководство пользователя
- `README.md` - Обзор проекта
- `TROUBLESHOOTING.md` - Детальное решение проблем
- `SECURITY.md` - Security best practices

---

## Checklist

Ежедневно:
- [ ] Запустить `./scripts/run_hardening_suite.sh`
- [ ] Проверить Grafana дашборд
- [ ] Проверить алерты

Еженедельно:
- [ ] Проанализировать тренды
- [ ] Исправить критичные issues

---

**Готово! Теперь у вас автоматизированный security hardening scanner.**
