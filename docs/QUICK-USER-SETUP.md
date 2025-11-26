# Быстрая настройка пользователей - Шпаргалка

> **Полное руководство**: [USER-SETUP.md](USER-SETUP.md)

## Быстрый старт

### Автоматическая настройка (рекомендуется)

```bash
# Сделать скрипт исполняемым
chmod +x scripts/setup-secure-user.sh

# Создать администратора
sudo ./scripts/setup-secure-user.sh admin

# Создать пользователя для сканирования
sudo ./scripts/setup-secure-user.sh scanner

# Создать сервисный аккаунт
sudo ./scripts/setup-secure-user.sh service

# Создать read-only пользователя
sudo ./scripts/setup-secure-user.sh readonly
```

## Типы пользователей

| Тип | Пользователь | Назначение | Sudo |
|-----|--------------|------------|------|
| **Admin** | `hardening-admin` | Управление платформой | Ограниченный |
| **Scanner** | `hardening-scanner` | Запуск сканирований | Минимальный |
| **Service** | `hardening-service` | Автоматизация (systemd) | Нет |
| **ReadOnly** | `hardening-readonly` | Просмотр отчетов | Нет |

## Принципы безопасности

### НИКОГДА НЕ ДЕЛАЙТЕ

```bash
# НЕ запускайте от root
sudo docker-compose up  # ПЛОХО

# НЕ добавляйте в docker group (кроме admin)
sudo usermod -aG docker hardening-scanner  # ОПАСНО!

# НЕ давайте полный sudo
hardening-scanner ALL=(ALL) ALL  # КРИТИЧЕСКАЯ УЯЗВИМОСТЬ!
```

### ВСЕГДА ДЕЛАЙТЕ

```bash
# Используйте выделенного пользователя
sudo -u hardening-admin docker-compose up  # ХОРОШО

# Используйте Docker Socket Proxy
DOCKER_HOST=unix:///var/run/docker-socket-proxy.sock  # БЕЗОПАСНО

# Ограничивайте sudo права
hardening-scanner ALL=(ALL) NOPASSWD: /usr/bin/lynis  # ПРАВИЛЬНО
```

## Сценарии использования

### Development (локальная разработка)

```bash
# 1. Создать администратора
sudo ./scripts/setup-secure-user.sh admin

# 2. Переключиться на администратора
sudo -iu hardening-admin

# 3. Запустить платформу
cd /opt/test-hard
make up
```

### Production (сканирование удаленных хостов)

```bash
# 1. На сервере мониторинга: создать scanner
sudo ./scripts/setup-secure-user.sh scanner

# 2. Скопировать SSH ключ на целевые хосты
ssh-copy-id -i /var/lib/hardening-scanner/.ssh/scanner_key.pub scanner-remote@target-host

# 3. На целевых хостах: создать read-only пользователя
ssh target-host
sudo useradd -m -s /bin/bash scanner-remote
sudo mkdir -p /home/scanner-remote/.ssh
sudo chmod 700 /home/scanner-remote/.ssh
# Настроить ограниченный sudo (см. USER-SETUP.md)

# 4. Запустить сканирование
sudo -u hardening-scanner /opt/test-hard/scripts/scan-remote-host.sh target-host
```

### Автоматизация (systemd timer)

```bash
# 1. Создать сервисный аккаунт
sudo ./scripts/setup-secure-user.sh service

# 2. Активировать таймер
sudo systemctl enable --now hardening-scanner.timer

# 3. Проверить статус
sudo systemctl status hardening-scanner.timer
sudo journalctl -u hardening-scanner.service -f
```

## Управление SSH ключами

### Генерация ключа

```bash
# Для scanner пользователя (уже создан автоматически)
sudo -u hardening-scanner cat /var/lib/hardening-scanner/.ssh/scanner_key.pub
```

### Копирование на целевые хосты

```bash
# Метод 1: ssh-copy-id (рекомендуется)
ssh-copy-id -i /var/lib/hardening-scanner/.ssh/scanner_key.pub scanner-remote@target-host

# Метод 2: вручную
cat /var/lib/hardening-scanner/.ssh/scanner_key.pub | \
  ssh scanner-remote@target-host 'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys'
```

### Ротация ключей (каждые 90 дней)

```bash
# Использовать скрипт ротации
sudo /opt/test-hard/scripts/rotate-ssh-keys.sh
```

## Настройка sudo прав

### Для scanner (минимальные права)

```bash
sudo visudo -f /etc/sudoers.d/hardening-scanner
```

```bash
# test-hard Scanner - только команды сканирования
Cmnd_Alias SCAN_COMMANDS = \
    /usr/bin/lynis audit system*, \
    /usr/bin/oscap xccdf eval*, \
    /usr/bin/docker exec */lynis*, \
    /usr/bin/docker exec */oscap*

hardening-scanner ALL=(ALL) NOPASSWD: SCAN_COMMANDS
Defaults:hardening-scanner !authenticate
```

### Для admin (ограниченные права)

```bash
sudo visudo -f /etc/sudoers.d/hardening-admin
```

```bash
# test-hard Admin - только Docker команды
hardening-admin ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/bin/docker-compose, /usr/bin/systemctl restart docker
```

