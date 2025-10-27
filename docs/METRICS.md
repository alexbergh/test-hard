# Metrics Reference

Complete guide to metrics available in test-hard monitoring platform.

## Table of Contents

- [Security Metrics](#security-metrics)
- [System Metrics](#system-metrics)
- [Atomic Red Team Metrics](#atomic-red-team-metrics)
- [Example Queries](#example-queries)
- [Dashboard Ideas](#dashboard-ideas)

---

## Security Metrics

### Lynis Metrics

**lynis_score**
- Type: Gauge
- Range: 0-100
- Description: Overall hardening index from Lynis audit
- Labels: `host`
- Example:
  ```promql
  lynis_score{host="target-ubuntu"}
  ```

**lynis_warnings_count**
- Type: Gauge
- Description: Number of security warnings found
- Labels: `host`
- Recommended threshold: < 10

**lynis_suggestions_count**
- Type: Gauge
- Description: Number of improvement suggestions
- Labels: `host`

**lynis_tests_performed**
- Type: Gauge
- Description: Total number of tests executed
- Labels: `host`

**lynis_plugins_count**
- Type: Gauge
- Description: Number of Lynis plugins available
- Labels: `host`

### OpenSCAP Metrics

**openscap_pass_count**
- Type: Gauge
- Description: Number of passed security checks
- Labels: `host`

**openscap_fail_count**
- Type: Gauge
- Description: Number of failed security checks
- Labels: `host`
- Alert thresholds:
  - Warning: > 50
  - Critical: > 100

**openscap_error_count**
- Type: Gauge
- Description: Checks that encountered errors
- Labels: `host`

**openscap_unknown_count**
- Type: Gauge
- Description: Checks with unknown results
- Labels: `host`

**openscap_notchecked_count**
- Type: Gauge
- Description: Checks that were not executed
- Labels: `host`

**openscap_notselected_count**
- Type: Gauge
- Description: Checks not selected by profile
- Labels: `host`

**openscap_informational_count**
- Type: Gauge
- Description: Informational findings
- Labels: `host`

**openscap_fixed_count**
- Type: Gauge
- Description: Issues automatically fixed
- Labels: `host`

---

## System Metrics

### CPU Metrics

**cpu_usage_idle**
- Type: Gauge
- Unit: Percent
- Description: CPU idle time percentage
- Labels: `host`, `cpu`

**cpu_usage_system**
- Type: Gauge
- Unit: Percent
- Description: CPU time in system mode
- Labels: `host`, `cpu`

**cpu_usage_user**
- Type: Gauge
- Unit: Percent
- Description: CPU time in user mode
- Labels: `host`, `cpu`

### Memory Metrics

**mem_total**
- Type: Gauge
- Unit: Bytes
- Description: Total system memory
- Labels: `host`

**mem_used**
- Type: Gauge
- Unit: Bytes
- Description: Used memory
- Labels: `host`

**mem_available**
- Type: Gauge
- Unit: Bytes
- Description: Available memory
- Labels: `host`

**mem_used_percent**
- Type: Gauge
- Unit: Percent
- Description: Memory usage percentage
- Labels: `host`

### Disk Metrics

**disk_total**
- Type: Gauge
- Unit: Bytes
- Description: Total disk space
- Labels: `host`, `path`, `device`, `fstype`

**disk_used**
- Type: Gauge
- Unit: Bytes
- Description: Used disk space
- Labels: `host`, `path`, `device`, `fstype`

**disk_free**
- Type: Gauge
- Unit: Bytes
- Description: Free disk space
- Labels: `host`, `path`, `device`, `fstype`

**disk_used_percent**
- Type: Gauge
- Unit: Percent
- Description: Disk usage percentage
- Labels: `host`, `path`

### Network Metrics

**net_bytes_sent**
- Type: Counter
- Unit: Bytes
- Description: Total bytes sent
- Labels: `host`, `interface`

**net_bytes_recv**
- Type: Counter
- Unit: Bytes
- Description: Total bytes received
- Labels: `host`, `interface`

**net_packets_sent**
- Type: Counter
- Description: Total packets sent
- Labels: `host`, `interface`

**net_packets_recv**
- Type: Counter
- Description: Total packets received
- Labels: `host`, `interface`

### Process Metrics

**processes_total**
- Type: Gauge
- Description: Total number of processes
- Labels: `host`

**processes_running**
- Type: Gauge
- Description: Number of running processes
- Labels: `host`

**processes_sleeping**
- Type: Gauge
- Description: Number of sleeping processes
- Labels: `host`

---

## Atomic Red Team Metrics

### Test Results

**art_test_result**
- Type: Gauge
- Values: 0=passed, 1=failed, 2=skipped, 3=error, 4=unknown
- Description: Individual test execution result
- Labels:
  - `host`: Hostname where test ran
  - `scenario`: Scenario identifier
  - `technique`: MITRE ATT&CK technique ID
  - `test`: Test identifier (technique-number)
  - `status`: Test status (passed/failed/skipped/error/unknown)
  - `executor`: Executor type (sh/bash/cmd/powershell)
  - `platforms`: Supported platforms (comma-separated)

**art_scenario_status**
- Type: Gauge
- Values: 0=passed, 1=failed, 2=skipped, 3=error, 4=unknown
- Description: Overall scenario status
- Labels:
  - `host`: Hostname
  - `scenario`: Scenario ID
  - `technique`: MITRE ATT&CK technique ID
  - `status`: Scenario status

**art_summary_total**
- Type: Gauge
- Description: Summary counts by bucket
- Labels:
  - `host`: Hostname
  - `bucket`: One of (passed, failed, skipped, error, unknown, total)

---

## Example Queries

### Security Posture

**Overall Security Score**
```promql
# Average Lynis score across all hosts
avg(lynis_score)

# Minimum score (weakest host)
min(lynis_score)

# Hosts below threshold
lynis_score < 60
```

**Compliance Rate**
```promql
# OpenSCAP pass rate percentage
(openscap_pass_count / (openscap_pass_count + openscap_fail_count)) * 100

# Per-host compliance
sum by(host) (openscap_pass_count) / 
  (sum by(host) (openscap_pass_count) + sum by(host) (openscap_fail_count)) * 100
```

**Security Trend**
```promql
# Lynis score change over time
delta(lynis_score[1h])

# OpenSCAP failures trend
rate(openscap_fail_count[1h])
```

### Atomic Red Team Analysis

**Test Success Rate**
```promql
# Overall success rate
sum(art_test_result{status="passed"} == 0) / 
  sum(art_summary_total{bucket="total"}) * 100

# Per-technique success rate
sum by(technique) (art_test_result{status="passed"} == 0) /
  sum by(technique) (art_test_result) * 100
```

**Failed Tests**
```promql
# Count of failed tests
sum(art_test_result{status="failed"} == 1)

# Failed tests by technique
sum by(technique) (art_test_result{status="failed"} == 1)

# Recent failures
changes(art_test_result{status="failed"}[1h])
```

**Test Coverage**
```promql
# Total unique techniques tested
count(count by(technique) (art_test_result))

# Tests per scenario
sum by(scenario) (art_summary_total{bucket="total"})
```

### System Health

**CPU Usage**
```promql
# Overall CPU usage
100 - (avg(cpu_usage_idle) * 100)

# Per-host CPU usage
100 - (avg by(host) (cpu_usage_idle) * 100)

# High CPU hosts
100 - (avg by(host) (cpu_usage_idle) * 100) > 80
```

**Memory Pressure**
```promql
# Memory usage percentage
(mem_used / mem_total) * 100

# Available memory in GB
mem_available / 1024 / 1024 / 1024

# Hosts with low memory
(mem_available / mem_total) * 100 < 15
```

**Disk Space**
```promql
# Free disk percentage
(disk_free / disk_total) * 100

# Used disk in GB
disk_used / 1024 / 1024 / 1024

# Partitions running out of space
(disk_free / disk_total) * 100 < 15
```

### Network Activity

**Network Throughput**
```promql
# Bytes sent per second
rate(net_bytes_sent[5m])

# Bytes received per second
rate(net_bytes_recv[5m])

# Total network I/O
rate(net_bytes_sent[5m]) + rate(net_bytes_recv[5m])
```

---

## Dashboard Ideas

### Security Overview Dashboard

**Row 1: Key Metrics**
- Stat panel: Average Lynis Score
- Stat panel: Total OpenSCAP Failures
- Stat panel: ART Tests Passed/Failed
- Stat panel: Security Alerts Active

**Row 2: Security Trends**
- Time series: Lynis Score Over Time (all hosts)
- Time series: OpenSCAP Pass/Fail Ratio
- Bar gauge: ART Success Rate by Technique

**Row 3: Host Details**
- Table: Host Security Metrics
  - Columns: Host, Lynis Score, SCAP Fails, Warnings, Status
- Heatmap: Security Scores by Host

### Atomic Red Team Dashboard

**Row 1: Summary**
- Stat panel: Total Tests Run
- Stat panel: Success Rate
- Stat panel: Failed Tests
- Stat panel: Techniques Covered

**Row 2: Test Results**
- Time series: Test Results Over Time (stacked by status)
- Bar chart: Tests by Technique
- Pie chart: Status Distribution

**Row 3: Details**
- Table: Failed Tests
  - Columns: Technique, Test, Host, Executor, Time
- Logs panel: Recent Test Execution Logs

### System Monitoring Dashboard

**Row 1: Resource Overview**
- Gauge: Average CPU Usage
- Gauge: Average Memory Usage
- Gauge: Minimum Free Disk Space
- Stat: Active Processes

**Row 2: Resource Trends**
- Time series: CPU Usage by Host
- Time series: Memory Usage by Host
- Time series: Disk Usage by Mount Point

**Row 3: Network**
- Time series: Network Throughput (in/out)
- Table: Network Interfaces

---

## Grafana Dashboard Configuration

### Datasource Setup

Already configured via provisioning:
```yaml
# grafana/provisioning/datasources/prometheus.yml
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    access: proxy
    isDefault: true
```

### Creating Dashboards

**Option 1: Manual Creation**
1. Login to Grafana (http://localhost:3000)
2. Click "+" → "Dashboard"
3. Add panels with queries from this guide
4. Save dashboard

**Option 2: JSON Import**
1. Create dashboard JSON file
2. Place in `grafana/dashboards/`
3. Restart Grafana: `docker compose restart grafana`
4. Dashboard auto-loads via provisioning

**Option 3: Export/Import**
1. Create dashboard in UI
2. Export JSON (Dashboard Settings → JSON Model)
3. Save to `grafana/dashboards/`
4. Commit to repository

### Panel Types Recommendations

| Metric Type | Recommended Panel |
|-------------|-------------------|
| Single value | Stat |
| Trend over time | Time series |
| Current vs threshold | Gauge |
| Multiple values | Bar chart / Table |
| Distribution | Pie chart |
| Heatmap data | Heatmap |
| Logs | Logs panel |

---

## Alerting Integration

Metrics can trigger alerts defined in `prometheus/alert.rules.yml`.

**Alert Flow:**
```
Metric → Prometheus → Alert Rule → Alertmanager → Notification
```

**Example Alert Configuration:**
```yaml
- alert: LynisScoreLow
  expr: lynis_score < 60
  for: 5m
  annotations:
    summary: "Low security score on {{ $labels.host }}"
    metric: "{{ $value }}"
```

See [prometheus/alert.rules.yml](../prometheus/alert.rules.yml) for all configured alerts.

---

## Metric Retention

Prometheus retention configured in docker-compose.yml:
- Time-based: 30 days (default)
- Size-based: 10GB (default)

Adjust via environment variables:
```bash
echo "PROMETHEUS_RETENTION_TIME=60d" >> .env
echo "PROMETHEUS_RETENTION_SIZE=20GB" >> .env
```

---

## Troubleshooting

**Metrics not appearing:**
1. Check Telegraf is running: `make health`
2. Verify metrics endpoint: `curl http://localhost:9091/metrics`
3. Check Prometheus targets: http://localhost:9090/targets
4. Review Telegraf logs: `docker compose logs telegraf`

**Stale metrics:**
1. Check scan execution: `make scan`
2. Verify report files exist: `ls -la reports/`
3. Review parser scripts in `scripts/`

**Missing labels:**
1. Verify hostname resolution
2. Check metric generation in scripts
3. Review Prometheus scrape config
