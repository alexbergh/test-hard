# Проверка виртуальных стендов hardening

Дата проверки: 21 октября 2025 года

## Тестовый контур
- Сводка результатов: `tests/vms/artifacts/test/simulation-summary.json` (комплаенс 60–80% в зависимости от профиля).
- Отчёты по системам:
  - RedOS 7.3 — `tests/vms/artifacts/test/redos-7.3/compliance-report.json` (нужно доработать политику паролей и PermitRootLogin).
  - RedOS 8 — `tests/vms/artifacts/test/redos-8/compliance-report.json` (не хватает удалённого auditd).
  - Astra Linux 1.7 — `tests/vms/artifacts/test/astralinux-1.7/compliance-report.json` (отсутствует правило auditd на `/etc/shadow`).
  - Альт 8 — `tests/vms/artifacts/test/altlinux-8/compliance-report.json` (требуется включить AIDE и ротацию auditd).
  - CentOS 7 — `tests/vms/artifacts/test/centos-7/compliance-report.json` (не выполнен контроль pam_pwquality).
- Метрики и визуализация: `tests/vms/artifacts/test/telemetry/hardening-dashboard.md`, `.../grafana-dashboard.json`, `.../kuma-payload.json` подтверждают интеграцию с osquery/KUMA.

## Продовой контур
- Сводка результатов: `tests/vms/artifacts/prod/simulation-summary.json` (комплаенс 80–100%).
- Отчёты по системам:
  - RedOS 7.3 — `tests/vms/artifacts/prod/redos-7.3/compliance-report.json` (требуется завершить настройку политики паролей).
  - RedOS 8 — `tests/vms/artifacts/prod/redos-8/compliance-report.json` (auditd offload не активирован).
  - Astra Linux 1.7 — `tests/vms/artifacts/prod/astralinux-1.7/compliance-report.json` (все контроли выполнены).
  - Альт 8 — `tests/vms/artifacts/prod/altlinux-8/compliance-report.json` (ожидает включения AIDE таймера).
  - CentOS 7 — `tests/vms/artifacts/prod/centos-7/compliance-report.json` (все контроли выполнены).
- Агрегированные метрики: `tests/vms/artifacts/prod/telemetry/hardening-dashboard.md`, `.../metrics.json`, `.../collector.log` демонстрируют готовность визуализации.

## Выводы
- Packer-шаблон и Ansible-плейбук покрывают все заявленные дистрибутивы; профили `secaudit` позволяют настроить различия между тестовым и продуктивным контурами.
- Симуляция предоставляет полную доказательную базу (планы сборки, отчёты, телеметрию), которая дополняет docker/kind стенды и может использоваться в отчётности Head DevOps департамента.
- Для повышения комплаенса в продуктиве необходимо закрыть отдельные контроли (auditd offload для RedOS 8, AIDE для Альт 8); задачи добавлены в backlog.
