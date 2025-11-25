#!/usr/bin/env bash
# Install Python dependencies and pre-commit hooks
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

error() {
    echo "[ERROR] $*" >&2
}

check_command() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python
if ! check_command python3; then
    error "python3 not found. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
log "Found Python $PYTHON_VERSION"

# Check pip
if ! check_command pip3 && ! python3 -m pip --version >/dev/null 2>&1; then
    error "pip not found. Please install pip."
    exit 1
fi

# Install Python requirements
log "Installing Python requirements..."
cd "$PROJECT_ROOT"

if [ -f "requirements.txt" ]; then
    python3 -m pip install --user -r requirements.txt
    log "[OK] Installed Python dependencies"
else
    error "requirements.txt not found"
    exit 1
fi

# Install pre-commit (optional)
if [ "${INSTALL_PRECOMMIT:-true}" = "true" ]; then
    log "Installing pre-commit hooks..."
    
    if python3 -m pip install --user pre-commit; then
        if [ -f ".pre-commit-config.yaml" ]; then
            python3 -m pre_commit install
            log "[OK] Installed pre-commit hooks"
        else
            log "[WARN] .pre-commit-config.yaml not found, skipping hooks installation"
        fi
    else
        log "[WARN] Failed to install pre-commit (optional)"
    fi
fi

# Verify installations
log "Verifying installations..."

if python3 -c "import yaml; import attr; import click" 2>/dev/null; then
    log "[OK] Core dependencies verified"
else
    error "Some dependencies failed to install"
    exit 1
fi

# Check atomic-operator
if python3 -c "from atomic_operator.atomic_operator import AtomicOperator" 2>/dev/null; then
    log "[OK] atomic-operator available"
else
    log "[WARN] atomic-operator not available (will be installed on first use)"
fi

log ""
log "Installation complete!"
log ""
log "Next steps:"
log "  1. Run: make setup"
log "  2. Edit .env file and change default passwords"
log "  3. Run: make validate"
log "  4. Run: make up"
log ""
