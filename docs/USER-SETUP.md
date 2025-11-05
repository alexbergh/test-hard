# Создание пользователей для test-hard: Руководство по безопасности

## Обзор

Данное руководство описывает безопасное создание и настройку пользователей для работы с платформой test-hard в различных сценариях развертывания. Следование принципу наименьших привилегий критически важно для безопасности.

---

## Принципы безопасности

### Основные принципы

1. Наименьшие привилегии — пользователи имеют только необходимые права
2. Разделение обязанностей — разные пользователи для разных задач
3. Изоляция — ограничение доступа к критическим ресурсам
4. Аудит — все действия логируются
5. Ротация учетных данных — регулярная смена паролей и ключей

### Типы пользователей

| Тип | Назначение | Уровень доступа |
|-----|------------|-----------------|
| `hardening-admin` | Администрирование платформы | Полный |
| `hardening-scanner` | Запуск сканирований | Ограниченный |
| `hardening-readonly` | Просмотр отчетов | Только чтение |
| `hardening-service` | Автоматизация (CI/CD) | Минимальный |

---

##  Сценарий 1: Локальное развертывание (Development)

### Создание пользователя-администратора

```bash
# Создать пользователя
sudo useradd -m -s /bin/bash -c "test-hard Administrator" hardening-admin

# Создать SSH директорию
sudo mkdir -p /home/hardening-admin/.ssh
sudo chmod 700 /home/hardening-admin/.ssh

# Добавить в группу Docker (для управления контейнерами)
sudo usermod -aG docker hardening-admin

# Создать директории проекта
sudo mkdir -p /opt/test-hard/{reports,logs,configs}
sudo chown -R hardening-admin:hardening-admin /opt/test-hard

# Установить права на директории
sudo chmod 750 /opt/test-hard
sudo chmod 700 /opt/test-hard/configs  # Конфиги содержат чувствительные данные
sudo chmod 755 /opt/test-hard/reports  # Отчеты могут читаться группой
```

### Настройка sudo доступа

```bash
# Создать файл sudoers
sudo visudo -f /etc/sudoers.d/hardening-admin

# Добавить ограниченные права (РЕКОМЕНДУЕТСЯ)
hardening-admin ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/bin/docker-compose, /usr/bin/systemctl restart docker
```

ВАЖНО: Не давайте полный `sudo` без ограничений!

### Генерация SSH ключей

```bash
# От имени администратора
sudo -u hardening-admin ssh-keygen -t ed25519 -C "hardening-admin@test-hard" -f /home/hardening-admin/.ssh/id_ed25519 -N ""

# Установить правильные права
sudo chmod 600 /home/hardening-admin/.ssh/id_ed25519
sudo chmod 644 /home/hardening-admin/.ssh/id_ed25519.pub

# Для автоматизации (без passphrase)
# ТОЛЬКО в изолированных окружениях!
```

### Настройка переменных окружения

```bash
# Создать .env файл
sudo -u hardening-admin cat > /home/hardening-admin/.env << 'EOF'
# test-hard Configuration
TEST_HARD_HOME=/opt/test-hard
REPORTS_DIR=/opt/test-hard/reports
DOCKER_HOST=unix:///var/run/docker.sock
GF_ADMIN_USER=admin
GF_ADMIN_PASSWORD=CHANGE_THIS_PASSWORD
EOF

# Защитить .env файл
sudo chmod 600 /home/hardening-admin/.env
sudo chown hardening-admin:hardening-admin /home/hardening-admin/.env
```

---

## Сценарий 2: Production развертывание

### Создание пользователя-сканера (минимальные права)

```bash
# Создать системного пользователя
sudo useradd -r -m -s /bin/bash -c "test-hard Scanner Service" hardening-scanner

# НЕ добавлять в sudo
# НЕ добавлять в docker group (используем Docker Socket Proxy)

# Создать рабочие директории
sudo mkdir -p /var/lib/hardening-scanner/{scripts,reports,cache}
sudo chown -R hardening-scanner:hardening-scanner /var/lib/hardening-scanner

# Установить строгие права
sudo chmod 750 /var/lib/hardening-scanner
sudo chmod 700 /var/lib/hardening-scanner/cache
```

