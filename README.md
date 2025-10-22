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

## Запуск окружений через Docker Compose

Все docker-compose файлы совместимы с Compose V2 (`docker compose`). Убедитесь, что у вас установлены Docker Engine и плагин Compose, а также что выполняются команды из корня репозитория или соответствующего подкаталога.

### Osquery + Telegraf (центральный стек)

```bash
cd environments/osquery-telegraf/docker
docker compose up -d
```

Стек поднимает InfluxDB, приёмник Telegraf и Grafana с дефолтными учётными данными `admin/changeme`. Конфигурация слушателя находится в `telegraf/telegraf.conf` — при необходимости скорректируйте выходы перед запуском.

### Wazuh + Elastic Stack

```bash
cd environments/wazuh/docker
docker compose up -d
```

Будут запущены `wazuh-indexer`, `wazuh-manager` и `wazuh-dashboard`. Стандартные логины/пароли задаются переменными окружения в `docker-compose.yml`; при первом запуске измените значения `changeme`/`SecretPassword` и при необходимости подправьте `config/manager/ossec.conf`.

### Полный тестовый стенд (все профили)

Для запуска всех контейнеров проекта одним файлом используйте агрегированный Compose в `tests/docker`:

```bash
cd tests/docker
docker compose --profile openscap --profile telemetry --profile wazuh up -d
```

Профили включают OpenSCAP-runner, телеметрический стек (InfluxDB, Telegraf, Grafana, KUMA mock, osquery-simulator) и полный набор сервисов Wazuh. Артефакты и логи сохраняются в `tests/docker/artifacts`. Для остановки выполните:

```bash
docker compose --profile openscap --profile telemetry --profile wazuh down
```

> **Совет.** Если доступ к `quay.io` ограничен (ошибка TLS handshake), задайте альтернативный образ перед запуском:
> 
> ```bash
> export OPENSCAP_IMAGE=deepsecurity/openscap-scan:latest
> docker compose --profile openscap --profile telemetry --profile wazuh up -d
> ```
> 
> Compose подставит значение переменной вместо дефолтного `quay.io/openscap/openscap:1.3.9`. Можно указать собственный реестр или локальный образ (`OPENSCAP_IMAGE=localhost:5000/openscap:custom`) и предварительно выполнить `docker pull`/`docker load`.

> **Пинning версии Wazuh.** Образы `wazuh/wazuh-*` в агрегированном Compose по умолчанию используют тег `4.7.1`, потому что более новые сборки (например, `4.7.2`) не публиковались для агента. Если вам нужна другая версия или зеркало, задайте переменные перед запуском:
>
> ```bash
> export WAZUH_VERSION=4.7.1        # или 4.7.3, если все образы есть в реестре
> export WAZUH_IMAGE_REGISTRY=wazuh # по умолчанию, можно указать registry.example.com/wazuh
> docker compose --profile openscap --profile telemetry --profile wazuh up -d
> ```
>
> Значения распространяются на `wazuh-indexer`, `wazuh-manager`, `wazuh-dashboard` и `wazuh-agent`. При использовании частного реестра выполните `docker login` и `docker pull` заранее.

Если требуется одноразовый запуск сканера без фоновых сервисов, можно ограничиться профилем `openscap`. Скрипт `run.sh` в том же каталоге автоматически переключит систему в оффлайн-симуляцию, если Docker недоступен.

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

### Детерминированные таймстемпы симуляций

Для воспроизводимых артефактов оффлайн-скрипты (`tests/docker/run.sh`, `tests/k8s/setup-kind.sh`, `tests/vms/run.sh`) автоматически экспортируют переменную `HARDENING_FIXED_TIMESTAMP=2025-01-01T00:00:00+00:00`, если она не задана. Значение считывается всеми симуляторами через общий `TimeSequencer`, поэтому повторные запуски формируют идентичные поля `generated_at` и `collected_at`. При необходимости можно переопределить переменную перед запуском, чтобы получить собственный временной срез.

## Отчёты пробных запусков
- Результаты текущей проверки оффлайн-симуляций: [reports/2025-10-21-simulation-results.md](reports/2025-10-21-simulation-results.md).
- Визуализация метрик osquery/Telegraf -> Grafana/KUMA: [reports/2025-10-21-monitoring-dashboard.md](reports/2025-10-21-monitoring-dashboard.md).
- Проверка артефактов VM и профилей `secaudit`: будет обновлена после запуска `tests/vms/run.sh` (см. каталог `reports/`).
