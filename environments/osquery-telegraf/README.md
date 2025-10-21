# Osquery + Telegraf окружение

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
