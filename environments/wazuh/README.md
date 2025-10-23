# Wazuh + Elastic Stack окружение

Пилотная HIDS/FIM-платформа для непрерывного контроля целостности и реагирования.

## Компоненты
- **Wazuh Manager** — управление агентами, корреляция правил и активные ответы.
- **Wazuh Indexer** — хранилище событий (OpenSearch/Elastic-совместимый).
- **Wazuh Dashboard** — визуализация, алертинг и расследования.
- **Wazuh Agents** — агенты на Linux/Windows/macOS с FIM, rootcheck и интеграцией с osquery.

## Быстрый старт (Docker Compose)
Каталог `docker/` содержит `docker-compose.yml`, поднимающий indexer, manager и dashboard с базовой конфигурацией.
Стек закреплён на Wazuh 4.13.1 (manager/indexer/dashboard) с включённой безопасностью OpenSearch и HTTPS API.
Пароли передаются через переменные `WAZUH_INDEXER_PASSWORD` и `WAZUH_API_PASSWORD`
(можно задать в `.env` перед запуском или использовать значения по умолчанию из compose).
```bash
cd docker
docker compose up -d
```
Файл `config/manager/ossec.conf` демонстрирует включение FIM, интеграцию с osquery и активный ответ.

## Автоматизация агентов
Ansible-плейбук `ansible/playbook.yml` выполняет:
1. Подключение официального репозитория Wazuh.
2. Установку `wazuh-agent`.
3. Генерацию `ossec.conf` по переменным (`group_vars/wazuh_agents.yml`).
4. Регистрацию агента на менеджере (`agent-auth`).

Запуск:
```bash
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml
```

## Интеграция
- Потоки событий можно реплицировать в KUMA/Elastic через Filebeat или syslog.
- Osquery результаты доступны как `wodle osquery` и коррелируются с hardening-профилями.
- Активные ответы (пример `fim_repair`) позволяют автоматически реагировать на критичные изменения.

## Эксплуатация
- Контроль статуса агентов, ротация ключей регистрации.
- Бэкап индексов и настроек (snapshot API) не реже раза в сутки.
- Регулярное обновление правил (`wazuh-control` → `update`) и проверка совместимости с OpenSCAP/osquery сценариями.
