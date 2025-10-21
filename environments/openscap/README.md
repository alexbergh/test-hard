# OpenSCAP Pilot окружение

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