### Ограниченный sudo для сканирования

```bash
# Создать файл sudoers для scanner
sudo visudo -f /etc/sudoers.d/hardening-scanner

# ТОЛЬКО необходимые команды сканирования
Cmnd_Alias SCAN_COMMANDS = \
    /usr/bin/lynis audit system, \
    /usr/bin/oscap xccdf eval, \
    /usr/sbin/oscap-ssh, \
    /usr/bin/docker exec */lynis*, \
    /usr/bin/docker exec */oscap*

# Разрешить без пароля
hardening-scanner ALL=(ALL) NOPASSWD: SCAN_COMMANDS

# Запретить остальное
Defaults:hardening-scanner !authenticate
```

### Генерация ключей для удаленного сканирования

```bash
# Генерация ключа для SSH сканирования
sudo -u hardening-scanner ssh-keygen -t ed25519 -C "scanner@test-hard" -f /var/lib/hardening-scanner/.ssh/scanner_key -N ""

# Установить права
sudo chmod 600 /var/lib/hardening-scanner/.ssh/scanner_key
sudo chmod 644 /var/lib/hardening-scanner/.ssh/scanner_key.pub

# Добавить известные хосты
sudo -u hardening-scanner touch /var/lib/hardening-scanner/.ssh/known_hosts
sudo chmod 644 /var/lib/hardening-scanner/.ssh/known_hosts
```

### Создание пользователя на целевых хостах

На **каждом хосте, который будет сканироваться**:

```bash
# Создать пользователя с минимальными правами
sudo useradd -m -s /bin/bash -c "Security Scanner (read-only)" scanner-remote

# Создать SSH директорию
sudo mkdir -p /home/scanner-remote/.ssh
sudo chmod 700 /home/scanner-remote/.ssh

# Скопировать публичный ключ с сервера мониторинга
# (выполнить на сервере мониторинга)
ssh-copy-id -i /var/lib/hardening-scanner/.ssh/scanner_key.pub scanner-remote@TARGET_HOST

# На целевом хосте: настроить sudo
sudo visudo -f /etc/sudoers.d/scanner-remote

# ТОЛЬКО команды для чтения системной информации
Cmnd_Alias READONLY_COMMANDS = \
    /usr/bin/lynis audit system --quick --quiet, \
    /usr/bin/oscap xccdf eval *, \
    /bin/cat /var/log/*, \
    /bin/ls -la /*, \
    /usr/bin/systemctl status *

scanner-remote ALL=(ALL) NOPASSWD: READONLY_COMMANDS

# Запретить интерактивную оболочку (опционально, для максимальной безопасности)
# Defaults:scanner-remote !requiretty
```

### Ограничение SSH доступа

На целевых хостах отредактируйте `/etc/ssh/sshd_config`:

```bash
# Ограничить scanner-remote пользователя
Match User scanner-remote
    AllowTcpForwarding no
    X11Forwarding no
    PermitTunnel no
    GatewayPorts no
    AllowAgentForwarding no
    PermitOpen none
    ForceCommand /usr/local/bin/scanner-shell.sh
```

Создайте скрипт `/usr/local/bin/scanner-shell.sh`:

```bash
#!/bin/bash
# Ограниченная оболочка для scanner пользователя

case "$SSH_ORIGINAL_COMMAND" in
    "sudo lynis audit system"*)
        exec $SSH_ORIGINAL_COMMAND
        ;;
    "sudo oscap"*)
        exec $SSH_ORIGINAL_COMMAND
        ;;
    *)
        echo "Command not allowed: $SSH_ORIGINAL_COMMAND" >&2
        exit 1
        ;;
esac
```

```bash
sudo chmod 755 /usr/local/bin/scanner-shell.sh
sudo chown root:root /usr/local/bin/scanner-shell.sh
```

