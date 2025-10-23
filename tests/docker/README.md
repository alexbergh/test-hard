# Docker test harness

`docker-compose.yml` агрегирует пилотные сервисы и упрощает запуск интеграционных тестов:

- `openscap-runner` выполняет локальный OVAL-скан и складывает результаты в `artifacts/openscap`.
- `influxdb`, `telegraf-listener`, `grafana` формируют телеметрический пайплайн для проверки пакетов osquery.
- `kuma-mock` эмулирует приёмник KUMA и сохраняет батчи телеметрии для последующего анализа.
- `osquery-simulator` периодически отправляет события на Telegraf по HTTP и UDP.
- `wazuh-*` поднимают менеджер, индексатор и дашборд Wazuh вместе с агентом, который регистрируется автоматически.
  В веб-интерфейс Wazuh входите под `admin / SecretPassword!`. Для сброса пароля используйте
  контейнерный скрипт: `docker exec -it wazuh-dashboard \
  /usr/share/wazuh-dashboard/node/bin/node /usr/share/wazuh-dashboard/wazuh-reset-password.js admin`.
  API менеджера по умолчанию слушает HTTPS на порту 55000 и конфигурируется через файл
  `config/wazuh-manager/api.yaml`, который должен использовать схему Wazuh 4.13: поле
  `host` — это список адресов (по умолчанию `['0.0.0.0', '::']`), `port` задаёт порт
  прослушивания, а блок `https` содержит абсолютные пути к сертификатам
  (`/var/ossec/api/configuration/ssl/server.crt` и
  `/var/ossec/api/configuration/ssl/server.key`). В репозитории
  лежит готовый self-signed сертификат в `config/wazuh-manager/ssl/server.crt`
  (закрытый ключ — `server.key`). При необходимости сгенерируйте новые файлы собственной CA
  и сохраните их в том же каталоге, чтобы compose-маунт автоматически подхватил их внутри
  контейнера. Чтобы перейти на HTTP, оставьте `host: ['0.0.0.0']` и выставьте
  `https.enabled: false`; маунт каталога `ssl/` можно убрать или заменить на собственные
  файлы по необходимости.

  При повреждённых томах Wazuh (ошибка `Installing /var/ossec/var/multigroups ... Exiting.`)
  удалите контейнер и связанные анонимные volumes: `docker compose rm -sfv wazuh-manager`
  и `docker volume prune`. После очистки запустите стек заново, начиная с `wazuh-indexer`.

Перед запуском убедитесь, что Docker Engine поддерживает Compose V2 (`docker compose`). Если Docker недоступен (например, в CI),
скрипт `run.sh` автоматически переключится на оффлайн-симуляцию, подготовит базу ФСТЭК через `prepare_fstec_content.py` и сгенерирует примерные отчёты в каталоге `artifacts/`. Учебный архив `scanoval.zip` формируется на лету утилитой `tests/tools/create_sample_fstec_archive.py`, поэтому бинарные файлы не хранятся в репозитории.

```bash
# поднять телеметрию и wazuh в фоне
./run.sh all

# однократный запуск OpenSCAP (контейнер или симуляция)
./run.sh openscap

# остановить и удалить контейнеры (актуально, когда Docker доступен)
docker compose -f docker-compose.yml --profile openscap --profile telemetry --profile wazuh down
```

> **Замена образа OpenSCAP.** При недоступности `quay.io` установите переменную перед запуском: `export OPENSCAP_IMAGE=deepsecurity/openscap-scan:latest`. Compose подставит её вместо значения по умолчанию (`quay.io/openscap/openscap:1.3.9`), поэтому можно использовать зеркала или локально загруженный образ (`OPENSCAP_IMAGE=myregistry.local/openscap:offline`). Не забудьте предварительно выполнить `docker pull`/`docker load`.

> **Версия образов Wazuh.** Тег по умолчанию — `4.7.1`, потому что для `4.7.2` отсутствует публикация агента в Docker Hub. Чтобы перейти на другую версию или частный реестр, экспортируйте переменные до запуска: `export WAZUH_VERSION=4.7.1` и, при необходимости, `export WAZUH_IMAGE_REGISTRY=registry.example.com/wazuh`. Эти значения применяются ко всем сервисам `wazuh-*` в файле Compose.

Артефакты сохраняются в `tests/docker/artifacts` (игнорируются git). В режиме симуляции формируются JSON/текстовые логи для всех профилей, а также готовые заготовки:

- `telemetry/hardening-dashboard.md` — Markdown-панель с визуализацией и ASCII-графиками по критичности.
- `telemetry/grafana-dashboard.json` — экспорт готового дашборда Grafana, использующего InfluxDB.
- `telemetry/kuma-payload.json` и `telemetry/collector.log` — батч и журнал условного коллектора для передачи в KUMA.

Эти артефакты формируются как при работе настоящих контейнеров, так и в режиме оффлайн-симуляции.
