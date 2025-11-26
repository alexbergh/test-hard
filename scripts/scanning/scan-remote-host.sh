#!/bin/bash
# Scan remote host via SSH
set -euo pipefail

# Usage: ./scan-remote-host.sh <host> [user] [ssh_key]
HOST=${1:?Usage: $0 <host> [user] [ssh_key]}
USER=${2:-scanner}
SSH_KEY=${3:-~/.ssh/scanner_key}

REPORTS_DIR="./reports/lynis"
mkdir -p "$REPORTS_DIR"

echo "Scanning remote host: $HOST"
echo "   User: $USER"
echo "   SSH Key: $SSH_KEY"
echo ""

# Test SSH connection
echo "Testing SSH connection..."
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=5 -o BatchMode=yes "$USER@$HOST" "echo 'SSH OK'" >/dev/null 2>&1; then
    echo "SSH connection failed to $USER@$HOST"
    echo "   Check:"
    echo "   1. SSH key is correct: $SSH_KEY"
    echo "   2. User exists on remote host: $USER"
    echo "   3. Host is reachable: $HOST"
    exit 1
fi
echo "SSH connection OK"
echo ""

# Detect OS
echo "Detecting OS..."
OS_TYPE=$(ssh -i "$SSH_KEY" "$USER@$HOST" "cat /etc/os-release | grep '^ID=' | cut -d= -f2 | tr -d '\"'")
echo "   OS: $OS_TYPE"
echo ""

# Install Lynis
echo "Installing Lynis..."
case "$OS_TYPE" in
    ubuntu|debian)
        ssh -i "$SSH_KEY" "$USER@$HOST" "sudo apt-get update -qq && sudo apt-get install -y -qq lynis" || {
            echo "Failed to install Lynis"
            exit 1
        }
        ;;
    fedora|rhel|centos)
        ssh -i "$SSH_KEY" "$USER@$HOST" "sudo dnf install -y -q epel-release && sudo dnf install -y -q lynis" || {
            echo "Failed to install Lynis"
            exit 1
        }
        ;;
    *)
        echo "Unknown OS: $OS_TYPE, trying generic install..."
        ssh -i "$SSH_KEY" "$USER@$HOST" "sudo apt-get install -y lynis || sudo dnf install -y lynis || sudo yum install -y lynis" || {
            echo "Failed to install Lynis"
            exit 1
        }
        ;;
esac
echo "Lynis installed"
echo ""

# Run Lynis audit
echo "Running Lynis audit (this may take 2-5 minutes)..."
ssh -i "$SSH_KEY" "$USER@$HOST" "sudo lynis audit system --quick --quiet" || {
    echo "Lynis audit completed with warnings"
}
echo "Audit complete"
echo ""

# Fetch reports
echo "Fetching reports..."
scp -i "$SSH_KEY" -q "$USER@$HOST:/var/log/lynis.log" "$REPORTS_DIR/${HOST}.log" || {
    echo "Failed to fetch lynis.log"
    exit 1
}

scp -i "$SSH_KEY" -q "$USER@$HOST:/var/log/lynis-report.dat" "$REPORTS_DIR/${HOST}.dat" 2>/dev/null || {
    echo "lynis-report.dat not found (optional)"
}
echo "Reports downloaded"
echo ""

# Parse metrics
echo "Parsing metrics..."
if [ -f "scripts/parse_lynis_report.py" ]; then
    python3 scripts/parse_lynis_report.py "$REPORTS_DIR/${HOST}.log" > "$REPORTS_DIR/${HOST}_metrics.prom" || {
        echo "Failed to parse metrics"
    }
    echo "Metrics generated: $REPORTS_DIR/${HOST}_metrics.prom"
else
    echo "parse_lynis_report.py not found, skipping metrics generation"
fi
echo ""

# Summary
echo "========================================================"
echo "Scan complete for $HOST"
echo "========================================================"
echo ""
echo "Reports:"
echo "  - Log: $REPORTS_DIR/${HOST}.log"
echo "  - Data: $REPORTS_DIR/${HOST}.dat"
echo "  - Metrics: $REPORTS_DIR/${HOST}_metrics.prom"
echo ""

# Show quick summary
if [ -f "$REPORTS_DIR/${HOST}.log" ]; then
    echo "Quick Summary:"
    SCORE=$(grep -i "hardening index" "$REPORTS_DIR/${HOST}.log" | grep -oE "\[[0-9]+\]" | grep -oE "[0-9]+" | head -1 || echo "N/A")
    WARNINGS=$(grep -c "Warning:" "$REPORTS_DIR/${HOST}.log" 2>/dev/null || echo "0")
    SUGGESTIONS=$(grep -c "Suggestion:" "$REPORTS_DIR/${HOST}.log" 2>/dev/null || echo "0")

    echo "  - Hardening Score: $SCORE/100"
    echo "  - Warnings: $WARNINGS"
    echo "  - Suggestions: $SUGGESTIONS"
fi
echo ""
echo "View in Grafana: http://localhost:3000"
