# Hardening сценарий: Linux

## Цели
- Соответствие ФСТЭК 17/21 и CIS Level 1/2.
- Обеспечение контроля соответствия через OpenSCAP, мониторинг изменений через Osquery/Wazuh.

## Этап 1. Подготовка
1. Определить профиль OpenSCAP (например, `xccdf_org.ssgproject.content_profile_cis`).
2. Импортировать профиль в Ansible/AWX для автоматизированного применения.
3. Настроить baseline-снимок Wazuh FIM для `/etc`, `/usr/bin`, critical paths.
4. Создать osquery pack `linux_cis.conf` с ключевыми проверками (auditd, sshd, passwd).

## Этап 2. Конфигурация системы
| Подсистема | Действия | Инструменты |
|------------|----------|-------------|
| Пакеты | Удалить ненужные пакеты, включить автообновления (`dnf-automatic`, `unattended-upgrades`) | Ansible roles, OpenSCAP remediation |
| Аутентификация | Настроить `pam_pwquality`, `faillock`, включить MFA (SAML/RADIUS) | Ansible, osquery проверки `user_ssh_keys` |
| Журналирование | Настроить `rsyslog`/`journald` удалённый вывод в KUMA | Ansible, Telegraf syslog input |
| Сеть | Включить firewalld/ufw профили, ограничить SSH | OpenSCAP rules, Wazuh rootcheck |
| Контроль доступа | SELinux/AppArmor enforcing, sudo по принципу наим. привилегий | OpenSCAP, Wazuh policy monitoring |

## Этап 3. Верификация
1. Запустить OpenSCAP скан и получить отчёт.
2. Осмотреть метрики из osquery (dashboards KUMA/Grafana) для подтверждения изменений.
3. Проверить Wazuh алерты: отсутствие критичных изменений после применения.

## Этап 4. Эксплуатация
- Планировать ежемесячные пересканы OpenSCAP.
- Поддерживать актуальность osquery pack (обновлять SQL-запросы).
- Использовать Wazuh для реагирования на изменения конфигурации (автоматические тикеты).
- Реализовать CI/CD pipeline: изменения playbook проходят тестирование в staging перед prod.

## Метрики успеха
- % соответствия профилям (OpenSCAP) >= 95%.
- SLA на закрытие несоответствий высокого риска < 10 дней.
- Нулевая терпимость к несанкционированным изменениям (Wazuh FIM alerts).
