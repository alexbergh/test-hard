# Parsing Scripts

Парсеры для обработки отчетов сканирования и конвертации в Prometheus-метрики.

## Файлы

- `parse_lynis_log.py` -- парсинг Lynis логов и извлечение метрик
- `parse_lynis_report.py` -- парсинг Lynis отчетов (JSON/DAT) в Prometheus-формат
- `generate_lynis_metrics.py` -- генерация агрегированных Lynis-метрик для Telegraf
- `parse_openscap_report.py` -- парсинг OpenSCAP XML-отчетов в Prometheus-формат
- `parse_atomic_red_team_result.py` -- парсинг результатов Atomic Red Team тестов