Перезапустите SSH:

```bash
sudo systemctl restart sshd
```

---

## Сценарий 3: Сервисный аккаунт для автоматизации

### Создание сервисного пользователя

```bash
# Системный пользователь без домашней директории
sudo useradd -r -s /usr/sbin/nologin -c "test-hard Service Account" hardening-service

# Создать минимальную рабочую директорию
sudo mkdir -p /var/lib/hardening-service
sudo chown hardening-service:hardening-service /var/lib/hardening-service
sudo chmod 700 /var/lib/hardening-service
```

### Настройка systemd сервиса

```bash
# Создать systemd unit файл
sudo tee /etc/systemd/system/hardening-scanner.service << 'EOF'
[Unit]
Description=test-hard Security Scanner Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
User=hardening-service
Group=hardening-service
WorkingDirectory=/opt/test-hard
EnvironmentFile=/etc/test-hard/scanner.env
ExecStart=/opt/test-hard/scripts/run_all_checks.sh
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hardening-scanner

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/test-hard/reports /var/lib/hardening-service

# Resource limits
CPUQuota=50%
MemoryLimit=1G
TasksMax=100

[Install]
WantedBy=multi-user.target
EOF

# Создать timer для периодического запуска
sudo tee /etc/systemd/system/hardening-scanner.timer << 'EOF'
[Unit]
Description=test-hard Security Scanner Timer
Requires=hardening-scanner.service

[Timer]
OnCalendar=daily
OnCalendar=02:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Активировать
sudo systemctl daemon-reload
sudo systemctl enable hardening-scanner.timer
sudo systemctl start hardening-scanner.timer
```

### Переменные окружения для сервиса

```bash
# Создать конфигурационный файл
sudo mkdir -p /etc/test-hard
sudo tee /etc/test-hard/scanner.env << 'EOF'
# test-hard Scanner Configuration
TEST_HARD_HOME=/opt/test-hard
REPORTS_DIR=/opt/test-hard/reports
LOG_LEVEL=INFO
DOCKER_HOST=unix:///var/run/docker-socket-proxy.sock
# НЕ используем напрямую Docker socket!
EOF

sudo chmod 600 /etc/test-hard/scanner.env
sudo chown hardening-service:hardening-service /etc/test-hard/scanner.env
```

---

## Сценарий 4: Read-Only пользователь для просмотра

### Создание пользователя только для чтения

```bash
# Создать пользователя
sudo useradd -m -s /bin/bash -c "test-hard Read-Only User" hardening-readonly

# Создать SSH директорию
sudo mkdir -p /home/hardening-readonly/.ssh
sudo chmod 700 /home/hardening-readonly/.ssh

# Добавить в группу для чтения отчетов
sudo groupadd -f hardening-reports
sudo usermod -aG hardening-reports hardening-readonly

# Установить права на отчеты
sudo chgrp -R hardening-reports /opt/test-hard/reports
sudo chmod -R 750 /opt/test-hard/reports
sudo chmod -R 640 /opt/test-hard/reports/*
```

### Доступ к Grafana (read-only)

```bash
# Создать read-only пользователя в Grafana через API
curl -X POST http://admin:${GF_ADMIN_PASSWORD}@localhost:3000/api/admin/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hardening-readonly",
    "email": "readonly@test-hard.local",
    "login": "hardening-readonly",
    "password": "CHANGE_THIS_PASSWORD",
    "role": "Viewer"
  }'

# Или через docker exec
docker compose exec grafana grafana-cli admin create-user \
  --login hardening-readonly \
  --email readonly@test-hard.local \
  --password CHANGE_THIS_PASSWORD \
  --role Viewer
```

---

## Дополнительные меры безопасности

### 1. Аудит действий пользователей

