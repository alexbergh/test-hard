@echo off
echo Adding executable permissions to scripts...

git add --chmod=+x IMMEDIATE_FIXES.sh
git add --chmod=+x scripts/parsing/parse_atomic_red_team_result.py
git add --chmod=+x scripts/parsing/parse_lynis_log.py
git add --chmod=+x scripts/parsing/parse_lynis_report.py
git add --chmod=+x scripts/parsing/parse_openscap_report.py
git add --chmod=+x scripts/testing/run_shell_tests.sh
git add --chmod=+x scripts/backup/backup.sh
git add --chmod=+x scripts/monitoring/health_check.sh
git add --chmod=+x scripts/monitoring/measure_docker_improvements.sh
git add --chmod=+x scripts/scanning/run_atomic_red_team_test.sh
git add --chmod=+x scripts/scanning/run_atomic_red_team_suite.py
git add --chmod=+x scripts/scanning/run_lynis.sh
git add --chmod=+x scripts/scanning/run_openscap.sh
git add --chmod=+x scripts/scanning/run_all_checks.sh
git add --chmod=+x scripts/scanning/run_hardening_suite.sh
git add --chmod=+x scripts/scanning/scan-remote-host.sh
git add --chmod=+x scripts/setup/install-deps.sh
git add --chmod=+x scripts/setup/setup-secure-user.sh
git add --chmod=+x scripts/testing/test-core-functionality.sh
git add --chmod=+x scripts/testing/verify_fixes.sh
git add --chmod=+x scripts/utils/bump-version.sh
git add --chmod=+x scripts/reorganize.sh
git add --chmod=+x docker/common/hardening-entrypoint.sh
git add --chmod=+x scanners/openscap/entrypoint-new.sh
git add --chmod=+x scanners/openscap/entrypoint.py
git add --chmod=+x scanners/lynis/entrypoint.sh

echo.
echo Executable permissions added!
echo.
echo Note: Pre-commit also fixed:
echo   - Trailing whitespace (27 files)
echo   - Black formatting (15 Python files)
echo   - Import sorting (7 files)
echo.
echo Remaining issues (can be ignored if non-critical):
echo   - Flake8: 47 line length warnings (E501)
echo   - Flake8: 6 complexity warnings (C901)
echo   - Shellcheck: Style suggestions
