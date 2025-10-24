# Индекс конфигураций

Этот документ агрегирует расположение конфигурационных файлов и каталогов в репозитории и кратко описывает, что в них настроено. Используйте его как путеводитель перед изменением параметров инфраструктурных окружений и тестовых стендов.

## Базовые артефакты

| Путь | Назначение | Основные параметры |
| --- | --- | --- |
| `config/wazuh-indexer/opensearch.yml` | Опорный конфиг OpenSearch для сборки Wazuh Indexer. | Название кластера `wazuh-indexer`, имя узла `node-1`, HTTP-интерфейс на `0.0.0.0:9200` и включённый TLS с путями до self-signed сертификатов в `/etc/wazuh-indexer/certs`. |
| `config/wazuh-indexer/certs/` | Набор демо-сертификатов для indexer'а. | В каталоге лежат ключи/сертификаты CA (`root-ca.*`), админа (`admin.*`), узла (`node-1.*`) и агрегированный `wazuh-indexer.pem/key` — используются при локальном деплое и в тестовом Compose. |
| `config/wazuh-indexer/security.policy` | Политика Java Security Manager для indexer'а. | Даёт OpenSearch права на чтение сертификатов в `/etc/wazuh-indexer/certs`, работу с конфигами в `/usr/share`, запись служебных данных и логов (`/var/lib`, `/var/log`), временные файлы в `/tmp`, сетевые соединения и изменение системных свойств. |

## Docker-окружения

| Путь | Назначение | Основные параметры |
| --- | --- | --- |
| `environments/osquery-telegraf/docker/telegraf/telegraf.conf` | Конфигурация Telegraf для профиля osquery+telemetry. | Слушает HTTP вебхук на `:9081/osquery`, syslog по UDP `6514`, отправляет метрики в InfluxDB `http://influxdb:8086` в организацию `security` и бакет `osquery`. |
| `environments/wazuh/docker/config/indexer/opensearch.yml` | Конфиг indexer'а в Wazuh-стеке. | Single-node OpenSearch (`discovery.type: single-node`), расширенные портовые диапазоны `9200-9299/9300-9399`, TLS включён, DN для admin/node заданы через `plugins.security.*`. |
| `environments/wazuh/docker/config/manager/ossec.conf` | Пользовательская конфигурация Wazuh Manager. | Включает JSON-логирование, secure remote (TCP/1515), дополнительные ruleset-файлы (`0310-win-base`, `0500-osquery`, `0530-auditd`), и active-response `fim_repair`. |
| `environments/wazuh/docker/config/dashboard/opensearch_dashboards.yml` | Конфиг Wazuh Dashboard (OpenSearch Dashboards). | HTTPS на `0.0.0.0:5601`, обязательная проверка CA, дефолтный маршрут `/app/wz-home`, подключение к indexer'у `https://wazuh-indexer:9200`. |
| `environments/wazuh/docker/.env` | Шаблон переменных окружения Wazuh-стека. | Содержит placeholder-пароли `WAZUH_INDEXER_PASSWORD` и `WAZUH_API_PASSWORD`, которые нужно заменить перед продуктивным запуском. |

## Тестовый Docker-стенд

| Путь | Назначение | Основные параметры |
| --- | --- | --- |
| `tests/docker/config/wazuh-indexer/opensearch.yml` | Конфиг indexer'а в агрегированном тестовом Compose. | Single-node кластер с TLS, использует тестовые certs (`admin.pem`/`node-1.pem`), перечислены `admin_dn` и `nodes_dn`, включён режим совместимости `compatibility.override_main_response_version`. |
| `tests/docker/config/wazuh-manager/api.yaml` | HTTP API настройки менеджера в тестовом стенде. | Слушает IPv4/IPv6 на `55000`, включает HTTPS с self-signed `server.crt/server.key` без проверки CA. |
| `tests/docker/config/wazuh-dashboard/opensearch_dashboards.yml` | Dashboard для тестового стенда. | Включён TLS, указаны пути до тестовых сертификатов, верификация по сертификату, дефолтный маршрут `/app/wz-home`. |
| `tests/docker/config/telegraf/telegraf.conf` | Telegraf-конфиг в тестовом стенде. | Минимальный агент: вывод в InfluxDB `http://influxdb:8086` с токеном `adminadmin`, собирает метрики CPU/Mem/Net. |

> Если требуется полный контекст по сервисам и зависимости, см. `environments/*/README.md` и `tests/docker/docker-compose.yml` — они показывают, как эти конфиги монтируются в контейнеры.
