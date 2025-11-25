@echo off
REM Remove problematic 0-byte script files that cause Git errors
echo Removing problematic script files...

git rm --cached scripts/bump-version.sh 2>nul
git rm --cached scripts/health_check.sh 2>nul
git rm --cached scripts/install-deps.sh 2>nul
git rm --cached scripts/measure_docker_improvements.sh 2>nul
git rm --cached scripts/parse_atomic_red_team_result.py 2>nul
git rm --cached scripts/parse_lynis_log.py 2>nul
git rm --cached scripts/parse_lynis_report.py 2>nul
git rm --cached scripts/parse_openscap_report.py 2>nul
git rm --cached scripts/run_all_checks.sh 2>nul
git rm --cached scripts/run_atomic_red_team_suite.py 2>nul
git rm --cached scripts/run_atomic_red_team_test.sh 2>nul
git rm --cached scripts/run_hardening_suite.sh 2>nul
git rm --cached scripts/run_lynis.sh 2>nul
git rm --cached scripts/run_openscap.sh 2>nul
git rm --cached scripts/run_shell_tests.sh 2>nul
git rm --cached scripts/scan-remote-host.sh 2>nul
git rm --cached scripts/setup-secure-user.sh 2>nul
git rm --cached scripts/test-core-functionality.sh 2>nul
git rm --cached scripts/verify_fixes.sh 2>nul

del /F /Q scripts\bump-version.sh 2>nul
del /F /Q scripts\health_check.sh 2>nul
del /F /Q scripts\install-deps.sh 2>nul
del /F /Q scripts\measure_docker_improvements.sh 2>nul
del /F /Q scripts\parse_atomic_red_team_result.py 2>nul
del /F /Q scripts\parse_lynis_log.py 2>nul
del /F /Q scripts\parse_lynis_report.py 2>nul
del /F /Q scripts\parse_openscap_report.py 2>nul
del /F /Q scripts\run_all_checks.sh 2>nul
del /F /Q scripts\run_atomic_red_team_suite.py 2>nul
del /F /Q scripts\run_atomic_red_team_test.sh 2>nul
del /F /Q scripts\run_hardening_suite.sh 2>nul
del /F /Q scripts\run_lynis.sh 2>nul
del /F /Q scripts\run_openscap.sh 2>nul
del /F /Q scripts\run_shell_tests.sh 2>nul
del /F /Q scripts\scan-remote-host.sh 2>nul
del /F /Q scripts\setup-secure-user.sh 2>nul
del /F /Q scripts\test-core-functionality.sh 2>nul
del /F /Q scripts\verify_fixes.sh 2>nul

echo Done. Now run: git add .
echo Then: git commit -m "Fix: Remove problematic files and normalize line endings"
