#!/bin/bash
# setup-secure-user.sh - Безопасная настройка пользователей для test-hard
# Использование: sudo ./scripts/setup-secure-user.sh [admin|scanner|service|readonly]

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции вывода
info() { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# Проверка root
if [[ $EUID -ne 0 ]]; then
   error "Этот скрипт должен быть запущен с правами root (sudo)"
fi

# Получить тип пользователя
USER_TYPE="${1:-}"
INSTALL_DIR="${2:-/opt/test-hard}"

show_usage() {
    cat << EOF
Использование: sudo $0 <тип_пользователя> [директория]

Типы пользователей:
  admin     - Администратор платформы (ограниченный sudo)
  scanner   - Пользователь для сканирований (минимальные права)
  service   - Сервисный аккаунт для systemd (без sudo)
  readonly  - Только просмотр отчетов (read-only)

Параметры:
  директория - Директория установки (по умолчанию: /opt/test-hard)

Примеры:
  sudo $0 admin
  sudo $0 scanner /var/lib/hardening
  sudo $0 service

Документация: docs/USER-SETUP.md
EOF
    exit 0
}

# Показать справку
if [[ -z "$USER_TYPE" ]] || [[ "$USER_TYPE" == "-h" ]] || [[ "$USER_TYPE" == "--help" ]]; then
    show_usage
fi

# Валидация типа пользователя
case "$USER_TYPE" in
    admin|scanner|service|readonly)
        ;;
    *)
        error "Неизвестный тип пользователя: $USER_TYPE. Используйте: admin, scanner, service или readonly"
        ;;
esac

USERNAME="hardening-${USER_TYPE}"

info "Настройка пользователя: $USERNAME"
info "Директория установки: $INSTALL_DIR"
echo ""

# Проверка существования пользователя
if id "$USERNAME" &>/dev/null; then
    warning "Пользователь $USERNAME уже существует"
    read -p "Пересоздать пользователя? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "Удаление существующего пользователя..."
        userdel -r "$USERNAME" 2>/dev/null || true
    else
        error "Прервано пользователем"
    fi
fi

# Создание пользователя в зависимости от типа
case "$USER_TYPE" in
    admin)
        info "Создание администратора с полными правами..."
        useradd -m -s /bin/bash -c "test-hard Administrator" "$USERNAME"
        
        # Добавить в docker group
        usermod -aG docker "$USERNAME"
        
        # Создать директории
        mkdir -p "$INSTALL_DIR"/{reports,logs,configs,scripts}
        chown -R "$USERNAME:$USERNAME" "$INSTALL_DIR"
        chmod 750 "$INSTALL_DIR"
        chmod 700 "$INSTALL_DIR/configs"
        
        # Настроить sudo
        info "Настройка ограниченного sudo доступа..."
        cat > "/etc/sudoers.d/$USERNAME" << 'EOF'
# test-hard Administrator - ограниченные права
hardening-admin ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/bin/docker-compose, /usr/local/bin/docker-compose, /usr/bin/systemctl restart docker, /usr/bin/systemctl stop docker, /usr/bin/systemctl start docker
Defaults:hardening-admin !requiretty
EOF
        chmod 440 "/etc/sudoers.d/$USERNAME"
        
        # Проверить sudoers
        visudo -c || error "Ошибка в конфигурации sudoers!"
        
        success "Администратор создан успешно"
        ;;
        
    scanner)
        info "Создание пользователя для сканирования..."
        useradd -r -m -s /bin/bash -c "test-hard Scanner Service" "$USERNAME"
        
        # НЕ добавляем в docker group!
        
        # Создать рабочие директории
        SCANNER_DIR="/var/lib/$USERNAME"
        mkdir -p "$SCANNER_DIR"/{scripts,reports,cache,.ssh}
        chown -R "$USERNAME:$USERNAME" "$SCANNER_DIR"
        chmod 750 "$SCANNER_DIR"
        chmod 700 "$SCANNER_DIR/.ssh"
        chmod 700 "$SCANNER_DIR/cache"
        
        # Настроить ограниченный sudo
        info "Настройка минимального sudo доступа..."
        cat > "/etc/sudoers.d/$USERNAME" << 'EOF'
