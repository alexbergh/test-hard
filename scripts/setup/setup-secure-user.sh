#!/bin/bash
# setup-secure-user.sh - Р‘РµР·РѕРїР°СЃРЅР°СЏ РЅР°СЃС‚СЂРѕР№РєР° РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№ РґР»СЏ test-hard
# РСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ: sudo ./scripts/setup-secure-user.sh [admin|scanner|service|readonly]

set -euo pipefail

# Р¦РІРµС‚Р° РґР»СЏ РІС‹РІРѕРґР°
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Р¤СѓРЅРєС†РёРё РІС‹РІРѕРґР°
info() { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# РџСЂРѕРІРµСЂРєР° root
if [[ $EUID -ne 0 ]]; then
   error "Р­С‚РѕС‚ СЃРєСЂРёРїС‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ Р·Р°РїСѓС‰РµРЅ СЃ РїСЂР°РІР°РјРё root (sudo)"
fi

# РџРѕР»СѓС‡РёС‚СЊ С‚РёРї РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ
USER_TYPE="${1:-}"
INSTALL_DIR="${2:-/opt/test-hard}"

show_usage() {
    cat << EOF
РСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ: sudo $0 <С‚РёРї_РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ> [РґРёСЂРµРєС‚РѕСЂРёСЏ]

РўРёРїС‹ РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№:
  admin     - РђРґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂ РїР»Р°С‚С„РѕСЂРјС‹ (РѕРіСЂР°РЅРёС‡РµРЅРЅС‹Р№ sudo)
  scanner   - РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РґР»СЏ СЃРєР°РЅРёСЂРѕРІР°РЅРёР№ (РјРёРЅРёРјР°Р»СЊРЅС‹Рµ РїСЂР°РІР°)
  service   - РЎРµСЂРІРёСЃРЅС‹Р№ Р°РєРєР°СѓРЅС‚ РґР»СЏ systemd (Р±РµР· sudo)
  readonly  - РўРѕР»СЊРєРѕ РїСЂРѕСЃРјРѕС‚СЂ РѕС‚С‡РµС‚РѕРІ (read-only)

РџР°СЂР°РјРµС‚СЂС‹:
  РґРёСЂРµРєС‚РѕСЂРёСЏ - Р”РёСЂРµРєС‚РѕСЂРёСЏ СѓСЃС‚Р°РЅРѕРІРєРё (РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ: /opt/test-hard)

РџСЂРёРјРµСЂС‹:
  sudo $0 admin
  sudo $0 scanner /var/lib/hardening
  sudo $0 service

Р”РѕРєСѓРјРµРЅС‚Р°С†РёСЏ: docs/USER-SETUP.md
EOF
    exit 0
}

# РџРѕРєР°Р·Р°С‚СЊ СЃРїСЂР°РІРєСѓ
if [[ -z "$USER_TYPE" ]] || [[ "$USER_TYPE" == "-h" ]] || [[ "$USER_TYPE" == "--help" ]]; then
    show_usage
fi

# Р’Р°Р»РёРґР°С†РёСЏ С‚РёРїР° РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ
case "$USER_TYPE" in
    admin|scanner|service|readonly)
        ;;
    *)
        error "РќРµРёР·РІРµСЃС‚РЅС‹Р№ С‚РёРї РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ: $USER_TYPE. РСЃРїРѕР»СЊР·СѓР№С‚Рµ: admin, scanner, service РёР»Рё readonly"
        ;;
esac

USERNAME="hardening-${USER_TYPE}"

info "РќР°СЃС‚СЂРѕР№РєР° РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ: $USERNAME"
info "Р”РёСЂРµРєС‚РѕСЂРёСЏ СѓСЃС‚Р°РЅРѕРІРєРё: $INSTALL_DIR"
echo ""

