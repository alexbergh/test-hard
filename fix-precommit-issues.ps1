# Fix pre-commit issues
Write-Host "Fixing pre-commit issues..." -ForegroundColor Cyan

# 1. Add executable permissions to scripts with shebangs
Write-Host "`nAdding executable permissions..." -ForegroundColor Yellow

$scriptsToFix = @(
    "IMMEDIATE_FIXES.sh",
    "scripts/parsing/parse_atomic_red_team_result.py",
    "scripts/parsing/parse_lynis_log.py",
    "scripts/parsing/parse_lynis_report.py",
    "scripts/parsing/parse_openscap_report.py",
    "scripts/testing/run_shell_tests.sh",
    "scripts/backup/backup.sh",
    "scripts/monitoring/health_check.sh",
    "scripts/monitoring/measure_docker_improvements.sh",
    "scripts/scanning/run_atomic_red_team_test.sh",
    "scripts/scanning/run_atomic_red_team_suite.py",
    "scripts/scanning/run_lynis.sh",
    "scripts/scanning/run_openscap.sh",
    "scripts/scanning/run_all_checks.sh",
    "scripts/scanning/run_hardening_suite.sh",
    "scripts/scanning/scan-remote-host.sh",
    "scripts/setup/install-deps.sh",
    "scripts/setup/setup-secure-user.sh",
    "scripts/testing/test-core-functionality.sh",
    "scripts/testing/verify_fixes.sh",
    "scripts/utils/bump-version.sh",
    "scripts/reorganize.sh",
    "docker/common/hardening-entrypoint.sh",
    "scanners/openscap/entrypoint-new.sh",
    "scanners/openscap/entrypoint.py",
    "scanners/lynis/entrypoint.sh"
)

foreach ($script in $scriptsToFix) {
    if (Test-Path $script) {
        git add --chmod=+x $script
        Write-Host "  ✓ $script" -ForegroundColor Green
    }
}

Write-Host "`nExecutable permissions added!" -ForegroundColor Green
Write-Host "`nNote: Flake8 errors (line length, complexity) are style warnings." -ForegroundColor Yellow
Write-Host "These can be addressed later or ignored if not critical." -ForegroundColor Yellow
