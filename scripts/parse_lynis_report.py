#!/usr/bin/env python3
import json
import sys

def parse_lynis_report(report_path):
    with open(report_path, 'r') as f:
        report = json.load(f)

    metrics = {}
    # Пример парсинга: Lynis Score
    if 'general' in report and 'hardening_index' in report['general']:
        metrics['lynis_score'] = int(report['general']['hardening_index'])

    # Пример парсинга: Количество предупреждений
    if 'warnings' in report:
        metrics['lynis_warnings_count'] = len(report['warnings'])
    
    # Пример парсинга: Количество предложений
    if 'suggestions' in report:
        metrics['lynis_suggestions_count'] = len(report['suggestions'])

    # Добавьте больше парсинга по мере необходимости (failed_audits, plugin_results и т.д.)

    # Вывод метрик в формате Prometheus/InfluxDB Line Protocol
    for key, value in metrics.items():
        print(f"{key}{{host=\"{report['general'].get('hostname', 'unknown')}\"}} {value}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: parse_lynis_report.py <path_to_lynis_json_report>")
        sys.exit(1)
    parse_lynis_report(sys.argv[1])
