# Проверка артефактов симуляций hardening

Дата проверки: 21 октября 2025 года

## Docker-симуляция (tests/docker/run.sh all)

- Подготовлен сводный файл `tests/docker/artifacts/simulation-summary.json` с указанием статуса всех подсистем.
- Отчёт OpenSCAP: `tests/docker/artifacts/openscap/scan-report.json` и текстовая сводка `scan-report.txt` подтверждают проверку одного OVAL-определения с успешным результатом.
- Телеметрия osquery/Telegraf:
  - Markdown-панель с итоговыми метриками: `tests/docker/artifacts/telemetry/hardening-dashboard.md` (5 уязвимостей, 5 инвентарных записей, 1 хост).
  - Экспорт дашборда Grafana: `tests/docker/artifacts/telemetry/grafana-dashboard.json` подтверждает готовность визуализации (панели bargauge и stat).
  - Payload для KUMA: `tests/docker/artifacts/telemetry/kuma-payload.json` включает 10 событий (5 уязвимостей, 5 инвентарей) и агрегированную статистику.
  - Журнал коллектора `tests/docker/artifacts/telemetry/collector.log` фиксирует суммарные показатели и выборку последних событий.
- Модуль Wazuh сформировал `tests/docker/artifacts/wazuh/alerts.json` (3 алерта) и `fim-events.jsonl` (3 записи), что подтверждает эмуляцию HIDS/FIM.

## kind-симуляция (tests/k8s/setup-kind.sh)

- Сводка развернутых ресурсов зафиксирована в `tests/k8s/artifacts/cluster-resources.json` и `cluster-overview.txt`.
- Лог выполнения OpenSCAP Job: `tests/k8s/artifacts/openscap-job.log` фиксирует успешное прохождение проверенного определения.
- Телеметрия osquery/Telegraf:
  - Журнал пода: `tests/k8s/artifacts/telemetry/pod.log` содержит 10 записей, подтверждающих отправку событий.
  - JSONL с событиями: `tests/k8s/artifacts/telemetry/events.jsonl` включает 10 строк (5 уязвимостей, 5 инвентарей).
  - Markdown-дашборд: `tests/k8s/artifacts/telemetry/hardening-dashboard.md` фиксирует распределение критичности (3 low, 2 medium).
  - Экспорт Grafana и payload KUMA расположены в `tests/k8s/artifacts/telemetry/grafana-dashboard.json` и `kuma-payload.json` соответственно.
- Лог Wazuh: `tests/k8s/artifacts/wazuh-pod.log` отражает 6 записей (3 алерта, 3 FIM события).

## Выводы

Обе симуляции сгенерировали полный набор артефактов hardening: отчёты OpenSCAP, телеметрию osquery/Telegraf с визуализацией для Grafana и KUMA, а также события Wazuh. Полученные файлы можно использовать как доказательную базу для демонстрации работоспособности пилотных стендов и проверок информационной безопасности.
