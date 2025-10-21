# Hardening Monitoring Environments

Репозиторий содержит описание инфраструктурных окружений и сценариев hardening для задач мониторинга и аудита.

## Окружения
- [OpenSCAP Pilot](environments/openscap/README.md) — формальный аудит в соответствии с ФСТЭК 17/21 и CIS, интеграция с Kaspersky KEA/KSC.
- [Osquery + Telegraf](environments/osquery-telegraf/README.md) — лёгкий инвентарь и сбор ad-hoc-метрик в KUMA/Grafana.
- [Wazuh + Elastic Stack](environments/wazuh/README.md) — HIDS/FIM функциональность.

## Сценарии hardening
- [Общие сценарии](hardening-scenarios/README.md)
- [Linux](hardening-scenarios/linux.md)
- [Windows](hardening-scenarios/windows.md)

Каждый сценарий увязывает контрольные мероприятия с соответствующим окружением мониторинга.
