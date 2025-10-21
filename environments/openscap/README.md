# OpenSCAP Pilot окружение

Пилотная зона для формального hardening-аудита (ФСТЭК 17/21, CIS) с экспортом результатов в Kaspersky KEA/KSC.

## Компоненты
- **SCAP Content Repository** — Git/HTTP(S)-узел с утверждёнными OVAL/XCCDF профилями.
- **OpenSCAP Scanner Nodes** — Linux/Windows-хосты, на которых выполняются сканы.
- **Automation Controller** — Ansible/AWX для оркестрации сканирований.
- **KEA/KSC Bridge** — процедура импорта ARF/OVAL отчётов в Kaspersky Endpoint Security.

## Автоматизация
В директории `ansible/` размещён плейбук, который:
1. Устанавливает `openscap-scanner` и `scap-security-guide`.
2. Синхронизирует утверждённые профили из центрального репозитория.
3. Разворачивает скрипт `run-openscap-scan` и systemd timer для периодического запуска.

Запуск плейбука:
```bash
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml
```

Переменные по умолчанию можно скорректировать в `ansible/group_vars/scanners.yml` (список профилей, расписание, каталог отчётов).

## Поток процесса
1. **Подготовка контента** — синхронизация профилей ФСТЭК/CIS с `scap_datastream_repo_url`.
2. **Сканирование** — systemd timer запускает `oscap xccdf eval` для каждого профиля.
3. **Отчётность** — ARF/XML отчёты попадают в `{{ scap_scan_output_dir }}` и передаются в KEA/KSC или SOC-портал.
4. **Ремедиация** — несоответствия обрабатываются плейбуками из раздела [hardening-scenarios](../../hardening-scenarios/README.md).

## Интеграция с KEA/KSC
- Отчёты в формате ARF импортируются через KEA Security Controls Importer.
- Профили OVAL синхронизируются в KSC для централизованного контроля соответствия.
- По webhook/REST API можно уведомлять SOC о критичных отклонениях.

## Минимальные требования
- Контроллер: 4 vCPU / 8 GB RAM / 100 GB Storage.
- Контент-репозиторий: 2 vCPU / 4 GB RAM / 50 GB Storage.
- Доступ к официальным источникам SCAP и внутреннему репозиторию.
=======
## Цель
Обеспечить формальный hardening-аудит для Linux/Windows систем в соответствии с ФСТЭК 17/21 и CIS Benchmarks, с возможностью загрузки OVAL-профилей в Kaspersky KEA/KSC.

## Архитектура
- **OpenSCAP Scanner Nodes** — агенты на целевых системах (RHEL/CentOS/Oracle, Debian/Ubuntu, Windows через SCAP Workbench).
- **SCAP Content Repository** — хранилище OVAL/XCCDF профилей (официальные профили ФСТЭК, CIS). Разворачивается на Git/HTTP(S) сервере.
- **Automation Controller** — Ansible AWX/Automation Platform или аналог для запуска сканирований, генерации отчётов, доставки результатов.
- **KEA/KSC Integration** — импорт OVAL-профилей и результатов в Kaspersky Endpoint Agent или Security Center для централизованной отчётности.

## Минимальные требования
- Виртуальная машина для контроллера (4 vCPU, 8 GB RAM, 100 GB storage).
- Central Repository (2 vCPU, 4 GB RAM, 50 GB storage).
- Доступ к официальным SCAP-источникам.
- Для Windows: SCAP Workbench 1.2+, адаптация профилей.

## Шаги развертывания
1. **Подготовка репозитория контента**
   - Развернуть Git-сервер (Gitea/GitLab) или Nginx/Apache с синхронизацией контента из https://static.open-scap.org, https://www.cisecurity.org/.
   - Добавить в репозиторий утверждённые профили ФСТЭК 17/21.

2. **Настройка OpenSCAP на целевых системах**
   - Установить `openscap-scanner`, `scap-security-guide` (Linux).
   - Для Windows — установить SCAP Workbench, подготовить PowerShell-обёртку для запуска сканирования.
   - Создать cron/systemd timers для запуска сканирований согласно графику (еженедельно/ежемесячно).

3. **Автоматизация запусков**
   - Настроить Ansible роли: `ansible-galaxy collection install redhat.rhel_system_roles` для применения профилей.
   - Шаблон playbook:
     ```yaml
     - hosts: hardened
       become: true
       vars:
         scap_profile: xccdf_org.ssgproject.content_profile_cis
       roles:
         - role: redhat.rhel_system_roles.rhel1
       tasks:
         - name: Run OpenSCAP scan
           command: >
             oscap xccdf eval --profile {{ scap_profile }}
             --results /var/tmp/`hostname`-results.xml
             --report /var/tmp/`hostname`-report.html
             {{ scap_datastream }}
     ```

4. **Интеграция с Kaspersky KEA/KSC**
   - Экспортировать результаты в форматах ARF/XML.
   - Использовать KEA Security Controls Importer для загрузки OVAL-профилей.
   - Настроить синхронизацию по расписанию (через API KSC или пакетный импорт).

5. **Отчётность и контроль**
   - Публиковать отчёты в Wiki/SharePoint.
   - Создать контрольные дашборды (количество несоответствий, критичность, динамика исправлений).

## Мониторинг и оповещения
- Использовать `oscap-docker` для контейнеров.
- Настроить webhook в KEA/KSC для уведомлений SOC.
- Хранить исторические отчёты минимум 1 год.

## Интеграция с hardening-сценариями
- Результаты сканирования формируют входные данные для сценариев устранения несоответствий в разделе [hardening-scenarios](../../hardening-scenarios/README.md).
