# Отчёт по визуализации hardening-метрик

Дата проверки: 21.10.2025

## Docker-стенд (osquery + Telegraf -> Grafana/KUMA)

- Генератор событий: `tests/docker/simulate.py` (оффлайн-режим, так как Docker недоступен).
- Итоги сканирования OpenSCAP: 1 определение, отклонений не выявлено.
- Телеметрия osquery: 10 событий (5 уязвимостей, 5 инвентаризаций) с одним хостом `simulated-osquery`.
- Сводная панель `tests/docker/artifacts/telemetry/hardening-dashboard.md` показывает 100% низкокритичных уязвимостей (CVE-2022-0778/CVE-2023-2650) и доминирование пакета `openssl`.
- Экспортированный дашборд Grafana (`.../grafana-dashboard.json`) включает панели «Vulnerability severity» и «Unique hosts» для InfluxDB `osquery`.
- Payload KUMA (`.../kuma-payload.json`) содержит 10 событий и агрегаты (уязвимости/инвентарь/уникальные хосты). Журнал коллектора (`.../collector.log`) подтверждает приём пакетов.

## kind-стенд (эмуляция k8s)

- Скрипт `tests/k8s/simulate.py` повторно формирует учебный архив ФСТЭК и строит сводку по манифестам.
- Логи Telemetry pod (`tests/k8s/artifacts/telemetry/pod.log`) фиксируют 10 событий (5 уязвимости + 5 инвентаризаций) с распределением критичности 60% Low / 40% Medium.
- Markdown-панель `tests/k8s/artifacts/telemetry/hardening-dashboard.md` отражает топ-CVE (`CVE-2023-2650`, `CVE-2024-2511`) и пакеты (`openssl`, `sudo`, `kernel`).
- Сформирован JSONL-файл с событиями (`tests/k8s/artifacts/telemetry/events.jsonl`), который можно отправить в KUMA или InfluxDB через вспомогательные утилиты.

## Выводы

- Цепочки формирования визуализаций и payload-ов срабатывают как в Docker-симуляции, так и в kind-окружении.
- Полученные артефакты позволяют импортировать данные в Grafana и KUMA, а также сверять фактические метрики hardening.
- Дальнейшие проверки могут запускаться регулярно; при появлении доступа к настоящим контейнерам требуется сменить профиль с симуляции на реальные сервисы без изменения playbook-ов.