# РџСЂРѕРІРµСЂРєР° СЃСѓС‰РµСЃС‚РІРѕРІР°РЅРёСЏ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ
if id "$USERNAME" &>/dev/null; then
    warning "РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ $USERNAME СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓРµС‚"
    read -p "РџРµСЂРµСЃРѕР·РґР°С‚СЊ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "РЈРґР°Р»РµРЅРёРµ СЃСѓС‰РµСЃС‚РІСѓСЋС‰РµРіРѕ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ..."
        userdel -r "$USERNAME" 2>/dev/null || true
    else
        error "РџСЂРµСЂРІР°РЅРѕ РїРѕР»СЊР·РѕРІР°С‚РµР»РµРј"
    fi
fi

# РЎРѕР·РґР°РЅРёРµ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РІ Р·Р°РІРёСЃРёРјРѕСЃС‚Рё РѕС‚ С‚РёРїР°
case "$USER_TYPE" in
    admin)
        info "РЎРѕР·РґР°РЅРёРµ Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂР° СЃ РїРѕР»РЅС‹РјРё РїСЂР°РІР°РјРё..."
        useradd -m -s /bin/bash -c "test-hard Administrator" "$USERNAME"

        # Р”РѕР±Р°РІРёС‚СЊ РІ docker group
        usermod -aG docker "$USERNAME"

        # РЎРѕР·РґР°С‚СЊ РґРёСЂРµРєС‚РѕСЂРёРё
        mkdir -p "$INSTALL_DIR"/{reports,logs,configs,scripts}
        chown -R "$USERNAME:$USERNAME" "$INSTALL_DIR"
        chmod 750 "$INSTALL_DIR"
        chmod 700 "$INSTALL_DIR/configs"

        # РќР°СЃС‚СЂРѕРёС‚СЊ sudo
        info "РќР°СЃС‚СЂРѕР№РєР° РѕРіСЂР°РЅРёС‡РµРЅРЅРѕРіРѕ sudo РґРѕСЃС‚СѓРїР°..."
        cat > "/etc/sudoers.d/$USERNAME" << 'EOF'
# test-hard Administrator - РѕРіСЂР°РЅРёС‡РµРЅРЅС‹Рµ РїСЂР°РІР°
hardening-admin ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/bin/docker-compose, /usr/local/bin/docker-compose, /usr/bin/systemctl restart docker, /usr/bin/systemctl stop docker, /usr/bin/systemctl start docker
Defaults:hardening-admin !requiretty
EOF
        chmod 440 "/etc/sudoers.d/$USERNAME"

        # РџСЂРѕРІРµСЂРёС‚СЊ sudoers
        visudo -c || error "РћС€РёР±РєР° РІ РєРѕРЅС„РёРіСѓСЂР°С†РёРё sudoers!"

        success "РђРґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂ СЃРѕР·РґР°РЅ СѓСЃРїРµС€РЅРѕ"
        ;;

    scanner)
        info "РЎРѕР·РґР°РЅРёРµ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РґР»СЏ СЃРєР°РЅРёСЂРѕРІР°РЅРёСЏ..."
        useradd -r -m -s /bin/bash -c "test-hard Scanner Service" "$USERNAME"

        # РќР• РґРѕР±Р°РІР»СЏРµРј РІ docker group!

        # РЎРѕР·РґР°С‚СЊ СЂР°Р±РѕС‡РёРµ РґРёСЂРµРєС‚РѕСЂРёРё
        SCANNER_DIR="/var/lib/$USERNAME"
        mkdir -p "$SCANNER_DIR"/{scripts,reports,cache,.ssh}
        chown -R "$USERNAME:$USERNAME" "$SCANNER_DIR"
        chmod 750 "$SCANNER_DIR"
        chmod 700 "$SCANNER_DIR/.ssh"
        chmod 700 "$SCANNER_DIR/cache"

        # РќР°СЃС‚СЂРѕРёС‚СЊ РѕРіСЂР°РЅРёС‡РµРЅРЅС‹Р№ sudo
        info "РќР°СЃС‚СЂРѕР№РєР° РјРёРЅРёРјР°Р»СЊРЅРѕРіРѕ sudo РґРѕСЃС‚СѓРїР°..."
        cat > "/etc/sudoers.d/$USERNAME" << 'EOF'
