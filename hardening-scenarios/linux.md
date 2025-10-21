# Hardening сценарий: Linux

## Цели
- Соответствие ФСТЭК 17/21 и CIS Level 1/2.
- Подтверждение соответствия OpenSCAP и мониторинг изменений через Osquery/Wazuh.
- Валидация профилей `secaudit-core` на стендах RedOS, Astra, Альт, CentOS.

## Инструменты
- Ansible плейбук: `ansible/playbooks/linux.yml` (роли `common_baseline`, `linux_cis`, `secaudit_profiles`).
- Мониторинг: OpenSCAP таймеры из [OpenSCAP Pilot](../environments/openscap/README.md), осадки osquery/Telegraf, FIM Wazuh.
- Тестовые ВМ: шаблоны Packer и симуляция `tests/vms` (RedOS 7.3/8, Astra 1.7, Альт 8, CentOS 7).

## Профили secaudit
| Профиль | Контур | Ключевые меры |
|---------|--------|----------------|
| `redos-7.3` | test/prod | PermitRootLogin=no, auditd→syslog, политика паролей 60/1/14, osquery pack |
| `redos-8` | test/prod | Banner, fapolicyd, auditd offload, осмотр баннеров, активный osqueryd |
| `astralinux-1.7` | test/prod | Правила auditd для `/etc/shadow`, unattended-upgrades, pam_tally2 |
| `altlinux-8` | test/prod | SSH ciphers, iptables DROP by default, aide timer, аудит логов |
| `centos-7` | test/prod | yum-cron, отключение telnet/rsh, audit=1, sudo logging, pwquality |

Профили описаны в `hardening-scenarios/secaudit/profiles/*.json` и подключаются к роли
`secaudit_profiles`, которая автоматически подбирает задачи в зависимости от
переменных `secaudit_profile_id` и `target_environment`.

## Этап 1. Подготовка
1. Актуализировать переменные в `ansible/group_vars/linux.yml` (списки пользователей, sysctl, политика паролей, `target_environment`).
2. Обновить описания профилей при выходе новых версий `secaudit-core`.
3. Настроить baseline Wazuh FIM для `/etc`, `/usr/bin`, critical paths.
4. Развернуть osquery пакеты `inventory.conf`, `vulnerability-management.conf` для контроля состояния.

## Этап 2. Конфигурация системы (Ansible)
| Подсистема | Действия | Роль/задача |
|------------|----------|-------------|
| Учётные записи | Блокировка неавторизованных shell-пользователей, политика паролей | `common_baseline`, `secaudit_profiles` |
| SSH | Отключение паролей, ограничение шифров/МАС, баннеры | `common_baseline`, `secaudit_profiles` |
| Аудит | Настройка `auditd` лимитов и правил на привилегированные команды, offload | `common_baseline`, `linux_cis`, `secaudit_profiles` |
| Системные параметры | Применение sysctl (tcp_syncookies, запрет redirect) | `linux_cis` |
| Привилегии | Логирование sudo, автоматический screen lock | `linux_cis`, `secaudit_profiles` |

Запуск плейбука: `ansible-playbook -i ansible/inventory.ini ansible/playbooks/linux.yml`.

## Этап 3. Верификация
1. Выполнить OpenSCAP скан и сверить отчёты с требуемым профилем.
2. Проверить панели Grafana/KUMA по данным osquery (пакеты, открытые порты).
3. Просмотреть оповещения Wazuh (FIM, rootcheck) на предмет отклонений.
4. Оценить `compliance-report.json` в `tests/vms/artifacts/<env>/<os>/` и агрегированную
   панель `telemetry/hardening-dashboard.md`.

## Этап 4. Эксплуатация
- Планировать ежемесячные пересканы OpenSCAP.
- Поддерживать актуальность osquery pack (обновлять SQL-запросы).
- Использовать Wazuh для реагирования на изменения конфигурации (автоматические тикеты).
- Включить плейбук в CI/CD pipeline (molecule/ansible-lint).

## Метрики успеха
- % соответствия профилям (OpenSCAP) ≥ 95%.
- SLA на закрытие несоответствий высокого риска < 10 дней.
- Нулевая терпимость к несанкционированным изменениям (Wazuh FIM alerts).
- Средний compliance для prod-хостов из симуляции `tests/vms` ≥ 90%.
