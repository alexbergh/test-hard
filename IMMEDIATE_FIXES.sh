#!/bin/bash
# Immediate Fixes Script for test-hard
# This script applies critical fixes identified in the analysis
# Run with: bash IMMEDIATE_FIXES.sh

set -euo pipefail

echo "[FIX] Applying immediate fixes to test-hard repository..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found. Please run this script from the repository root."
    exit 1
fi

print_status "Found docker-compose.yml"

# 1. Fix hardcoded paths in docker-compose files
echo ""
echo "[NOTE] Fix 1: Removing hardcoded paths from docker-compose files..."

# Backup original files
for file in docker-compose.yml docker-compose.*.yml; do
    if [ -f "$file" ]; then
        cp "$file" "$file.backup"
        print_status "Backed up $file to $file.backup"
    fi
done

# Fix docker-compose.yml
if grep -q "/Users/" docker-compose.yml 2>/dev/null; then
    sed -i.tmp 's|/Users/[^/]*/Documents/GitHub/test-hard/reports|./reports|g' docker-compose.yml
    sed -i.tmp 's|/Users/[^/]*/Documents/GitHub/test-hard/art-storage|./art-storage|g' docker-compose.yml
    rm -f docker-compose.yml.tmp
    print_status "Fixed hardcoded paths in docker-compose.yml"
else
    print_status "No hardcoded paths found in docker-compose.yml"
fi

# 2. Improve .dockerignore
echo ""
echo "[NOTE] Fix 2: Updating .dockerignore..."

cat >> .dockerignore << 'EOF'

# Analysis and reports
reports/
art-storage/
*.log

# Testing
.pytest_cache/
htmlcov/
.coverage
coverage.xml

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.bak
*.backup
EOF

print_status "Updated .dockerignore"

# 3. Create health check script
echo ""
echo "[NOTE] Fix 3: Creating health check script..."

cat > scripts/health_check.sh << 'EOF'
#!/bin/bash
# Health check script for all services
set -e

echo "[HEALTH] Checking services health..."
echo ""

# Prometheus
if curl -sf http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "[OK] Prometheus: healthy"
else
    echo "[ERROR] Prometheus: unhealthy"
    exit 1
fi

# Grafana
if curl -sf http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "[OK] Grafana: healthy"
else
    echo "[ERROR] Grafana: unhealthy"
    exit 1
fi

# Telegraf
if curl -sf http://localhost:9091/metrics > /dev/null 2>&1; then
    echo "[OK] Telegraf: healthy"
else
    echo "[ERROR] Telegraf: unhealthy"
    exit 1
fi

# Alertmanager
if curl -sf http://localhost:9093/-/healthy > /dev/null 2>&1; then
    echo "[OK] Alertmanager: healthy"
else
    echo "[ERROR] Alertmanager: unhealthy"
    exit 1
fi

echo ""
echo "[SUCCESS] All services are healthy!"
EOF

chmod +x scripts/health_check.sh
print_status "Created scripts/health_check.sh"

# 4. Improve .env.example
echo ""
echo "[NOTE] Fix 4: Improving .env.example..."

cat > .env.example << 'EOF'
# Grafana Configuration
# Default credentials (CHANGE IN PRODUCTION!)
GF_ADMIN_USER=admin
GF_ADMIN_PASSWORD=admin

# Grafana Port (change if 3000 is occupied)
GRAFANA_HOST_PORT=3000

# Grafana Authentication
GF_AUTH_BASIC_ENABLED=true
GF_AUTH_DISABLE_LOGIN_FORM=false

# Grafana Logging
GF_LOG_LEVEL=info

# Prometheus Configuration
PROMETHEUS_RETENTION_TIME=30d
PROMETHEUS_RETENTION_SIZE=10GB

# Telegraf Configuration
TELEGRAF_INTERVAL=10s

# Paths (relative to project root)
REPORTS_DIR=./reports
ART_STORAGE_DIR=./art-storage

# Docker Image Version
VERSION=1.0.0

