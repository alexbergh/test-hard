#!/bin/bash

if [[ "${LYNIS_ALREADY_ESCALATED:-0}" != "1" && "$(id -u)" -ne 0 ]]; then
  exec sudo -E LYNIS_ALREADY_ESCALATED=1 "$0" "$@"
fi

REPORT_FILE="/tmp/lynis-report-$(hostname).json"
METRICS_FILE="/tmp/lynis-metrics-$(hostname).txt"

# Запуск Lynis
lynis audit system --json --report-file "$REPORT_FILE"

# Парсинг отчета и отправка метрик через Telegraf (через socat или curl)
/usr/bin/python3 "$(dirname "$0")/parse_lynis_report.py" "$REPORT_FILE" > "$METRICS_FILE"

# Отправка метрик в Telegraf (если Telegraf настроен на input.socket_listener)
# Или Telegraf может сам читать этот файл через input.file
# Пример для input.file:
# mv "$METRICS_FILE" "/var/lib/telegraf/lynis_metrics.txt" # Telegraf будет читать из /var/lib/telegraf
