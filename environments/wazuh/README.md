# Wazuh + Elastic Stack окружение

Пилотная HIDS/FIM-платформа для непрерывного контроля целостности и реагирования.

## Компоненты
- **Wazuh Manager** — управление агентами, корреляция правил и активные ответы.
- **Wazuh Indexer** — хранилище событий (OpenSearch/Elastic-совместимый).
- **Wazuh Dashboard** — визуализация, алертинг и расследования.
- **Wazuh Agents** — агенты на Linux/Windows/macOS с FIM, rootcheck и интеграцией с osquery.

## Быстрый старт (Docker Compose)
Каталог `docker/` содержит `docker-compose.yml`, поднимающий indexer, manager и dashboard с базовой конфигурацией.
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

## Цель
Обеспечить HIDS/FIM-функциональность, корреляцию событий и реагирование, дополняющее hardening контроль.

## Архитектура
- **Wazuh Manager** — управление агентами, корреляция правил.
- **Wazuh Indexer (OpenSearch/Elastic)** — хранение событий и индексов FIM.
- **Wazuh Dashboard (Kibana/OpenSearch Dashboards)** — визуализация и алертинг.
- **Filebeat/Logstash** — буферизация, отправка событий в SIEM (опционально).
- **Agents** — Linux, Windows, macOS; включают FIM, rootcheck, Syscheck.

## Ресурсы
- Manager: 4 vCPU, 8 GB RAM, 100 GB storage.
- Indexer cluster: минимум 3 ноды (по 4 vCPU, 16 GB RAM) для HA.
- Dashboard: 2 vCPU, 4 GB RAM.

## Развертывание
1. **Установка Wazuh**
   - Использовать официальный `wazuh-install.sh` для all-in-one пилота или ansible-роли (`wazuh/wazuh-ansible`).
   - При промышленном внедрении — разделение на dedicated manager + indexer cluster.

2. **Настройка FIM**
   - В `ossec.conf` определить директории для контроля:
     ```xml
     <syscheck>
       <directories realtime="yes" check_all="yes">/etc</directories>
       <directories realtime="yes" check_all="yes">/usr/bin</directories>
       <directories realtime="yes">C:\\Windows\\System32</directories>
     </syscheck>
     ```
   - Включить подписывание файлов (символьные хеши SHA256).

3. **Корреляционные правила**
   - Импортировать правила CIS/FSTEC.
   - Создать пользовательские правила для контроля несоответствий hardening (несоответствие sysctl, отключённый аудит).

4. **Интеграция с Elastic/KUMA**
   - Отправка событий через Filebeat в Elastic/KUMA для централизованного анализа.
   - Использовать `wazuh-module` для KUMA, если доступен, или через стандартный Syslog/CEF.

5. **Оповещения**
   - Настроить webhook/Slack/Teams для критичных алертов.
   - Интеграция с SOAR (Shuffle, TheHive) для автоматизации реакций.

6. **Эксплуатация**
   - Ежедневный контроль состояния агентов.
   - Настройка резервного копирования индексов и конфигураций.

## Безопасность
- Использовать TLS взаимную аутентификацию между агентами и менеджером.
- Сегментировать сеть (менеджер в зоне безопасности).
- Регулярно обновлять Wazuh/Elastic.

## Интеграция с hardening-сценариями
- Wazuh FIM и rootcheck проверяют соблюдение мер из сценариев hardening.
- Отчётность из Wazuh дополняет OpenSCAP и osquery результаты.