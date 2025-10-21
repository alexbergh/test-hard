# Hardening сценарий: Linux

## Цели
- Соответствие ФСТЭК 17/21 и CIS Level 1/2.
- Подтверждение соответствия OpenSCAP и мониторинг изменений через Osquery/Wazuh.

## Инструменты
- Ansible плейбук: `ansible/playbooks/linux.yml` (роли `common_baseline`, `linux_cis`).
- Мониторинг: OpenSCAP таймеры из [OpenSCAP Pilot](../environments/openscap/README.md), осадки osquery/Telegraf, FIM Wazuh.

## Этап 1. Подготовка
1. Актуализировать переменные в `ansible/group_vars/linux.yml` (списки пользователей, sysctl, политика паролей).
2. Определить профиль OpenSCAP (например, `xccdf_org.ssgproject.content_profile_cis`).
3. Настроить baseline Wazuh FIM для `/etc`, `/usr/bin`, critical paths.
4. Развернуть osquery пакеты `inventory.conf`, `vulnerability-management.conf` для контроля состояния.

## Этап 2. Конфигурация системы (Ansible)
| Подсистема | Действия | Роль/задача |
|------------|----------|-------------|
| Учётные записи | Блокировка неавторизованных shell-пользователей, политика паролей | `common_baseline` |
| SSH | Отключение паролей, ограничение шифров/МАС | `common_baseline` |
| Аудит | Настройка `auditd` лимитов и правил на привилегированные команды | `common_baseline`, `linux_cis` |
| Системные параметры | Применение sysctl (tcp_syncookies, запрет redirect) | `linux_cis` |
| Привилегии | Логирование sudo, автоматический screen lock | `linux_cis` |

Запуск плейбука: `ansible-playbook -i ansible/inventory.ini ansible/playbooks/linux.yml`.

## Этап 3. Верификация
1. Выполнить OpenSCAP скан и сверить отчёты с требуемым профилем.
2. Проверить панели Grafana/KUMA по данным osquery (пакеты, открытые порты).
3. Просмотреть оповещения Wazuh (FIM, rootcheck) на предмет отклонений.

## Этап 4. Эксплуатация
- Планировать ежемесячные пересканы OpenSCAP.
- Поддерживать актуальность osquery pack (обновлять SQL-запросы).
- Использовать Wazuh для реагирования на изменения конфигурации (автоматические тикеты).
- Включить плейбук в CI/CD pipeline (molecule/ansible-lint).

## Метрики успеха
- % соответствия профилям (OpenSCAP) ≥ 95%.
- SLA на закрытие несоответствий высокого риска < 10 дней.
- Нулевая терпимость к несанкционированным изменениям (Wazuh FIM alerts).