# test-hard Scanner - С‚РѕР»СЊРєРѕ РєРѕРјР°РЅРґС‹ СЃРєР°РЅРёСЂРѕРІР°РЅРёСЏ
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

        # РџСЂРѕРІРµСЂРёС‚СЊ sudoers
        visudo -c || error "РћС€РёР±РєР° РІ РєРѕРЅС„РёРіСѓСЂР°С†РёРё sudoers!"

        # Р“РµРЅРµСЂРёСЂРѕРІР°С‚СЊ SSH РєР»СЋС‡
        info "Р“РµРЅРµСЂР°С†РёСЏ SSH РєР»СЋС‡Р° РґР»СЏ СѓРґР°Р»РµРЅРЅРѕРіРѕ СЃРєР°РЅРёСЂРѕРІР°РЅРёСЏ..."
        sudo -u "$USERNAME" ssh-keygen -t ed25519 -C "scanner@test-hard" \
            -f "$SCANNER_DIR/.ssh/scanner_key" -N "" -q
        chmod 600 "$SCANNER_DIR/.ssh/scanner_key"
        chmod 644 "$SCANNER_DIR/.ssh/scanner_key.pub"

        success "РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РґР»СЏ СЃРєР°РЅРёСЂРѕРІР°РЅРёСЏ СЃРѕР·РґР°РЅ СѓСЃРїРµС€РЅРѕ"
        echo ""
        info "РџСѓР±Р»РёС‡РЅС‹Р№ SSH РєР»СЋС‡ РґР»СЏ РєРѕРїРёСЂРѕРІР°РЅРёСЏ РЅР° С†РµР»РµРІС‹Рµ С…РѕСЃС‚С‹:"
        cat "$SCANNER_DIR/.ssh/scanner_key.pub"
        ;;

    service)
        info "РЎРѕР·РґР°РЅРёРµ СЃРёСЃС‚РµРјРЅРѕРіРѕ СЃРµСЂРІРёСЃРЅРѕРіРѕ Р°РєРєР°СѓРЅС‚Р°..."
        useradd -r -s /usr/sbin/nologin -c "test-hard Service Account" "$USERNAME"

        # РЎРѕР·РґР°С‚СЊ РјРёРЅРёРјР°Р»СЊРЅСѓСЋ СЂР°Р±РѕС‡СѓСЋ РґРёСЂРµРєС‚РѕСЂРёСЋ
        SERVICE_DIR="/var/lib/$USERNAME"
        mkdir -p "$SERVICE_DIR"
        chown "$USERNAME:$USERNAME" "$SERVICE_DIR"
        chmod 700 "$SERVICE_DIR"

        # РЎРѕР·РґР°С‚СЊ РєРѕРЅС„РёРіСѓСЂР°С†РёРѕРЅРЅС‹Р№ С„Р°Р№Р»
        info "РЎРѕР·РґР°РЅРёРµ РєРѕРЅС„РёРіСѓСЂР°С†РёРё РґР»СЏ systemd СЃРµСЂРІРёСЃР°..."
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

        # РЎРѕР·РґР°С‚СЊ systemd unit
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

        # РЎРѕР·РґР°С‚СЊ timer
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

        success "РЎРµСЂРІРёСЃРЅС‹Р№ Р°РєРєР°СѓРЅС‚ СЃРѕР·РґР°РЅ СѓСЃРїРµС€РЅРѕ"
        info "Р”Р»СЏ Р°РєС‚РёРІР°С†РёРё С‚Р°Р№РјРµСЂР° РІС‹РїРѕР»РЅРёС‚Рµ: systemctl enable --now hardening-scanner.timer"
        ;;

    readonly)
        info "РЎРѕР·РґР°РЅРёРµ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ С‚РѕР»СЊРєРѕ РґР»СЏ С‡С‚РµРЅРёСЏ..."
        useradd -m -s /bin/bash -c "test-hard Read-Only User" "$USERNAME"

        # РЎРѕР·РґР°С‚СЊ РіСЂСѓРїРїСѓ РґР»СЏ С‡С‚РµРЅРёСЏ РѕС‚С‡РµС‚РѕРІ
        groupadd -f hardening-reports
        usermod -aG hardening-reports "$USERNAME"

        # РЈСЃС‚Р°РЅРѕРІРёС‚СЊ РїСЂР°РІР° РЅР° РѕС‚С‡РµС‚С‹
        if [[ -d "$INSTALL_DIR/reports" ]]; then
            chgrp -R hardening-reports "$INSTALL_DIR/reports"
            chmod -R 750 "$INSTALL_DIR/reports"
            find "$INSTALL_DIR/reports" -type f -exec chmod 640 {} \;
        fi

        success "РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РґР»СЏ С‡С‚РµРЅРёСЏ СЃРѕР·РґР°РЅ СѓСЃРїРµС€РЅРѕ"
        info "Р”Р»СЏ РґРѕСЃС‚СѓРїР° Рє Grafana СЃРѕР·РґР°Р№С‚Рµ Viewer РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РІ РІРµР±-РёРЅС‚РµСЂС„РµР№СЃРµ"
        ;;
