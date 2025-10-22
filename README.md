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
- Linux-плейбук: `hardening-scenarios/ansible/playbooks/linux.yml` (включая роль `secaudit_profiles` для профилей RedOS/Astra/Alt/CentOS).
- Windows-плейбук: `hardening-scenarios/ansible/playbooks/windows.yml`.
- Методические заметки по платформам: [Linux](hardening-scenarios/linux.md), [Windows](hardening-scenarios/windows.md).

Каждое окружение и сценарий интегрированы: результаты OpenSCAP направляют приоритеты ремедиации, а osquery и Wazuh проверяют внедрение настроек. Профили `secaudit` обеспечивают единую базу контролей для тестовых и продуктивных ВМ.

## Тестовые окружения
- Docker Compose: `tests/docker` для быстрой генерации отчётов и телеметрии. При отсутствии Docker скрипты автоматически
  переключаются на оффлайн-симуляцию, подготавливают базу ФСТЭК через `prepare_fstec_content.py` и формируют примерные артефакты
  в `tests/docker/artifacts` (включая Markdown-панель hardening-метрик, экспорт дашборда Grafana и payload для KUMA). Учебный архив `scanoval.zip` собирается на лету утилитой `tests/tools/create_sample_fstec_archive.py`.
- Kubernetes (kind): `tests/k8s` для эмуляции стека в кластере. Скрипт `setup-kind.sh` создаёт кластер или запускает симуляцию
  логов и сводок, предварительно извлекая OVAL базу ФСТЭК (архив также формируется утилитой `tests/tools/create_sample_fstec_archive.py`), если бинарник `kind` недоступен.
- Виртуальные машины: `tests/vms` описывает Packer-шаблон для RedOS 7.3/8, Astra 1.7, Альт 8, CentOS 7 и содержит симуляцию, которая формирует `compliance-report.json`, телеметрию osquery→Grafana/KUMA и журналы сборки для test/prod контуров.

Скрипты `tests/docker/run.sh`, `tests/k8s/setup-kind.sh` и `tests/vms/run.sh` перед запуском симуляций выставляют `HARDENING_FIXED_TIMESTAMP=2025-10-21T00:00:00+00:00`, чтобы метки времени в артефактах оставались детерминированными и не засоряли git-статус; при необходимости переменную можно переопределить.

## Процесс DevOps и контроль изменений
- **Локальная разработка**: каждая задача оформляется предложенным диффом и набором локальных запусков (docker/kind/VM симуляторы); решение утверждает ревьюер по результатам тестов.
- **CI-проверки**: перед слиянием выполняются `python3 -m py_compile` для новых утилит, оффлайн-тесты `./tests/docker/run.sh all`, `./tests/k8s/setup-kind.sh`, `./tests/vms/run.sh` и агрегация `tests/tools/generate_process_report.py`.
- **Промежуточное хранение**: симуляторы воспроизводят синтетический и канареечный трафик, результаты сохраняются в `tests/**/artifacts` как доказательство готовности к прод-катастрофам.
- **Аудит**: подсказка, план и итоговый дифф сопровождаются отчётами каталога `reports/` (например, `2025-10-21-process-analytics.md`, `process-metrics-summary.json`).

## Измерение воздействия и метрик
- Базовые значения времени цикла, переделки обзора, MTTR и производительности определены в `tests/shared/process_baseline.json`.
- Каждый запуск симуляторов формирует `process-impact.json`/`process-impact.md` с фактами и дельтами; агрегатор `tests/tools/generate_process_report.py` собирает сведения по всем семействам.
- Консолидированный отчёт и JSON-сводка доступны соответственно в `reports/2025-10-21-process-analytics.md` и `reports/process-metrics-summary.json`.

## Отчёты пробных запусков
- Результаты текущей проверки оффлайн-симуляций: [reports/2025-10-21-simulation-results.md](reports/2025-10-21-simulation-results.md).
- Визуализация метрик osquery/Telegraf -> Grafana/KUMA: [reports/2025-10-21-monitoring-dashboard.md](reports/2025-10-21-monitoring-dashboard.md).
- Проверка артефактов VM и профилей `secaudit`: будет обновлена после запуска `tests/vms/run.sh` (см. каталог `reports/`).
- Сводный отчёт по процессным метрикам: [reports/2025-10-21-process-analytics.md](reports/2025-10-21-process-analytics.md) и агрегированный JSON `reports/process-metrics-summary.json`.
