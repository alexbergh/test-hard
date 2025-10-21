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
=======
## Цель
Предоставить лёгкий агентский стек для инвентаризации, сбора метрик и запуска ad-hoc скриптов с отправкой данных в KUMA или Grafana.

## Архитектура
- **Osquery Agents** — устанавливаются на Linux, Windows, macOS.
- **Telegraf Forwarder** — собирает результаты osquery через `exec`/`socket_listener` и отправляет в KUMA (через Kafka/HTTP) или Grafana Loki/InfluxDB.
- **Configuration Management** — управление через Ansible/SaltStack, хранение pack-файлов в Git.
- **Central Dashboard** — KUMA SIEM либо Grafana (через Prometheus/InfluxDB).

## Компоненты
| Компонент | Назначение | Ресурсы |
|-----------|------------|---------|
| Osquery | SQL-подобные запросы к ОС, инвентаризация | ~50 МБ RAM на хост |
| Telegraf | Буферизация и доставка метрик | 1 vCPU, 256 МБ RAM |
| Message Broker (Kafka/Redis) | Очередь сообщений в KUMA | Завист от нагрузки |
| Grafana / KUMA | Визуализация, алертинг | HA по стандартам SOC |

## Развертывание
1. **Репозиторий конфигураций**
   - Создать Git-репозиторий `osquery-packs` c pack-файлами (CIS, инвентарь, обнаружение отклонений).
   - Хранить конфигурацию Telegraf (`telegraf.d/osquery.conf`).

2. **Установка агентов**
   - Linux: rpm/deb пакеты, systemd unit `osqueryd`.
   - Windows: MSI пакет, настройка osquery flags (`--logger_min_status=1`).
   - Настроить сертификаты TLS для `tls_config` (osquery->fleet/telegraf).

3. **Интеграция Osquery и Telegraf**
   - Пример конфигурации `telegraf.d/osquery.conf`:
     ```toml
     [[inputs.exec]]
       commands = ["/usr/bin/osqueryi --json 'select * from processes;'" ]
       data_format = "json"
       interval = "1m"

     [[outputs.http]]
       url = "https://kuma.example.com/collector"
       method = "POST"
       data_format = "json"
       timeout = "5s"
     ```
   - Для Grafana/InfluxDB использовать `[[outputs.influxdb]]` с retention policies.

4. **Поток в KUMA**
   - Telegraf отправляет события в KUMA Data Collector (HTTP или Kafka).
   - KUMA обогащает события CMDB, строит таймлайны.

5. **Поток в Grafana**
   - Интеграция с InfluxDB/Prometheus для метрик.
   - Настроить Grafana dashboards: состояние обновлений, изменения конфигурации, контроль сервисов.

6. **Ad-hoc скрипты**
   - Использовать osquery `distributed queries` через FleetDM или Kolide.
   - Результаты обрабатываются Telegraf exec input и транслируются в SOC.

## Безопасность и контроль доступа
- Разделить права на чтение/запуск pack-файлов через RBAC FleetDM.
- Хранить секреты Telegraf в HashiCorp Vault/Ansible Vault.
- Настроить алерты: изменение критичных файлов, запуск подозрительных процессов.

## Интеграция с hardening-сценариями
- Osquery пакеты реализуют проверки из сценариев hardening для Linux/Windows.
- Результаты передаются в SOC для контроля внедрения мер.