```bash
# Установить auditd
sudo apt-get install auditd audispd-plugins  # Debian/Ubuntu
sudo dnf install audit                        # RHEL/CentOS

# Добавить правила аудита
sudo tee -a /etc/audit/rules.d/hardening.rules << 'EOF'
# Мониторинг действий hardening пользователей
-a always,exit -F arch=b64 -S execve -F euid=hardening-scanner -k hardening_scanner_exec
-a always,exit -F arch=b64 -S execve -F euid=hardening-service -k hardening_service_exec

# Мониторинг доступа к отчетам
-w /opt/test-hard/reports/ -p rwa -k hardening_reports_access

# Мониторинг изменений конфигурации
-w /opt/test-hard/configs/ -p wa -k hardening_config_changes
-w /etc/test-hard/ -p wa -k hardening_config_changes

# Мониторинг sudo использования
-a always,exit -F arch=b64 -S execve -F euid=0 -F auid>=1000 -k hardening_sudo
EOF

# Перезагрузить правила
sudo augenrules --load
sudo systemctl restart auditd

# Просмотр логов
sudo ausearch -k hardening_scanner_exec
sudo ausearch -k hardening_reports_access
```

### 2. Ротация SSH ключей

```bash
#!/bin/bash
# /opt/test-hard/scripts/rotate-ssh-keys.sh

set -euo pipefail

USER="hardening-scanner"
KEY_PATH="/var/lib/hardening-scanner/.ssh/scanner_key"
BACKUP_DIR="/var/lib/hardening-scanner/.ssh/backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "Rotating SSH keys for $USER..."

# Создать backup директорию
sudo -u "$USER" mkdir -p "$BACKUP_DIR"

# Backup старого ключа
sudo -u "$USER" cp "$KEY_PATH" "$BACKUP_DIR/scanner_key_${DATE}.bak"
sudo -u "$USER" cp "${KEY_PATH}.pub" "$BACKUP_DIR/scanner_key_${DATE}.pub.bak"

# Генерировать новый ключ
sudo -u "$USER" ssh-keygen -t ed25519 -C "scanner@test-hard-${DATE}" -f "$KEY_PATH" -N "" -q

# Установить права
sudo chmod 600 "$KEY_PATH"
sudo chmod 644 "${KEY_PATH}.pub"

echo "New SSH key generated: $KEY_PATH"
echo "Old key backed up to: $BACKUP_DIR/scanner_key_${DATE}.bak"
echo ""
echo "IMPORTANT: Update authorized_keys on all target hosts!"
echo "Public key:"
cat "${KEY_PATH}.pub"

# Удалить старые backup (старше 90 дней)
find "$BACKUP_DIR" -name "scanner_key_*.bak" -mtime +90 -delete
```

```bash
# Добавить в cron для ежеквартальной ротации
sudo tee /etc/cron.d/hardening-key-rotation << 'EOF'
# Ротация SSH ключей каждые 90 дней
0 0 1 */3 * root /opt/test-hard/scripts/rotate-ssh-keys.sh | tee -a /var/log/hardening-key-rotation.log
EOF
```

### 3. Мониторинг доступа

```bash
# Добавить в telegraf.conf
cat >> /opt/test-hard/telegraf/telegraf.conf << 'EOF'

# Мониторинг SSH подключений
[[inputs.logparser]]
  files = ["/var/log/auth.log", "/var/log/secure"]
  from_beginning = false
  
  [inputs.logparser.grok]
    patterns = ["%{SYSLOGTIMESTAMP:timestamp} %{SYSLOGHOST:hostname} sshd(?:\\[%{POSINT:pid}\\])?: %{DATA:event} %{DATA:method} for (invalid user )?%{DATA:username} from %{IPORHOST:src_ip} port %{NUMBER:src_port}"]
    measurement = "ssh_auth"
    
  [inputs.logparser.tags]
    service = "ssh"

# Мониторинг sudo использования
[[inputs.logparser]]
  files = ["/var/log/auth.log", "/var/log/secure"]
  from_beginning = false
  
  [inputs.logparser.grok]
    patterns = ["%{SYSLOGTIMESTAMP:timestamp} %{SYSLOGHOST:hostname} sudo(?:\\[%{POSINT:pid}\\])?:\\s+%{DATA:username} : TTY=%{DATA:tty} ; PWD=%{DATA:pwd} ; USER=%{DATA:effective_user} ; COMMAND=%{GREEDYDATA:command}"]
    measurement = "sudo_commands"
    
  [inputs.logparser.tags]
    service = "sudo"
EOF

# Перезапустить telegraf
docker compose restart telegraf
```