esac

# РЎРѕР·РґР°С‚СЊ Р±Р°Р·РѕРІСѓСЋ СЃС‚СЂСѓРєС‚СѓСЂСѓ SSH
if [[ "$USER_TYPE" != "service" ]]; then
    SSH_DIR="/home/$USERNAME/.ssh"
    if [[ ! -d "$SSH_DIR" ]]; then
        mkdir -p "$SSH_DIR"
        chown "$USERNAME:$USERNAME" "$SSH_DIR"
        chmod 700 "$SSH_DIR"
    fi
fi

# РЎРѕР·РґР°С‚СЊ .env С„Р°Р№Р» РґР»СЏ admin
if [[ "$USER_TYPE" == "admin" ]]; then
    info "РЎРѕР·РґР°РЅРёРµ .env С„Р°Р№Р»Р°..."
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

    warning "РЈСЃС‚Р°РЅРѕРІР»РµРЅ СЃР»СѓС‡Р°Р№РЅС‹Р№ РїР°СЂРѕР»СЊ РґР»СЏ Grafana: $RANDOM_PASSWORD"
    warning "РЎРѕС…СЂР°РЅРёС‚Рµ РїР°СЂРѕР»СЊ РІ Р±РµР·РѕРїР°СЃРЅРѕРј РјРµСЃС‚Рµ Рё РёР·РјРµРЅРёС‚Рµ РµРіРѕ РїСЂРё РїРµСЂРІРѕРј РІС…РѕРґРµ!"
fi

echo ""
success "=========================================="
success "РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ $USERNAME РЅР°СЃС‚СЂРѕРµРЅ СѓСЃРїРµС€РЅРѕ!"
success "=========================================="
echo ""

