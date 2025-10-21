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

## База OVAL ФСТЭК (scanoval.zip)
- Источник: [https://bdu.fstec.ru/files/scanoval.zip](https://bdu.fstec.ru/files/scanoval.zip). В средах с фильтрацией HTTP(S) возможен ответ `403 Domain forbidden` — в этом случае скачайте архив вручную и укажите путь в переменной `fstec_oval_local_archive`.
- Для анализа и подготовки контента используйте скрипт `tools/prepare_fstec_content.py`:
  ```bash
  python tools/prepare_fstec_content.py \
    --archive ~/Downloads/scanoval.zip \
    --output ./content/fstec \
    --product "Red Hat" --product "Windows"
  ```
- Скрипт формирует `manifest.json` со сводкой определений и YAML `fstec_oval.yml`, который можно включить в `group_vars`.
- После извлечения Ansible-роль автоматически развёртывает архив, а таймер `run-openscap-scan` запускает дополнительные проверки `oscap oval eval` для каждого выбранного файла.

## Минимальные требования
- Контроллер: 4 vCPU / 8 GB RAM / 100 GB Storage.
- Контент-репозиторий: 2 vCPU / 4 GB RAM / 50 GB Storage.
- Доступ к официальным источникам SCAP и внутреннему репозиторию.