### 4. Настройка PAM для дополнительной безопасности

```bash
# Ограничить количество одновременных сессий
sudo tee -a /etc/security/limits.conf << 'EOF'
# test-hard users limits
hardening-scanner hard maxlogins 2
hardening-service hard maxlogins 1
hardening-readonly hard maxlogins 3
EOF

# Настроить faillock (защита от brute-force)
sudo tee /etc/pam.d/common-auth << 'EOF'
auth required pam_faillock.so preauth silent audit deny=5 unlock_time=900
auth [default=die] pam_faillock.so authfail audit deny=5 unlock_time=900
EOF
```

---

## Матрица разрешений

### Файлы и директории

| Путь | Владелец | Группа | Права | Назначение |
|------|----------|--------|-------|-----------|
| `/opt/test-hard` | hardening-admin | hardening-admin | 750 | Корневая директория |
| `/opt/test-hard/configs` | hardening-admin | hardening-admin | 700 | Конфигурационные файлы |
| `/opt/test-hard/reports` | hardening-admin | hardening-reports | 750 | Отчеты сканирований |
| `/opt/test-hard/scripts` | hardening-admin | hardening-admin | 750 | Скрипты |
| `/var/lib/hardening-scanner` | hardening-scanner | hardening-scanner | 750 | Рабочая директория сканера |
| `/var/lib/hardening-service` | hardening-service | hardening-service | 700 | Сервисная директория |
| `/etc/test-hard` | root | root | 755 | Системные конфигурации |

### Docker доступ

| Пользователь | Docker Group | Socket Proxy | Разрешенные команды |
|--------------|--------------|--------------|---------------------|
| hardening-admin | Да | Нет | Все |
| hardening-scanner | Нет | Да | docker exec (ограниченно) |
| hardening-service | Нет | Да | docker ps, docker exec |
| hardening-readonly | Нет | Нет | Нет |

### Sudo права

| Пользователь | Права sudo | Команды |
|--------------|------------|---------|
| hardening-admin | Ограниченные | docker, docker-compose, systemctl restart docker |
| hardening-scanner | Ограниченные | lynis, oscap, docker exec */lynis*, docker exec */oscap* |
| hardening-service | Нет | - |
| hardening-readonly | Нет | - |

---

## Контрольный чек-лист безопасности

### Базовая настройка
- [ ] Создан выделенный пользователь (не root)
- [ ] Установлены минимальные необходимые права
- [ ] Настроена SSH аутентификация по ключам
- [ ] Отключена аутентификация по паролю для сервисных аккаунтов
- [ ] Настроены правильные права на файлы и директории (700/750/755)
- [ ] Создан `.env` файл с правами 600

### Разграничение доступа
- [ ] Разделены пользователи для разных задач (admin/scanner/service/readonly)
- [ ] Настроены ограниченные sudo права (не используется `ALL=(ALL) ALL`)
- [ ] Пользователи НЕ добавлены в docker group (используется Socket Proxy)
- [ ] Настроен read-only доступ для просмотра отчетов
- [ ] Ограничен SSH доступ (ForceCommand, ограничение команд)

### Аудит и мониторинг
- [ ] Включен auditd для мониторинга действий
- [ ] Настроены правила аудита для критических операций
- [ ] Логируются SSH подключения
- [ ] Логируются sudo команды
- [ ] Настроены alerts на подозрительную активность