# Р’С‹РІРµСЃС‚Рё РёРЅСЃС‚СЂСѓРєС†РёРё
case "$USER_TYPE" in
    admin)
        info "РЎР»РµРґСѓСЋС‰РёРµ С€Р°РіРё:"
        echo "1. РџРµСЂРµРєР»СЋС‡РёС‚РµСЃСЊ РЅР° РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ: sudo -iu $USERNAME"
        echo "2. РљР»РѕРЅРёСЂСѓР№С‚Рµ СЂРµРїРѕР·РёС‚РѕСЂРёР№ РІ $INSTALL_DIR"
        echo "3. РќР°СЃС‚СЂРѕР№С‚Рµ .env С„Р°Р№Р»: nano ~/.env"
        echo "4. Р—Р°РїСѓСЃС‚РёС‚Рµ РїР»Р°С‚С„РѕСЂРјСѓ: cd $INSTALL_DIR && make up"
        ;;
    scanner)
        info "РЎР»РµРґСѓСЋС‰РёРµ С€Р°РіРё:"
        echo "1. РЎРєРѕРїРёСЂСѓР№С‚Рµ РїСѓР±Р»РёС‡РЅС‹Р№ РєР»СЋС‡ РЅР° С†РµР»РµРІС‹Рµ С…РѕСЃС‚С‹:"
        echo "   ssh-copy-id -i /var/lib/$USERNAME/.ssh/scanner_key.pub user@target-host"
        echo "2. РќР°СЃС‚СЂРѕР№С‚Рµ inventory С„Р°Р№Р» (СЃРј. docs/REAL-HOSTS-SCANNING.md)"
        echo "3. Р—Р°РїСѓСЃС‚РёС‚Рµ СЃРєР°РЅРёСЂРѕРІР°РЅРёРµ: sudo -u $USERNAME $INSTALL_DIR/scripts/scan-remote-host.sh"
        ;;
    service)
        info "РЎР»РµРґСѓСЋС‰РёРµ С€Р°РіРё:"
        echo "1. РџСЂРѕРІРµСЂСЊС‚Рµ РєРѕРЅС„РёРіСѓСЂР°С†РёСЋ: cat /etc/test-hard/scanner.env"
        echo "2. РђРєС‚РёРІРёСЂСѓР№С‚Рµ С‚Р°Р№РјРµСЂ: systemctl enable --now hardening-scanner.timer"
        echo "3. РџСЂРѕРІРµСЂСЊС‚Рµ СЃС‚Р°С‚СѓСЃ: systemctl status hardening-scanner.timer"
        echo "4. РџСЂРѕСЃРјРѕС‚СЂ Р»РѕРіРѕРІ: journalctl -u hardening-scanner.service -f"
        ;;
    readonly)
        info "РЎР»РµРґСѓСЋС‰РёРµ С€Р°РіРё:"
        echo "1. РЎРѕР·РґР°Р№С‚Рµ Grafana РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ СЃ СЂРѕР»СЊСЋ Viewer"
        echo "2. РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РјРѕР¶РµС‚ С‡РёС‚Р°С‚СЊ РѕС‚С‡РµС‚С‹ РІ $INSTALL_DIR/reports"
        ;;
esac

echo ""
info "РџРѕР»РЅР°СЏ РґРѕРєСѓРјРµРЅС‚Р°С†РёСЏ: docs/USER-SETUP.md"

# РќР°РїРѕРјРёРЅР°РЅРёРµ Рѕ Р±РµР·РѕРїР°СЃРЅРѕСЃС‚Рё
echo ""
warning "=========================================="
warning "РќРђРџРћРњРРќРђРќРР• Рћ Р‘Р•Р—РћРџРђРЎРќРћРЎРўР"
warning "=========================================="
echo "РќР• РґРѕР±Р°РІР»СЏР№С‚Рµ РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№ РІ docker group (РєСЂРѕРјРµ admin)"
echo "РќР• РёСЃРїРѕР»СЊР·СѓР№С‚Рµ РїРѕР»РЅС‹Р№ sudo РґРѕСЃС‚СѓРї ALL=(ALL) ALL"
echo "РСЃРїРѕР»СЊР·СѓР№С‚Рµ SSH РєР»СЋС‡Рё РІРјРµСЃС‚Рѕ РїР°СЂРѕР»РµР№"
echo "РќР°СЃС‚СЂРѕР№С‚Рµ auditd РґР»СЏ РјРѕРЅРёС‚РѕСЂРёРЅРіР° РґРµР№СЃС‚РІРёР№"
echo "Р РѕС‚РёСЂСѓР№С‚Рµ SSH РєР»СЋС‡Рё РєР°Р¶РґС‹Рµ 90 РґРЅРµР№"
echo ""