## Права на файлы

### Критические директории

```bash
# Корневая директория
sudo chown hardening-admin:hardening-admin /opt/test-hard
sudo chmod 750 /opt/test-hard

# Конфигурации (чувствительные данные)
sudo chmod 700 /opt/test-hard/configs

# Отчеты (групповое чтение)
sudo chgrp -R hardening-reports /opt/test-hard/reports
sudo chmod 750 /opt/test-hard/reports

# .env файл (критически важно!)
chmod 600 ~/.env
```

### SSH директории

```bash
# Для scanner пользователя
sudo chmod 700 /var/lib/hardening-scanner/.ssh
sudo chmod 600 /var/lib/hardening-scanner/.ssh/scanner_key
sudo chmod 644 /var/lib/hardening-scanner/.ssh/scanner_key.pub
```

## Аудит и мониторинг

### Установка auditd

```bash
# Debian/Ubuntu
sudo apt-get install auditd audispd-plugins

# RHEL/CentOS
sudo dnf install audit
```

### Настройка правил

```bash
sudo tee -a /etc/audit/rules.d/hardening.rules << 'EOF'
# Мониторинг действий scanner
-a always,exit -F arch=b64 -S execve -F euid=hardening-scanner -k hardening_scanner

# Мониторинг доступа к отчетам
-w /opt/test-hard/reports/ -p rwa -k hardening_reports

# Мониторинг sudo
-a always,exit -F arch=b64 -S execve -F euid=0 -F auid>=1000 -k hardening_sudo
EOF

# Применить правила
sudo augenrules --load
sudo systemctl restart auditd
```

### Просмотр логов

```bash
# SSH подключения scanner
sudo ausearch -k hardening_scanner | tail -20

# Доступ к отчетам
sudo ausearch -k hardening_reports | tail -20

# Sudo команды
sudo ausearch -k hardening_sudo | tail -20
```

## Контрольный чек-лист

### Базовая безопасность

* [ ] Создан выделенный пользователь (не root)
* [ ] Пользователи НЕ в docker group (кроме admin)
* [ ] Настроены ограниченные sudo права
* [ ] SSH аутентификация по ключам
* [ ] Права на файлы: 700 (configs), 750 (dirs), 600 (.env)

### Удаленное сканирование

* [ ] SSH ключи скопированы на целевые хосты
* [ ] На целевых хостах созданы read-only пользователи
* [ ] Настроены ограниченные SSH команды (ForceCommand)
* [ ] Firewall правила разрешают SSH только с сервера мониторинга

### Аудит

* [ ] Установлен и настроен auditd
* [ ] Логируются SSH подключения
* [ ] Логируются sudo команды
* [ ] Настроены alerts на подозрительную активность

### Обслуживание

* [ ] Настроена ротация SSH ключей (90 дней)
* [ ] Пароли не дефолтные
* [ ] Backup критических конфигураций
* [ ] Документированы процедуры восстановления

## Troubleshooting

### Проблема: Permission denied

```bash
# Проверить права
ls -la /opt/test-hard
ls -la ~/.ssh

# Исправить права на SSH
chmod 700 ~/.ssh
chmod 600 ~/.ssh/*_key
chmod 644 ~/.ssh/*.pub
```

### Проблема: sudo не работает

```bash
# Проверить конфигурацию
sudo visudo -c

# Проверить файл sudoers
sudo cat /etc/sudoers.d/hardening-scanner

# Проверить права на файл
ls -l /etc/sudoers.d/hardening-scanner  # должно быть 440
```

### Проблема: Docker permission denied

```bash
# НЕ добавляйте в docker group!
# Используйте Docker Socket Proxy

# Проверить настройку
echo $DOCKER_HOST  # должно быть unix:///var/run/docker-socket-proxy.sock

# Или используйте sudo для ограниченных команд
sudo docker ps  # только если настроен sudoers
```

### Проблема: SSH ключ не работает

```bash
# Проверить права
ls -la ~/.ssh/scanner_key  # должно быть 600

# Проверить authorized_keys на целевом хосте
ssh target-host
cat ~/.ssh/authorized_keys

# Проверить SSH логи
sudo tail -f /var/log/auth.log  # Debian/Ubuntu
sudo tail -f /var/log/secure    # RHEL/CentOS
```

## Дополнительные ресурсы

- **[USER-SETUP.md](USER-SETUP.md)** - Полное руководство по настройке пользователей
- **[SECURITY.md](SECURITY.md)** - Политика безопасности
- **[REAL-HOSTS-SCANNING.md](REAL-HOSTS-SCANNING.md)** - Сканирование удаленных хостов

## Полезные команды

```bash
# Переключиться на пользователя
sudo -iu hardening-scanner

# Выполнить команду от имени пользователя
sudo -u hardening-scanner /path/to/script.sh

# Проверить членство в группах
id hardening-scanner

# Проверить sudo права
sudo -l -U hardening-scanner

# Посмотреть активные SSH сессии
who
w

# Посмотреть логи пользователя
sudo journalctl _UID=$(id -u hardening-scanner)
```

---

**Помните**: Безопасность начинается с правильной настройки пользователей!
