# Сводный отчёт по аналитике процессов hardening

Сформировано: 2025-10-21T22:53:17.451079+00:00

## Семейство: openscap
### Контекст: docker (функция: docker_openscap)
- cycle_time_hours: 10.0 → 8.5 (Δ -1.5)
- review_rounds: 2 → 1 (Δ -1)
- review_comments: 12 → 5 (Δ -7)
- incident_frequency: 0.25 → 0.138 (Δ -0.112)
- mttr_hours: 4.5 → 3.6 (Δ -0.9)
- p95_latency_ms: 950.0 → 855.0 (Δ -95.0)
- error_budget_consumed: 0.18 → 0.09 (Δ -0.09)

### Контекст: k8s (функция: k8s_openscap)
- cycle_time_hours: 11.0 → 9.68 (Δ -1.32)
- review_rounds: 2 → 1 (Δ -1)
- review_comments: 11 → 6 (Δ -6)
- incident_frequency: 0.24 → 0.144 (Δ -0.096)
- mttr_hours: 4.8 → 3.94 (Δ -0.86)
- p95_latency_ms: 1000.0 → 920.0 (Δ -80.0)
- error_budget_consumed: 0.19 → 0.105 (Δ -0.085)

**Средние значения по семейству:**
- cycle_time_hours: 10.5 → 9.09 (Δ -1.41)
- review_rounds: 2 → 1 (Δ -1)
- review_comments: 12 → 6 (Δ -6)
- incident_frequency: 0.245 → 0.141 (Δ -0.104)
- mttr_hours: 4.65 → 3.77 (Δ -0.88)
- p95_latency_ms: 975.0 → 887.5 (Δ -87.5)
- error_budget_consumed: 0.185 → 0.098 (Δ -0.087)

## Семейство: telemetry
### Контекст: docker (функция: docker_telemetry)
- cycle_time_hours: 8.0 → 8.0 (Δ 0.0)
- review_rounds: 1 → 1 (Δ 0)
- review_comments: 6 → 6 (Δ 0)
- incident_frequency: 0.3 → 0.27 (Δ -0.03)
- mttr_hours: 3.0 → 2.88 (Δ -0.12)
- p95_latency_ms: 850.0 → 786.2 (Δ -63.8)
- error_budget_consumed: 0.2 → 0.17 (Δ -0.03)

### Контекст: k8s (функция: k8s_telemetry)
- cycle_time_hours: 8.5 → 8.5 (Δ 0.0)
- review_rounds: 1 → 1 (Δ 0)
- review_comments: 5 → 5 (Δ 0)
- incident_frequency: 0.32 → 0.291 (Δ -0.029)
- mttr_hours: 3.5 → 3.38 (Δ -0.12)
- p95_latency_ms: 900.0 → 846.0 (Δ -54.0)
- error_budget_consumed: 0.21 → 0.181 (Δ -0.029)

**Средние значения по семейству:**
- cycle_time_hours: 8.25 → 8.25 (Δ 0.0)
- review_rounds: 1 → 1 (Δ +0)
- review_comments: 6 → 6 (Δ +0)
- incident_frequency: 0.31 → 0.28 (Δ -0.029)
- mttr_hours: 3.25 → 3.13 (Δ -0.12)
- p95_latency_ms: 875.0 → 816.1 (Δ -58.9)
- error_budget_consumed: 0.205 → 0.175 (Δ -0.029)

## Семейство: vm
### Контекст: prod (функция: vm_prod)
- cycle_time_hours: 16.0 → 12.48 (Δ -3.52)
- review_rounds: 3 → 2 (Δ -1)
- review_comments: 18 → 12 (Δ -6)
- incident_frequency: 0.33 → 0.243 (Δ -0.087)
- mttr_hours: 6.0 → 5.7 (Δ -0.3)
- p95_latency_ms: 1180.0 → 1156.4 (Δ -23.6)
- error_budget_consumed: 0.25 → 0.18 (Δ -0.07)

### Контекст: test (функция: vm_test)
- cycle_time_hours: 14.0 → 11.48 (Δ -2.52)
- review_rounds: 3 → 2 (Δ -1)
- review_comments: 15 → 11 (Δ -4)
- incident_frequency: 0.35 → 0.274 (Δ -0.076)
- mttr_hours: 6.5 → 6.17 (Δ -0.33)
- p95_latency_ms: 1200.0 → 1176.0 (Δ -24.0)
- error_budget_consumed: 0.26 → 0.2 (Δ -0.06)

**Средние значения по семейству:**
- cycle_time_hours: 15.0 → 11.98 (Δ -3.02)
- review_rounds: 3 → 2 (Δ -1)
- review_comments: 16 → 12 (Δ -5)
- incident_frequency: 0.34 → 0.259 (Δ -0.081)
- mttr_hours: 6.25 → 5.94 (Δ -0.32)
- p95_latency_ms: 1190.0 → 1166.2 (Δ -23.8)
- error_budget_consumed: 0.255 → 0.19 (Δ -0.065)

## Семейство: wazuh
### Контекст: docker (функция: docker_wazuh)
- cycle_time_hours: 9.5 → 7.79 (Δ -1.71)
- review_rounds: 2 → 2 (Δ 0)
- review_comments: 10 → 8 (Δ -2)
- incident_frequency: 0.28 → 0.238 (Δ -0.042)
- mttr_hours: 5.0 → 4.55 (Δ -0.45)
- p95_latency_ms: 1025.0 → 963.5 (Δ -61.5)
- error_budget_consumed: 0.22 → 0.194 (Δ -0.026)

### Контекст: k8s (функция: k8s_wazuh)
- cycle_time_hours: 9.0 → 7.92 (Δ -1.08)
- review_rounds: 2 → 2 (Δ 0)
- review_comments: 9 → 8 (Δ -1)
- incident_frequency: 0.27 → 0.241 (Δ -0.029)
- mttr_hours: 5.3 → 4.92 (Δ -0.38)
- p95_latency_ms: 990.0 → 942.5 (Δ -47.5)
- error_budget_consumed: 0.23 → 0.209 (Δ -0.021)

**Средние значения по семейству:**
- cycle_time_hours: 9.25 → 7.86 (Δ -1.4)
- review_rounds: 2 → 2 (Δ +0)
- review_comments: 10 → 8 (Δ -2)
- incident_frequency: 0.275 → 0.239 (Δ -0.036)
- mttr_hours: 5.15 → 4.73 (Δ -0.42)
- p95_latency_ms: 1007.5 → 953.0 (Δ -54.5)
- error_budget_consumed: 0.225 → 0.202 (Δ -0.024)

