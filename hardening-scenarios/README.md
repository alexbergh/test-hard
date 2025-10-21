# Сценарии hardening ОС

## Подход
1. **Классификация активов** — разделить системы по критичности (уровни ФСТЭК, сегменты безопасности).
2. **Выбор бенчмарка** — ФСТЭК 17/21, CIS Level 1/2, внутренние политики.
3. **Назначение окружения мониторинга**:
   - Формальный аудит и отчётность — [OpenSCAP](../environments/openscap/README.md).
   - Оперативный мониторинг и инвентарь — [Osquery + Telegraf](../environments/osquery-telegraf/README.md).
   - Непрерывный контроль целостности — [Wazuh](../environments/wazuh/README.md).
4. **Автоматизация внедрения** — использовать плейбуки в `ansible/playbooks/` данного каталога и профили `secaudit`.
5. **Верификация** — сравнение результатов разных инструментов, закрытие несоответствий.

## Репозиторий автоматизации
- Linux-плейбук: `ansible/playbooks/linux.yml` (роли `common_baseline`, `linux_cis`, `secaudit_profiles`).
- Windows-плейбук: `ansible/playbooks/windows.yml` (роль `windows_baseline`).
- Профильные контролы для RedOS/Astra/Alt/CentOS: `secaudit/profiles/*.json`.
- Общие переменные: `ansible/group_vars/`.
- Пример инвентаря: `ansible/inventory.ini` (с тестовыми/продовыми ВМ).

## Общие шаги hardening
- Обновление и управление патчами.
- Минимизация сервисов, удаление неиспользуемых пакетов.
- Настройка журналирования и централизованного сбора логов.
- Усиление аутентификации (MFA, длина паролей, блокировки).
- Настройка сетевых фильтров, сегментация.
- Контроль целостности и реагирование на отклонения.

## Профильные сценарии
| ОС | Профиль | Особенности |
|----|---------|-------------|
| RedOS 7.3 | `secaudit_profiles` + `redos-7.3.json` | Политика паролей 60/1/14, auditd→syslog, osquery pack |
| RedOS 8 | `secaudit_profiles` + `redos-8.json` | fapolicyd, баннеры, удалённый auditd |
| Astra Linux 1.7 | `secaudit_profiles` + `astralinux-1.7.json` | unattended-upgrades, pam_tally2, auditd на shadow |
| Альт 8 | `secaudit_profiles` + `altlinux-8.json` | iptables DROP, aide timer, строгие права shadow |
| CentOS 7 | `secaudit_profiles` + `centos-7.json` | yum-cron, audit=1, sudo logging |

## Потоки данных
| Сценарий | Источник | Инструмент | Назначение |
|----------|----------|------------|------------|
| Формальный аудит | SCAP контент | OpenSCAP | Отчёт в KEA/KSC |
| Инвентарь | osquery packs | Telegraf -> KUMA/Grafana | SOC дашборды |
| Контроль целостности | Wazuh FIM | Wazuh Dashboard/Elastic | Реагирование |
| Валидация профилей `secaudit` | VM симуляции | `tests/vms/simulate.py` | Отчёты `compliance-report.json`, панели Grafana/KUMA |

## Процесс управления несоответствиями
1. Найдено несоответствие (OpenSCAP/Wazuh/osquery/VM-симуляция).
2. Создать тикет с приоритетом на основе критичности.
3. Выполнить ремедиацию плейбуками [Linux](linux.md) или [Windows](windows.md).
4. Провести повторную проверку и обновить отчётность.

