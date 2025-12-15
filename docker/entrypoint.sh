#!/bin/bash
set -e

COMMAND="${1:-help}"

case "$COMMAND" in
  lynis)
    shift
    exec /usr/sbin/lynis "$@"
    ;;
  openscap)
    shift
    exec /usr/bin/oscap "$@"
    ;;
  scan-lynis)
    if [[ -x /opt/test-hard/scanners/lynis/entrypoint.sh ]]; then
      exec /opt/test-hard/scanners/lynis/entrypoint.sh
    fi
    exec /opt/test-hard/scripts/scanning/run_lynis.sh
    ;;
  scan-openscap)
    if [[ -x /opt/test-hard/scanners/openscap/entrypoint-new.sh ]]; then
      exec /opt/test-hard/scanners/openscap/entrypoint-new.sh
    fi
    exec /opt/test-hard/scripts/scanning/run_openscap.sh
    ;;
  scan-all)
    exec /opt/test-hard/scripts/scanning/run_all_checks.sh
    ;;
  atomic)
    shift
    exec python3 /opt/test-hard/scripts/scanning/run_atomic_red_team_suite.py "$@"
    ;;
  parse-lynis)
    shift
    exec python3 /opt/test-hard/scripts/parsing/parse_lynis_report.py "$@"
    ;;
  parse-openscap)
    shift
    exec python3 /opt/test-hard/scripts/parsing/parse_openscap_report.py "$@"
    ;;
  parse-atomic)
    shift
    exec python3 /opt/test-hard/scripts/parsing/parse_atomic_red_team_result.py "$@"
    ;;
  telegraf)
    shift
    exec /usr/bin/telegraf --config /etc/telegraf/telegraf.conf "$@"
    ;;
  bash)
    exec /bin/bash
    ;;
  help|*)
    cat <<EOF
test-hard - Security hardening and monitoring platform
Version: 1.0.0

Usage: docker run test-hard <command> [args]

Scanner Commands:
  lynis [args]          Run Lynis scanner directly
  openscap [args]       Run OpenSCAP scanner directly
  scan-lynis           Run Lynis scan with default settings
  scan-openscap        Run OpenSCAP scan with default settings
  scan-all             Run all scanners sequentially
  atomic [args]        Run Atomic Red Team tests

Parser Commands:
  parse-lynis <file>   Parse Lynis report to Prometheus format
  parse-openscap <file> Parse OpenSCAP report to Prometheus format
  parse-atomic <file>   Parse Atomic Red Team results

Utility Commands:
  bash                 Start interactive bash shell
  help                 Show this help message

Examples:
  # Run all scanners
  docker run --rm -v /var/run/docker.sock:/var/run/docker.sock test-hard scan-all

  # Run Lynis on a specific container
  docker run --rm test-hard lynis audit system

  # Run OpenSCAP scan
  docker run --rm test-hard scan-openscap

  # Run Atomic Red Team tests in dry-run mode
  docker run --rm test-hard atomic --dry-run

  # Parse reports
  docker run --rm -v ./reports:/reports test-hard parse-lynis /reports/lynis.json

For more information, visit: https://github.com/alexbergh/test-hard
EOF
    ;;
esac