# Optional: Atomic Red Team Configuration
ATOMIC_DRY_RUN=true
RUN_HARDENING_ON_START=false
EOF

print_status "Updated .env.example with comments"

# 5. Add Makefile help
echo ""
echo "[NOTE] Fix 5: Adding help target to Makefile..."

# Check if help target exists
if ! grep -q "^help:" Makefile; then
    # Create temporary file with help target at the beginning
    cat > Makefile.tmp << 'EOF'
.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help

EOF
    cat Makefile >> Makefile.tmp
    mv Makefile.tmp Makefile
    print_status "Added help target to Makefile"
else
    print_status "Help target already exists in Makefile"
fi

# 6. Create CHANGELOG.md
echo ""
echo "[NOTE] Fix 6: Creating CHANGELOG.md..."

if [ ! -f "CHANGELOG.md" ]; then
    cat > CHANGELOG.md << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Repository analysis and development roadmap
- Health check script for all services
- Improved .env.example with detailed comments
- Makefile help target

### Changed
- Fixed hardcoded paths in docker-compose files
- Improved .dockerignore

### Fixed
- Portability issues with absolute paths

## [1.0.0] - 2025-10-29

### Added
- Initial release
- OpenSCAP and Lynis security scanning
- Prometheus + Grafana + Alertmanager monitoring stack
- Atomic Red Team integration
- Telegraf metrics collection
- Multi-distribution support (Debian, Ubuntu, Fedora, CentOS)
- Kubernetes deployment manifests
- Docker Compose multi-environment support
- Comprehensive documentation
- CI/CD with GitHub Actions
- Pre-commit hooks for code quality

### Security
- Docker socket proxy for limited API access
- Resource limits on all containers
- Health checks for all services
EOF
    print_status "Created CHANGELOG.md"
else
    print_status "CHANGELOG.md already exists"
fi

# 7. Create GitHub issue templates
echo ""
echo "[NOTE] Fix 7: Creating GitHub issue templates..."

mkdir -p .github/ISSUE_TEMPLATE

cat > .github/ISSUE_TEMPLATE/bug_report.md << 'EOF'
---
name: Bug Report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description
A clear and concise description of what the bug is.

## To Reproduce
Steps to reproduce the behavior:
1. Run command '...'
2. See error

## Expected Behavior
A clear description of what you expected to happen.

## Environment
- OS: [e.g. Ubuntu 22.04]
- Docker version: [e.g. 24.0.0]
- Docker Compose version: [e.g. 2.20.0]
- Project version: [e.g. 1.0.0]

## Logs
```
Paste relevant logs here
```

## Additional Context
Add any other context about the problem here.
EOF

cat > .github/ISSUE_TEMPLATE/feature_request.md << 'EOF'
---
name: Feature Request
about: Suggest an idea for this project
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

## Feature Description
A clear description of the feature you'd like to see.

## Problem Statement
What problem does this feature solve?

## Proposed Solution
How would you like this feature to work?

## Alternatives Considered
What alternative solutions have you considered?

## Additional Context
Add any other context or screenshots about the feature request here.
EOF

print_status "Created GitHub issue templates"

# 8. Add badges to README
echo ""
echo "[NOTE] Fix 8: Adding badges to README..."

# Check if badges already exist
if ! grep -q "shields.io" README.md; then
    # Create temporary file with badges
    cat > README.tmp << 'EOF'
# test-hard вЂ” РџР»Р°С‚С„РѕСЂРјР° Security Hardening & Monitoring

