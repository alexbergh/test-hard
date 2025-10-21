# Hardening Monitoring Environments

Репозиторий содержит инфраструктурные шаблоны и автоматизацию для мониторинга hardening-процессов.

## Окружения
- [OpenSCAP Pilot](environments/openscap/README.md)
  - Ansible-плейбук: `environments/openscap/ansible/playbook.yml`.
- [Osquery + Telegraf](environments/osquery-telegraf/README.md)
  - Ansible-плейбук агентов: `environments/osquery-telegraf/ansible/playbook.yml`.
  - Docker Compose-стек для приёмника и визуализации: `environments/osquery-telegraf/docker/docker-compose.yml`.
  - Готовые шаблоны визуализаций: `tests/docker/artifacts/telemetry/hardening-dashboard.md` и `.../grafana-dashboard.json` (генерируются симуляторами).
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
- Docker Compose: `tests/docker` для быстрой генерации отчётов и телеметрии. При отсутствии Docker скрипты автоматически
  переключаются на оффлайн-симуляцию, подготавливают базу ФСТЭК через `prepare_fstec_content.py` и формируют примерные артефакты в `tests/docker/artifacts` (включая Markdown-панель hardening-метрик, экспорт дашборда Grafana и payload для KUMA). Учебный архив `scanoval.zip` собирается на лету утилитой `tests/tools/create_sample_fstec_archive.py`.
- Kubernetes (kind): `tests/k8s` для эмуляции стека в кластере. Скрипт `setup-kind.sh` создаёт кластер или запускает симуляцию
  логов и сводок, предварительно извлекая OVAL базу ФСТЭК (архив также формируется утилитой `tests/tools/create_sample_fstec_archive.py`), если бинарник `kind` недоступен.

## Отчёты пробных запусков
- Результаты текущей проверки оффлайн-симуляций: [reports/2025-10-21-simulation-results.md](reports/2025-10-21-simulation-results.md).
- Визуализация метрик osquery/Telegraf -> Grafana/KUMA: [reports/2025-10-21-monitoring-dashboard.md](reports/2025-10-21-monitoring-dashboard.md).
