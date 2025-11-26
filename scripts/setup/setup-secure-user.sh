#!/bin/bash
# setup-secure-user.sh - Secure user setup for test-hard
# Usage: sudo ./scripts/setup-secure-user.sh [admin|scanner|service|readonly]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Output functions
info() { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# Check root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root (sudo)"
fi

# Get user type
USER_TYPE="${1:-}"
INSTALL_DIR="${2:-/opt/test-hard}"

show_usage() {
    cat << EOF
Usage: sudo $0 <user_type> [directory]

User types:
  admin     - Platform administrator (limited sudo)
  scanner   - User for scanning (minimal privileges)
  service   - Service account for systemd (no sudo)
  readonly  - Read-only access to reports

Parameters:
  directory - Installation directory (default: /opt/test-hard)

Examples:
  sudo $0 admin
  sudo $0 scanner /var/lib/hardening
  sudo $0 service

Documentation: docs/USER-SETUP.md
EOF
    exit 0
}

# Show help
if [[ -z "$USER_TYPE" ]] || [[ "$USER_TYPE" == "-h" ]] || [[ "$USER_TYPE" == "--help" ]]; then
    show_usage
fi

# Validate user type
case "$USER_TYPE" in
    admin|scanner|service|readonly)
        ;;
    *)
        error "Unknown user type: $USER_TYPE. Use: admin, scanner, service or readonly"
        ;;
esac

USERNAME="hardening-${USER_TYPE}"

info "Setting up user: $USERNAME"
info "Installation directory: $INSTALL_DIR"
echo ""

# Check if user exists
if id "$USERNAME" &>/dev/null; then
    warning "User $USERNAME already exists"
    read -p "Recreate user? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "Removing existing user..."
        userdel -r "$USERNAME" 2>/dev/null || true
    else
        info "Keeping existing user"
        exit 0
    fi
fi

# Create user based on type
case "$USER_TYPE" in
    admin)
        info "Creating administrator user..."
        useradd -m -s /bin/bash -c "test-hard Administrator" "$USERNAME"

        # Create working directories
        mkdir -p "$INSTALL_DIR"/{scripts,reports,configs}
        chown -R "$USERNAME:$USERNAME" "$INSTALL_DIR"
        chmod 750 "$INSTALL_DIR"
        chmod 700 "$INSTALL_DIR/configs"

        # Setup limited sudo
        info "Setting up limited sudo access..."
        cat > "/etc/sudoers.d/$USERNAME" << 'EOF'
# test-hard Administrator - limited sudo
hardening-admin ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/bin/docker-compose
hardening-admin ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart docker
hardening-admin ALL=(ALL) NOPASSWD: /usr/bin/systemctl status *
hardening-admin ALL=(ALL) NOPASSWD: /opt/test-hard/scripts/*
Defaults:hardening-admin !authenticate
EOF
        chmod 440 "/etc/sudoers.d/$USERNAME"

        # Verify sudoers
        visudo -c || error "Error in sudoers configuration!"

        success "Administrator user created successfully"
        ;;

    scanner)
        info "Creating scanner user..."
        useradd -m -s /bin/bash -c "test-hard Scanner" "$USERNAME"
        # Do NOT add to docker group!

        # Create working directories
        SCANNER_DIR="/var/lib/$USERNAME"
        mkdir -p "$SCANNER_DIR"/{scripts,reports,cache,.ssh}
        chown -R "$USERNAME:$USERNAME" "$SCANNER_DIR"
        chmod 750 "$SCANNER_DIR"
        chmod 700 "$SCANNER_DIR/.ssh"
        chmod 700 "$SCANNER_DIR/cache"

        # Setup limited sudo
        info "Setting up minimal sudo access..."
        cat > "/etc/sudoers.d/$USERNAME" << 'EOF'
# test-hard Scanner - minimal sudo for scanning only
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

        # Verify sudoers
        visudo -c || error "Error in sudoers configuration!"

        # Generate SSH key
        info "Generating SSH key for remote scanning..."
        sudo -u "$USERNAME" ssh-keygen -t ed25519 -C "scanner@test-hard" \
            -f "$SCANNER_DIR/.ssh/scanner_key" -N "" -q
        chmod 600 "$SCANNER_DIR/.ssh/scanner_key"
        chmod 644 "$SCANNER_DIR/.ssh/scanner_key.pub"

        success "Scanner user created successfully"
        echo ""
        info "Public SSH key for copying to target hosts:"
        cat "$SCANNER_DIR/.ssh/scanner_key.pub"
        ;;

    service)
        info "Creating system service account..."
        useradd -r -s /usr/sbin/nologin -c "test-hard Service Account" "$USERNAME"

        # Create minimal working directory
        SERVICE_DIR="/var/lib/$USERNAME"
        mkdir -p "$SERVICE_DIR"
        chown "$USERNAME:$USERNAME" "$SERVICE_DIR"
        chmod 700 "$SERVICE_DIR"

        # Create configuration file
        info "Creating systemd service configuration..."
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

        # Create systemd unit
        cat > /etc/systemd/system/hardening-scanner.service << EOF
[Unit]
Description=test-hard Security Scanner
After=network.target docker.service
Requires=docker.service

[Service]
Type=oneshot
User=$USERNAME
Group=$USERNAME
EnvironmentFile=/etc/test-hard/scanner.env
ExecStart=$INSTALL_DIR/scripts/scanning/run_hardening_suite.sh
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ReadWritePaths=$INSTALL_DIR/reports

[Install]
WantedBy=multi-user.target
EOF

        # Create timer for scheduled scanning
        cat > /etc/systemd/system/hardening-scanner.timer << EOF
[Unit]
Description=Run security scan daily

[Timer]
OnCalendar=daily
RandomizedDelaySec=3600
Persistent=true

[Install]
WantedBy=timers.target
EOF

        systemctl daemon-reload

        success "Service account created successfully"
        info "To activate timer run: systemctl enable --now hardening-scanner.timer"
        ;;

    readonly)
        info "Creating read-only user..."
        useradd -m -s /bin/bash -c "test-hard Read-Only User" "$USERNAME"

        # Create group for reading reports
        groupadd -f hardening-reports
        usermod -aG hardening-reports "$USERNAME"

        # Set permissions on reports
        if [[ -d "$INSTALL_DIR/reports" ]]; then
            chgrp -R hardening-reports "$INSTALL_DIR/reports"
            chmod -R 750 "$INSTALL_DIR/reports"
            find "$INSTALL_DIR/reports" -type f -exec chmod 640 {} \;
        fi

        success "Read-only user created successfully"
        info "For Grafana access create a Viewer user in web interface"
        ;;
esac

echo ""

# Generate random password for Grafana if admin user
if [[ "$USER_TYPE" == "admin" ]]; then
    RANDOM_PASSWORD=$(openssl rand -base64 16)
    cat > "/home/$USERNAME/.env" << EOF
# Grafana credentials - CHANGE AFTER FIRST LOGIN!
GF_ADMIN_USER=admin
GF_ADMIN_PASSWORD=$RANDOM_PASSWORD
EOF
    chown "$USERNAME:$USERNAME" "/home/$USERNAME/.env"
    chmod 600 "/home/$USERNAME/.env"

    warning "Random Grafana password set: $RANDOM_PASSWORD"
    warning "Save the password securely and change it on first login!"
fi

echo ""
success "User $USERNAME setup complete!"
echo ""
info "Next steps:"
echo "  1. Review created configuration files"
echo "  2. Test user permissions"
echo "  3. See docs/USER-SETUP.md for detailed documentation"
