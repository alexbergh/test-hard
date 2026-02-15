# Scanning Scripts

Скрипты для выполнения security-сканирования контейнеров, образов и сети.

## Файлы

- `run_lynis.sh` -- запуск Lynis аудита безопасности
- `run_openscap.sh` -- запуск OpenSCAP compliance-сканирования
- `run_atomic_red_team_test.sh` -- запуск Atomic Red Team тестов (MITRE ATT&CK)
- `run_atomic_red_team_suite.py` -- Python-обертка для ART тестов с параллельным запуском
- `run_hardening_suite.sh` -- запуск полного набора проверок (Lynis + OpenSCAP + ART)
- `run_all_checks.sh` -- запуск всех видов сканирования
- `run_network_scan.py` -- сетевое сканирование Docker-сети (nmap: хосты, порты, сервисы)
- `scan-images.sh` -- сканирование контейнерных образов через Trivy
- `scan-remote-host.sh` -- сканирование удаленных хостов по SSH