# test-hard Scanner - только команды сканирования
Cmnd_Alias SCAN_COMMANDS = \
    /usr/bin/lynis audit system*, \
    /usr/bin/oscap xccdf eval*, \
    /usr/sbin/oscap-ssh*, \
    /usr/bin/docker exec */lynis*, \
    /usr/bin/docker exec */oscap*

hardening-scanner ALL=(ALL) NOPASSWD: SCAN_COMMANDS
Defaults:hardening-scanner !authenticate
Defaults:hardening-scanner !requiretty
EOF
        chmod 440 "/etc/sudoers.d/$USERNAME"
        
        # Проверить sudoers
        visudo -c || error "Ошибка в конфигурации sudoers!"
        
        # Генерировать SSH ключ
        info "Генерация SSH ключа для удаленного сканирования..."
        sudo -u "$USERNAME" ssh-keygen -t ed25519 -C "scanner@test-hard" \
            -f "$SCANNER_DIR/.ssh/scanner_key" -N "" -q
        chmod 600 "$SCANNER_DIR/.ssh/scanner_key"
        chmod 644 "$SCANNER_DIR/.ssh/scanner_key.pub"
        
        success "Пользователь для сканирования создан успешно"
        echo ""
        info "Публичный SSH ключ для копирования на целевые хосты:"
        cat "$SCANNER_DIR/.ssh/scanner_key.pub"
        ;;
        
    service)
        info "Создание системного сервисного аккаунта..."
        useradd -r -s /usr/sbin/nologin -c "test-hard Service Account" "$USERNAME"
        
        # Создать минимальную рабочую директорию
        SERVICE_DIR="/var/lib/$USERNAME"
        mkdir -p "$SERVICE_DIR"
        chown "$USERNAME:$USERNAME" "$SERVICE_DIR"
        chmod 700 "$SERVICE_DIR"
        
        # Создать конфигурационный файл
        info "Создание конфигурации для systemd сервиса..."
        mkdir -p /etc/test-hard
        cat > /etc/test-hard/scanner.env << EOF
# test-hard Service Configuration
TEST_HARD_HOME=$INSTALL_DIR
REPORTS_DIR=$INSTALL_DIR/reports
LOG_LEVEL=INFO
DOCKER_HOST=unix:///var/run/docker-socket-proxy.sock
EOF
        chmod 600 /etc/test-hard/scanner.env
        chown "$USERNAME:$USERNAME" /etc/test-hard/scanner.env
        
        # Создать systemd unit
        cat > /etc/systemd/system/hardening-scanner.service << EOF
[Unit]
Description=test-hard Security Scanner Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
User=$USERNAME
Group=$USERNAME
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=/etc/test-hard/scanner.env
ExecStart=$INSTALL_DIR/scripts/run_all_checks.sh
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hardening-scanner

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR/reports $SERVICE_DIR

# Resource limits
CPUQuota=50%
MemoryLimit=1G
TasksMax=100

[Install]
WantedBy=multi-user.target
EOF

        # Создать timer
        cat > /etc/systemd/system/hardening-scanner.timer << 'EOF'
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

        systemctl daemon-reload
        
        success "Сервисный аккаунт создан успешно"
        info "Для активации таймера выполните: systemctl enable --now hardening-scanner.timer"
        ;;
        
    readonly)
        info "Создание пользователя только для чтения..."
        useradd -m -s /bin/bash -c "test-hard Read-Only User" "$USERNAME"
        
        # Создать группу для чтения отчетов
        groupadd -f hardening-reports
        usermod -aG hardening-reports "$USERNAME"
        
        # Установить права на отчеты
        if [[ -d "$INSTALL_DIR/reports" ]]; then
            chgrp -R hardening-reports "$INSTALL_DIR/reports"
            chmod -R 750 "$INSTALL_DIR/reports"
            find "$INSTALL_DIR/reports" -type f -exec chmod 640 {} \;
        fi
        
        success "Пользователь для чтения создан успешно"
        info "Для доступа к Grafana создайте Viewer пользователя в веб-интерфейсе"
        ;;
