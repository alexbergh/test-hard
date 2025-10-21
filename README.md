# Hardening Monitoring Environments

Репозиторий содержит инфраструктурные шаблоны и автоматизацию для мониторинга hardening-процессов.

## Окружения
- [OpenSCAP Pilot](environments/openscap/README.md)
  - Ansible-плейбук: `environments/openscap/ansible/playbook.yml`.
- [Osquery + Telegraf](environments/osquery-telegraf/README.md)
  - Ansible-плейбук агентов: `environments/osquery-telegraf/ansible/playbook.yml`.
  - Docker Compose-стек для приёмника и визуализации: `environments/osquery-telegraf/docker/docker-compose.yml`.
- [Wazuh + Elastic Stack](environments/wazuh/README.md)
  - Docker Compose all-in-one: `environments/wazuh/docker/docker-compose.yml`.
  - Ansible-плейбук для агентов: `environments/wazuh/ansible/playbook.yml`.

## Сценарии hardening
- [Общие принципы и поток работ](hardening-scenarios/README.md).
- Linux-плейбук: `hardening-scenarios/ansible/playbooks/linux.yml`.
- Windows-плейбук: `hardening-scenarios/ansible/playbooks/windows.yml`.
- Методические заметки по платформам: [Linux](hardening-scenarios/linux.md), [Windows](hardening-scenarios/windows.md).

Каждое окружение и сценарий интегрированы: результаты OpenSCAP направляют приоритеты ремедиации, а osquery и Wazuh проверяют внедрение настроек.

## Тестовые окружения
- Docker Compose: `tests/docker` для быстрой генерации отчётов и телеметрии.
- Kubernetes (kind): `tests/k8s` для эмуляции стека в кластере.
=======
=======
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
