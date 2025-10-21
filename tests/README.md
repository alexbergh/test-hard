# Test Environments

Тестовые окружения предназначены для быстрой генерации логов и отчётов из пилотных стеков hardening-мониторинга.

## Docker Compose

В директории `tests/docker` находится единый Compose-проект с тремя профилями:

- `openscap` — одноразовый запуск контейнера OpenSCAP, который применяет локальное OVAL-правило и сохраняет ARF/HTML в `tests/docker/artifacts/openscap/`.
- `telemetry` — InfluxDB, Telegraf и Grafana с контейнером-симулятором osquery-агента, генерирующим телеметрию.
- `wazuh` — компактный стек Wazuh (Indexer, Manager, Dashboard) и контейнер-агент, который регистрируется на менеджере и создаёт базовые события FIM/Syscollector.

### Запуск

```bash
# Все сервисы в фоне (отчёты/логи сохраняются в tests/docker/artifacts)
./tests/docker/run.sh all

# Однократный запуск OpenSCAP со сбором отчёта
./tests/docker/run.sh openscap
```

После запуска можно открыть Grafana на `http://localhost:3000` (admin/changeme) или Wazuh Dashboard на `https://localhost:5601` (admin/changeme).

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

Job сохраняет результаты OpenSCAP в артефакт-контейнере (лог можно выгрузить командой `kubectl logs`). Логи Telegraf и Wazuh доступны через `kubectl logs` для соответствующих pod-ов.
