# Сценарии hardening по мотивам secaudit-core

Каталог `hardening-scenarios/secaudit` содержит профильные наборы контролей для
каждой из виртуальных машин, требуемых заказчиком. Структура JSON совместима с
концепцией проекта [secaudit-core](https://github.com/alexbergh/secaudit-core):
каждый контроль содержит идентификатор, ссылку на модуль/паттерн `secaudit`
(`secaudit_reference`), описание проверки и рекомендации по ремедиации.

## Формат профиля

```json
{
  "metadata": {
    "id": "redos-7.3",
    "name": "РедОС 7.3 базовый профиль",
    "source": "alexbergh/secaudit-core",
    "version": "2025.10"
  },
  "environments": {
    "test": {"goal": "Подтверждение развёртывания"},
    "prod": {"goal": "Поддержание соответствия"}
  },
  "controls": [
    {
      "id": "REDOS73-CTRL-001",
      "title": "Отключить root вход по SSH",
      "severity": "high",
      "tags": ["ssh", "access"],
      "secaudit_reference": "linux.ssh.disable_root_login",
      "check": "grep -i PermitRootLogin /etc/ssh/sshd_config",
      "remediation": "Настроить PermitRootLogin no",
      "category": "access_control"
    }
  ]
}
```

Поля `check` и `remediation` используются в отчётах и артефактах симуляции, а
идентификатор `secaudit_reference` помогает сопоставить контроль с исходными
ролями из `secaudit-core`.

## Использование

- Профили подключаются к Ansible-роле `secaudit_profiles`, которая учитывает
  `secaudit_profile_id` и `target_environment`.
- Симулятор `tests/vms/simulate.py` считывает JSON-файлы и формирует
  `compliance-report.json` для каждой ВМ, а также метрики для Grafana/KUMA.
- При появлении новых версий `secaudit-core` достаточно обновить описание
  профиля и задействованные контролы — тестовые стенды автоматически подхватят
  изменения при следующем запуске симуляции.