### Ротация и обслуживание
- [ ] Настроена периодическая ротация SSH ключей (каждые 90 дней)
- [ ] Старые ключи удаляются после ротации
- [ ] Пароли в `.env` не дефолтные и достаточно сложные
- [ ] Настроен backup критических конфигураций

### Production
- [ ] НЕ используются дефолтные пароли (особенно Grafana admin/admin)
- [ ] Включен TLS для всех внешних соединений
- [ ] Настроены firewall правила
- [ ] Ограничен сетевой доступ к сервисам
- [ ] Настроены resource limits для systemd сервисов
- [ ] Применены security hardening опции (NoNewPrivileges, ProtectSystem, etc.)

---

## Миграция существующих установок

Если платформа уже развернута с небезопасными настройками:

```bash
#!/bin/bash
# /opt/test-hard/scripts/migrate-to-secure-users.sh

set -euo pipefail

echo "Migrating test-hard to secure user setup..."

# 1. Создать новых пользователей
sudo useradd -m -s /bin/bash -c "test-hard Scanner" hardening-scanner
sudo useradd -m -s /bin/bash -c "test-hard ReadOnly" hardening-readonly

# 2. Переместить файлы
sudo mkdir -p /var/lib/hardening-scanner
sudo cp -r /opt/test-hard/* /var/lib/hardening-scanner/
sudo chown -R hardening-scanner:hardening-scanner /var/lib/hardening-scanner

# 3. Создать symlink для обратной совместимости
sudo ln -sf /var/lib/hardening-scanner /opt/test-hard-scanner

# 4. Обновить systemd сервисы
sudo sed -i 's/User=root/User=hardening-scanner/' /etc/systemd/system/hardening-scanner.service
sudo systemctl daemon-reload

# 5. Применить правильные права
sudo chmod 750 /var/lib/hardening-scanner
sudo chmod 700 /var/lib/hardening-scanner/.ssh
sudo chmod 600 /var/lib/hardening-scanner/.ssh/*_key

echo "Migration complete!"
echo "Please review and test before production use!"
```

---

##  Дополнительные ресурсы

### Документация
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [SSH Security Best Practices](https://www.ssh.com/academy/ssh/security)
- [Linux Security Hardening](https://www.cisecurity.org/benchmark/distribution_independent_linux)
- [Principle of Least Privilege](https://en.wikipedia.org/wiki/Principle_of_least_privilege)

### Связанные документы
- [SECURITY.md](SECURITY.md) - Общая политика безопасности
- [REAL-HOSTS-SCANNING.md](REAL-HOSTS-SCANNING.md) - Сканирование удаленных хостов
- [DEPLOYMENT.md](DEPLOYMENT.md) - Развертывание платформы

### Инструменты проверки
```bash
# Проверить права на файлы
find /opt/test-hard -type f -perm /o+w -ls

# Проверить sudo конфигурацию
sudo visudo -c

# Проверить SSH конфигурацию
sshd -T | grep -i permit

# Проверить auditd правила
sudo auditctl -l
```

---

## FAQ

**Q: Можно ли использовать root пользователя?**  
A: **НЕТ!** Это критическая уязвимость безопасности. Всегда используйте выделенных пользователей с ограниченными правами.

**Q: Нужно ли добавлять scanner пользователя в docker group?**  
A: **НЕТ!** Используйте Docker Socket Proxy для ограничения доступа к Docker API. Прямой доступ к docker socket эквивалентен root доступу.

**Q: Как часто ротировать SSH ключи?**  
A: Рекомендуется каждые 90 дней для production окружений, каждые 180 дней для dev/staging.

**Q: Можно ли использовать пароли вместо SSH ключей?**  
A: Для автоматизации - **НЕТ**. Для интерактивного доступа - возможно, но SSH ключи более безопасны.

**Q: Нужен ли аудит в dev окружении?**  
A: Желательно для отладки и выявления проблем, но можно отключить для экономии ресурсов.

---

**Версия документа:** 1.0  
**Последнее обновление:** Ноябрь 2025  
**Автор:** test-hard Security Team
