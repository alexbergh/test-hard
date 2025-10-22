# Osquery + Telegraf окружение

Лёгкий агентский стек для инвентаризации, мониторинга и ad-hoc проверок с отправкой данных в KUMA/Grafana.

## Компоненты
- **Osquery Agents** — устанавливаются на конечные системы и выполняют SQL-запросы.
- **Telegraf Forwarder** — собирает результаты osquery и проксирует их в выбранную систему аналитики.
- **InfluxDB + Grafana (опционально)** — пилотный стек визуализации и алертинга.
- **KUMA (по лицензии)** — корпоративная платформа мониторинга; в тестовом стенде её API имитирует `tests/docker/kuma-mock`.

## Автоматизация агентов
Ansible-плейбук `ansible/playbook.yml`:
1. Подключает официальные репозитории osquery и InfluxData.
2. Устанавливает `osqueryd` и `telegraf`.
3. Разворачивает конфигурацию `osquery.conf` и pack-файлы (`files/packs`).
4. Настраивает Telegraf outputs (HTTP, InfluxDB) на основании переменных `telegraf_outputs`.

Запуск:
```bash
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml
```
Переменные изменяются в `ansible/group_vars/osquery_agents.yml`.

## Центральный сборщик
В каталоге `docker/` находится `docker-compose.yml`, разворачивающий:
- `influxdb` для хранения метрик;
- `telegraf-listener` с входами `http_listener_v2` и `syslog`;
- `grafana` для дашбордов;
- `kuma-mock` — контейнер на Python, принимающий JSON-пакеты и имитирующий REST API KUMA для тестов.

Развертывание:
```bash
cd docker
docker compose up -d
```

## Поток данных
1. Osquery формирует результаты и пишет в `/var/log/osquery/*.log`.
2. Telegraf через `inputs.exec` опрашивает `osqueryi` и отправляет результаты по HTTP/InfluxDB.
3. Осадки попадют в KUMA или в локальный InfluxDB -> Grafana.
4. Пакеты `inventory.conf`, `vulnerability-management.conf`, `security_monitoring.conf` и `compliance_checks.conf` обеспечивают контроль состава ПО, состояние безопасности и проверку политик.

## Готовый шаблон мониторинга

Роль `osquery_telegraf` разворачивает полноценную связку «осмотр → доставка» по умолчанию:

- Основной конфиг `osquery.conf` включает базовый инвентаризационный график (`system_info`, `os_version`) и подключает пакеты `security_monitoring` и `compliance_checks`.
- Пакеты лежат в `ansible/roles/osquery_telegraf/files/packs/` и покрывают:
  - мониторинг безопасности (установленные пакеты, сетевые порты, локальные администраторы, свежая shell-история, cron-задачи);
  - проверки соответствия (SUID-бинарники, `PermitRootLogin`, состояние `iptables`).
- Шаблон `telegraf.conf` настраивает агента на чтение результатов через `inputs.exec` (вызовы `osqueryi --json ...`) и передачу событий как в KUMA (HTTP), так и в InfluxDB/Grafana.

Все параметры выносятся в `group_vars/osquery_agents.yml`: здесь настраиваются список пакетов, команды `inputs.exec`, а также outputs (`http`, `influxdb_v2`, и др.). Это позволяет быстро переключить сбор событий между SIEM (KUMA), системами визуализации (Grafana/InfluxDB) или другими получателями.

## Безопасность
- Хранить токены/пароли Telegraf в Ansible Vault.
- Включить TLS для HTTP-output и listener, при необходимости использовать mTLS.
- Использовать RBAC в Grafana и права read-only на результирующие дашборды.

## Интеграция с hardening-сценариями
Osquery пакеты покрывают проверки из [Linux](../../hardening-scenarios/linux.md) и [Windows](../../hardening-scenarios/windows.md) сценариев, а события передаются в SOC для подтверждения внедрения мер.


## Контейнерные образы

- `grafana/grafana:10.4.1` — официальный образ Grafana (Docker Hub).
- `influxdb:2.7`, `telegraf:1.28` — официальный стек InfluxData.
- `registry.kaspersky.local/kuma/collector:<tag>` — приватный образ Kaspersky Unified Monitoring and Analysis Platform (для реальной интеграции требуется доступ к корпоративному реестру; в тестовом стенде используется `tests/docker/kuma-mock`).

Mock-коллектор сохраняет входящие события в общий volume и позволяет просматривать их через HTTP `GET /`.
