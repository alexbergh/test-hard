# Hardening сценарий: Windows

## Цели
- Соответствие ФСТЭК 17/21 и CIS Microsoft Windows Benchmarks.
- Централизованный контроль через SCAP Workbench/OpenSCAP, osquery и Wazuh.

## Инструменты
- Ansible плейбук: `ansible/playbooks/windows.yml` (роль `windows_baseline`).
- Мониторинг: SCAP отчёты, osquery события (через Telegraf/KUMA) и Wazuh FIM/Sysmon.

## Этап 1. Подготовка
1. Настроить переменные в `ansible/group_vars/windows.yml` (политика паролей, аудит, firewall).
2. Получить CIS Level 1/2 GPO templates и согласовать с безопасностью.
3. Развернуть osquery MSI, включить расширения `win_event_log`, `powershell_events`.
4. Подключить Wazuh агента с политиками Sysmon и директориями FIM `C:\Windows`, `C:\Program Files`.

## Этап 2. Применение политик (Ansible)
| Область | Действия | Задача |
|---------|----------|--------|
| Пароли | Минимальная длина, срок жизни, история | `win_password_policy` |
| Блокировки | Ограничение неудачных входов | `win_security_policy` |
| Firewall | Включение профилей, запрет inbound по умолчанию | `win_firewall_profile` |
| Аудит | Настройка подкатегорий Logon/Policy Change | `win_audit_policy_system` |
| PowerShell | Включение transcription, module/script-block logging | `win_regedit` |
| SMB | Удаление SMBv1 | `win_feature` |

Запуск плейбука: `ansible-playbook -i ansible/inventory.ini ansible/playbooks/windows.yml`.

## Этап 3. Верификация
1. Выполнить SCAP скан (SCAP Workbench → Ansible/AWX) и экспортировать отчёт.
2. Проверить osquery дашборды: статус обновлений, risky logon events.
3. Проанализировать Wazuh оповещения (FIM, Sysmon) и корреляции.

## Этап 4. Эксплуатация
- Еженедельные проверки соответствия через SCAP/KEA.
=======
- Соответствие ФСТЭК 17/21, CIS Microsoft Windows Benchmarks.
- Централизованный контроль через OpenSCAP (SCAP Workbench), osquery, Wazuh.

## Этап 1. Подготовка
1. Получить CIS Level 1/2 GPO templates, согласовать с безопасностью.
2. Сформировать SCAP профиль (OVAL + XCCDF) для Windows Server/Desktop.
3. Развернуть osquery MSI, включить расширения (winlog, powershell_events).
4. Настроить Wazuh агента с политиками Sysmon, FIM для `C:\Windows`, `C:\Program Files`.

## Этап 2. Применение политик
| Область | Действия | Инструменты |
|---------|----------|-------------|
| GPO | Импорт security baseline шаблонов, запрет LM/NTLM v1, конфигурация audit policy | Group Policy, OpenSCAP отчёт |
| Обновления | Включить WSUS/SCCM, контролировать patch level | osquery таблица `patches`, Wazuh vulnerability detector |
| Журналы | Настроить Event Forwarding в KUMA/SIEM | Windows Event Forwarding + Telegraf/Wazuh |
| Контроль приложений | AppLocker/Windows Defender Application Control | GPO, Wazuh alerts |
| RDP/Сеть | Включить NLA, ограничить RDP по VPN, firewall rules | OpenSCAP, osquery `listening_ports` |

## Этап 3. Верификация
1. Выполнить SCAP скан (SCAP Workbench -> Ansible upload) и экспортировать отчёт.
2. Проверить osquery дашборды: статус обновлений, risky logon events.
3. Анализ Wazuh оповещений по FIM и Sysmon.

## Этап 4. Эксплуатация
- Еженедельные проверки соответствия через SCAP.
- Автоматизация ремедиации через PowerShell DSC/Ansible (WinRM).
- Использование Wazuh для расследования подозрительных событий (подключение SOAR).
- Хранение отчётов и GPO версий для аудита.

## Метрики успеха
- Отсутствие критичных несоответствий CIS Level 1.
- Все системы с последними накопительными обновлениями (< 14 дней).
- Время реакции на критичные события Wazuh < 30 минут.