![CI Status](https://github.com/alexbergh/test-hard/workflows/CI%20Pipeline/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![Kubernetes](https://img.shields.io/badge/kubernetes-ready-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)

EOF
    tail -n +2 README.md >> README.tmp
    mv README.tmp README.md
    print_status "Added badges to README.md"
else
    print_status "Badges already exist in README.md"
fi

# 9. Improve error handling in scripts
echo ""
echo "[NOTE] Fix 9: Improving error handling in bash scripts..."

for script in scripts/*.sh; do
    if [ -f "$script" ] && [ -x "$script" ]; then
        # Check if script already has proper error handling
        if ! grep -q "set -euo pipefail" "$script"; then
            # Backup
            cp "$script" "$script.backup"

            # Add error handling after shebang
            awk 'NR==1 {print; print "set -euo pipefail"; print ""; next} {print}' "$script.backup" > "$script"

            print_status "Improved error handling in $script"
        fi
    fi
done

# 10. Create verification script
echo ""
echo "[NOTE] Fix 10: Creating verification script..."

cat > scripts/verify_fixes.sh << 'EOF'
#!/bin/bash
# Verification script to check if all fixes were applied correctly
set -euo pipefail

echo "[CHECK] Verifying applied fixes..."
echo ""

ERRORS=0

# Check 1: No hardcoded paths
echo "Checking for hardcoded paths..."
if grep -r "/Users/" docker-compose*.yml 2>/dev/null; then
    echo "[ERROR] Found hardcoded paths in docker-compose files"
    ERRORS=$((ERRORS + 1))
else
    echo "[OK] No hardcoded paths found"
fi

# Check 2: Health check script exists
echo "Checking health check script..."
if [ -x "scripts/health_check.sh" ]; then
    echo "[OK] Health check script exists and is executable"
else
    echo "[ERROR] Health check script missing or not executable"
    ERRORS=$((ERRORS + 1))
fi

# Check 3: .env.example has comments
echo "Checking .env.example..."
if grep -q "# Grafana Configuration" .env.example; then
    echo "[OK] .env.example has proper comments"
else
    echo "[ERROR] .env.example missing comments"
    ERRORS=$((ERRORS + 1))
fi

# Check 4: CHANGELOG.md exists
echo "Checking CHANGELOG.md..."
if [ -f "CHANGELOG.md" ]; then
    echo "[OK] CHANGELOG.md exists"
else
    echo "[ERROR] CHANGELOG.md missing"
    ERRORS=$((ERRORS + 1))
fi

# Check 5: Issue templates exist
echo "Checking GitHub issue templates..."
if [ -f ".github/ISSUE_TEMPLATE/bug_report.md" ]; then
    echo "[OK] Bug report template exists"
else
    echo "[ERROR] Bug report template missing"
    ERRORS=$((ERRORS + 1))
fi

# Check 6: Makefile has help
echo "Checking Makefile help..."
if grep -q "^help:" Makefile; then
    echo "[OK] Makefile has help target"
else
    echo "[ERROR] Makefile missing help target"
    ERRORS=$((ERRORS + 1))
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "[SUCCESS] All fixes verified successfully!"
    exit 0
else
    echo "[FAIL] Found $ERRORS issues"
    exit 1
fi
EOF

chmod +x scripts/verify_fixes.sh
print_status "Created scripts/verify_fixes.sh"

# Summary
echo ""
echo "================================================================"
echo "[SUCCESS] All immediate fixes have been applied!"
echo "================================================================"
echo ""
echo "Applied fixes:"
echo "  1. [OK] Fixed hardcoded paths in docker-compose files"
echo "  2. [OK] Improved .dockerignore"
echo "  3. [OK] Created health check script"
echo "  4. [OK] Improved .env.example with comments"
echo "  5. [OK] Added Makefile help target"
echo "  6. [OK] Created CHANGELOG.md"
echo "  7. [OK] Created GitHub issue templates"
echo "  8. [OK] Added badges to README.md"
echo "  9. [OK] Improved error handling in scripts"
echo " 10. [OK] Created verification script"
echo ""
echo "Next steps:"
echo "  1. Review the changes: git diff"
echo "  2. Test the fixes: make up && scripts/health_check.sh"
echo "  3. Verify all fixes: scripts/verify_fixes.sh"
echo "  4. Commit changes: git add . && git commit -m 'Apply immediate fixes from analysis'"
echo ""
echo "Backup files created with .backup extension - remove them after verification"
echo ""
print_status "Done!"
