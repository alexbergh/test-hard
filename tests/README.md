# Test Environments

Тестовые окружения предназначены для быстрой генерации логов и отчётов из пилотных стеков hardening-мониторинга.

## Docker Compose

В директории `tests/docker` находится единый Compose-проект с тремя профилями:

- `openscap` — одноразовый запуск контейнера OpenSCAP, который применяет локальное OVAL-правило и сохраняет ARF/HTML в `tests/docker/artifacts/openscap/`.
- `telemetry` — InfluxDB, Telegraf, Grafana и mock-инстанс KUMA с контейнером-симулятором osquery-агента, генерирующим телеметрию и собирающим батчи hardening-метрик.
- `wazuh` — компактный стек Wazuh (Indexer, Manager, Dashboard) и контейнер-агент, который регистрируется на менеджере и создаёт базовые события FIM/Syscollector.

### Запуск

```bash
# Все сервисы в фоне (отчёты/логи сохраняются в tests/docker/artifacts)
./tests/docker/run.sh all

# Однократный запуск OpenSCAP со сбором отчёта
./tests/docker/run.sh openscap
```

Если Docker недоступен, `run.sh` выполнит оффлайн-симуляцию, перед этим извлечёт базу ФСТЭК через `prepare_fstec_content.py` и сформирует примерные отчёты и логи в `tests/docker/artifacts`. Дополнительно генерируются Markdown-панель (`telemetry/hardening-dashboard.md`), экспорт дашборда Grafana (`telemetry/grafana-dashboard.json`) и payload для KUMA (`telemetry/kuma-payload.json`), чтобы визуально проверить метрики. Учебный архив `scanoval.zip` создаётся на лету утилитой `tests/tools/create_sample_fstec_archive.py`, поэтому бинарники не попадают в репозиторий. После запуска можно открыть Grafana на `http://localhost:3000` (admin/changeme) или Wazuh Dashboard на `https://localhost:5601` (admin/changeme), когда контейнеры реально подняты.

## Kubernetes (kind)

В `tests/k8s` содержится набор манифестов и helper-скриптов для развёртывания тестовых инстансов в кластер `kind`:

- `openscap-job.yaml` — Kubernetes Job, запускающий OpenSCAP с тем же OVAL-профилем.
- `telemetry.yaml` — ConfigMap, Deployment и Service для Telegraf + симулятор osquery.
- `wazuh.yaml` — Deployment менеджера и агента Wazuh.
- `kustomization.yaml` — объединённое описание для применения всех ресурсов.
- `kind-cluster.yaml` — конфигурация тестового кластера.

### Быстрый старт

```bash
./tests/k8s/setup-kind.sh
kubectl apply -k tests/k8s
kubectl logs job/openscap-scan -n hardening-test
```

Если `kind` не установлен, `setup-kind.sh` выполнит симуляцию, предварительно подготовит OVAL базу ФСТЭК (архив также формируется скриптом `tests/tools/create_sample_fstec_archive.py`) и сформирует сводку по манифестам и примерные логи в `tests/k8s/artifacts`. При наличии `kind` Job сохраняет результаты OpenSCAP в артефакт-контейнере (лог можно выгрузить командой `kubectl logs`), а логи Telegraf и Wazuh доступны через `kubectl logs` для соответствующих pod-ов.

## Виртуальные машины (Packer + симуляция)

Каталог `tests/vms` решает задачу подготовки тестовых/продуктивных образов RedOS 7.3/8, Astra Linux 1.7, Альт 8 и CentOS 7. Шаблон `packer/linux.pkr.hcl` поддерживает запуск с `packer build -var "distro=<id>" -var "environment=test|prod"`, а `run.sh` автоматически переключается на оффлайн-симуляцию, если гипервизор недоступен.

Симуляция `tests/vms/simulate.py` использует профили `hardening-scenarios/secaudit/profiles` и создаёт:

- `artifacts/<env>/<os>/build-plan.json` и `build-log.txt` — доказательства сборки образа.
- `artifacts/<env>/<os>/compliance-report.json` — отчёт о прохождении контролей `secaudit`.
- `artifacts/<env>/telemetry/` — события osquery (events/inventory JSONL), Markdown-панель, экспорт Grafana, payload KUMA и сводка метрик.

Эти артефакты используются в отчётах департамента DevOps как доказательство прохождения сценариев hardening для test/prod контуров.

## Агрегация процессных метрик
- Базовые значения метрик (время цикла, раунды ревью, MTTR, P95, расход бюджета ошибок) определены в `tests/shared/process_baseline.json`.
- Скрипты симуляции сохраняют `process-impact.json` и Markdown-версии с фактами для каждого контекста (docker/k8s/vm test/prod).
- После каждого запуска `tests/docker/run.sh`, `tests/k8s/setup-kind.sh` и `tests/vms/run.sh` автоматически вызывается `tests/tools/generate_process_report.py`, формирующий консолидированный отчёт `reports/2025-10-21-process-analytics.md` и JSON `reports/process-metrics-summary.json`.

