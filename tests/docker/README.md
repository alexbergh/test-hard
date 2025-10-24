# Docker test harness

`docker-compose.yml` агрегирует пилотные сервисы и упрощает запуск интеграционных тестов:

- `openscap-runner` выполняет локальный OVAL-скан и складывает результаты в `artifacts/openscap`.
- `influxdb`, `telegraf-listener`, `grafana` формируют телеметрический пайплайн для проверки пакетов osquery.
- `kuma-mock` эмулирует приёмник KUMA и сохраняет батчи телеметрии для последующего анализа.
- `osquery-simulator` периодически отправляет события на Telegraf по HTTP и UDP.
- `wazuh-*` поднимают менеджер, индексатор и дашборд Wazuh вместе с агентом, который
  регистрируется автоматически. Все сервисы читают пароли из `.env` в корне каталога
  (`WAZUH_INDEXER_PASSWORD` для OpenSearch и `WAZUH_API_PASSWORD` для API менеджера).
  По умолчанию используются значения из репозитория, но перед продуктивным запуском
  замените их на уникальные. Дашборд слушает HTTPS на `https://localhost:443` и требует
  пару `admin/<WAZUH_API_PASSWORD>` из `.env`. При необходимости пароль можно сменить
  через встроенный скрипт: `docker exec -it wazuh-dashboard \
  /usr/share/wazuh-dashboard/node/bin/node \
  /usr/share/wazuh-dashboard/wazuh-reset-password.js admin`.
  API менеджера по умолчанию слушает HTTPS на порту 55000 и конфигурируется через файл
  `config/wazuh-manager/api.yaml`, который должен использовать схему Wazuh 4.13: раздел
  `hosts` — это список адресов (по умолчанию `0.0.0.0` и `::` на порту 55000), а блок
  `https` содержит пути к self-signed сертификатам (`ssl/server.crt` и `ssl/server.key`).
  Файлы уже лежат в репозитории; при замене сертификатов достаточно перезаписать содержимое
  каталога `config/wazuh-manager/ssl/`.

> **Секреты Wazuh.** OpenSearch запускается с включённым security-плагином и проверкой TLS.
> Файл `config/wazuh-indexer/opensearch.yml` оставляет стандартные пути сертификатов
> (`/usr/share/wazuh-indexer/certs/*.pem`) и включает DN для администратора и узла,
> совпадающие с теми, что прописаны в дефолтных сертификатах образа. Менеджер и
> дашборд подключаются к индексеру по HTTPS с логином `admin` и паролем из `.env`.
> Если требуется доверять собственному центру сертификации, замените стандартные сертификаты
> внутри контейнеров (см. официальную инструкцию Wazuh по `wazuh-cert-tool`).

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

> **Версия образов Wazuh.** Compose закреплён на релизе `4.13.1` для indexer/manager/dashboard/agent, что соответствует текущей LTS-ветке Wazuh. Для использования другого тега отредактируйте соответствующие поля `image:` или передайте переменные окружения при запуске (`WAZUH_VERSION`, `WAZUH_IMAGE_REGISTRY`).

Артефакты сохраняются в `tests/docker/artifacts` (игнорируются git). В режиме симуляции формируются JSON/текстовые логи для всех профилей, а также готовые заготовки:

- `telemetry/hardening-dashboard.md` — Markdown-панель с визуализацией и ASCII-графиками по критичности.
- `telemetry/grafana-dashboard.json` — экспорт готового дашборда Grafana, использующего InfluxDB.
- `telemetry/kuma-payload.json` и `telemetry/collector.log` — батч и журнал условного коллектора для передачи в KUMA.

Эти артефакты формируются как при работе настоящих контейнеров, так и в режиме оффлайн-симуляции.