esac

# Создать базовую структуру SSH
if [[ "$USER_TYPE" != "service" ]]; then
    SSH_DIR="/home/$USERNAME/.ssh"
    if [[ ! -d "$SSH_DIR" ]]; then
        mkdir -p "$SSH_DIR"
        chown "$USERNAME:$USERNAME" "$SSH_DIR"
        chmod 700 "$SSH_DIR"
    fi
fi

# Создать .env файл для admin
if [[ "$USER_TYPE" == "admin" ]]; then
    info "Создание .env файла..."
    RANDOM_PASSWORD=$(openssl rand -base64 32)
    cat > "/home/$USERNAME/.env" << EOF
# test-hard Configuration
TEST_HARD_HOME=$INSTALL_DIR
REPORTS_DIR=$INSTALL_DIR/reports
DOCKER_HOST=unix:///var/run/docker.sock

# Grafana credentials (CHANGE THIS!)
GF_ADMIN_USER=admin
GF_ADMIN_PASSWORD=$RANDOM_PASSWORD
EOF
    chown "$USERNAME:$USERNAME" "/home/$USERNAME/.env"
    chmod 600 "/home/$USERNAME/.env"
    
    warning "Установлен случайный пароль для Grafana: $RANDOM_PASSWORD"
    warning "Сохраните пароль в безопасном месте и измените его при первом входе!"
fi

echo ""
success "=========================================="
success "Пользователь $USERNAME настроен успешно!"
success "=========================================="
echo ""

# Вывести инструкции
case "$USER_TYPE" in
    admin)
        info "Следующие шаги:"
        echo "1. Переключитесь на пользователя: sudo -iu $USERNAME"
        echo "2. Клонируйте репозиторий в $INSTALL_DIR"
        echo "3. Настройте .env файл: nano ~/.env"
        echo "4. Запустите платформу: cd $INSTALL_DIR && make up"
        ;;
    scanner)
        info "Следующие шаги:"
        echo "1. Скопируйте публичный ключ на целевые хосты:"
        echo "   ssh-copy-id -i /var/lib/$USERNAME/.ssh/scanner_key.pub user@target-host"
        echo "2. Настройте inventory файл (см. docs/REAL-HOSTS-SCANNING.md)"
        echo "3. Запустите сканирование: sudo -u $USERNAME $INSTALL_DIR/scripts/scan-remote-host.sh"
        ;;
    service)
        info "Следующие шаги:"
        echo "1. Проверьте конфигурацию: cat /etc/test-hard/scanner.env"
        echo "2. Активируйте таймер: systemctl enable --now hardening-scanner.timer"
        echo "3. Проверьте статус: systemctl status hardening-scanner.timer"
        echo "4. Просмотр логов: journalctl -u hardening-scanner.service -f"
        ;;
    readonly)
        info "Следующие шаги:"
        echo "1. Создайте Grafana пользователя с ролью Viewer"
        echo "2. Пользователь может читать отчеты в $INSTALL_DIR/reports"
        ;;
esac

echo ""
info "Полная документация: docs/USER-SETUP.md"

# Напоминание о безопасности
echo ""
warning "=========================================="
warning "НАПОМИНАНИЕ О БЕЗОПАСНОСТИ"
warning "=========================================="
echo "НЕ добавляйте пользователей в docker group (кроме admin)"
echo "НЕ используйте полный sudo доступ ALL=(ALL) ALL"
echo "Используйте SSH ключи вместо паролей"
echo "Настройте auditd для мониторинга действий"
echo "Ротируйте SSH ключи каждые 90 дней"
echo ""
