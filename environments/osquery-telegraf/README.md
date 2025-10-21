# Osquery + Telegraf окружение

Лёгкий агентский стек для инвентаризации, мониторинга и ad-hoc проверок с отправкой данных в KUMA/Grafana.

## Компоненты
- **Osquery Agents** — устанавливаются на конечные системы и выполняют SQL-запросы.
- **Telegraf Forwarder** — собирает результаты osquery и проксирует их в выбранную систему аналитики.
- **InfluxDB + Grafana (опционально)** — пилотный стек визуализации и алертинга.

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
- `grafana` для дашбордов.

Развертывание:
```bash
cd docker
docker compose up -d
```

## Поток данных
1. Osquery формирует результаты и пишет в `/var/log/osquery/*.log`.
2. Telegraf tail-input считывает JSON и отправляет по HTTP/InfluxDB.
3. Осадки попадют в KUMA или в локальный InfluxDB -> Grafana.
4. Пакеты `inventory.conf` и `vulnerability-management.conf` обеспечивают контроль состава ПО и версий.

## Безопасность
- Хранить токены/пароли Telegraf в Ansible Vault.
- Включить TLS для HTTP-output и listener, при необходимости использовать mTLS.
- Использовать RBAC в Grafana и права read-only на результирующие дашборды.

## Интеграция с hardening-сценариями
Osquery пакеты покрывают проверки из [Linux](../../hardening-scenarios/linux.md) и [Windows](../../hardening-scenarios/windows.md) сценариев, а события передаются в SOC для подтверждения внедрения мер.
