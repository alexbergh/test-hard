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
