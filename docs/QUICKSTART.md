# Quick Start Guide

Get up and running with test-hard in 5 minutes.

## Prerequisites

- Docker 20.10+
- Docker Compose v2.0+
- Python 3.8+
- 4GB RAM minimum
- 10GB free disk space

## Installation

### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd test-hard

# Initial setup (creates .env, directories)
make setup

# Verify dependencies
make check-deps
```

### 2. Configure Environment

```bash
# Edit .env file
nano .env

# IMPORTANT: Change default password!
# Generate strong password:
openssl rand -base64 32

# Update in .env:
# GF_ADMIN_PASSWORD=<your-strong-password>
```

### 3. Start Services

```bash
# Validate configurations
make validate

# Start all services
make up

# Check health
make health
```

Wait 1-2 minutes for services to become healthy.

## Access Services

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| Grafana | http://localhost:3000 | admin / (see .env) |
| Prometheus | http://localhost:9090 | None |
| Alertmanager | http://localhost:9093 | None |

## Run Security Scans

### Quick Scan

```bash
# Run all scanners
make scan

# View reports
ls -la reports/openscap/
ls -la reports/lynis/
```

### Atomic Red Team (Dry Run)

```bash
# Run ART scenarios in dry-run mode (safe)
./scripts/run_atomic_red_team_test.sh

# View results
cat art-storage/latest.json | jq '.summary'
```

## View Metrics

### In Prometheus

1. Open http://localhost:9090
2. Try queries:
   ```promql
   # Lynis score
   lynis_score
   
   # OpenSCAP failures
   openscap_fail_count
   
   # Atomic Red Team results
   art_test_result
   ```

### In Grafana

1. Open http://localhost:3000
2. Login with credentials from `.env`
3. Navigate to Explore
4. Select Prometheus datasource
5. Enter metrics queries

## Common Commands

```bash
# View logs
make logs

# Restart services
make restart

# Stop everything
make down

# Clean reports
make clean

# Run health checks
make health

# Run validation
make validate

# Run syntax tests
make test
```

## Troubleshooting

### Services won't start

```bash
# Check logs
docker compose logs grafana
docker compose logs prometheus

# Verify ports not in use
sudo lsof -i :3000
sudo lsof -i :9090

# Restart Docker
sudo systemctl restart docker
make restart
```

### Permission errors

```bash
# Fix reports directory
chmod 777 reports/

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

### High memory usage

```bash
# Check resource usage
docker stats

# Reduce Prometheus retention
echo "PROMETHEUS_RETENTION_TIME=15d" >> .env
make restart
```

## Next Steps

### Import Grafana Dashboards

1. Create dashboard files in `grafana/dashboards/`
2. Restart Grafana: `docker compose restart grafana`
3. Dashboards auto-load via provisioning

### Configure Alerting

1. Edit `prometheus/alertmanager.yml`
2. Add webhook/email configuration
3. Restart: `docker compose restart alertmanager`

Example webhook:
```yaml
receivers:
  - name: 'webhook'
    webhook_configs:
      - url: 'http://your-webhook-url'
```

### Run Real Atomic Red Team Tests

**WARNING**: Only in isolated test environments!

```bash
# Disable dry-run
echo "ATOMIC_DRY_RUN=false" >> .env

# Run specific technique
./scripts/run_atomic_red_team_test.sh T1082 run
```

### Add More Targets

1. Edit `docker-compose.yml`
2. Add target container:
   ```yaml
   target-rocky:
     image: rockylinux/rockylinux:9
     container_name: target-rocky
     command: ["sleep", "infinity"]
   ```
3. Update scanner environment:
   ```yaml
   environment:
     TARGET_CONTAINERS: "... target-rocky"
   ```

## Production Checklist

Before deploying to production:

- [ ] Change all default passwords
- [ ] Enable TLS/SSL (use reverse proxy)
- [ ] Configure firewall rules
- [ ] Set up regular backups
- [ ] Configure alerting destination
- [ ] Review and adjust resource limits
- [ ] Enable audit logging
- [ ] Schedule regular scans
- [ ] Document incident response procedures
- [ ] Test disaster recovery

See [SECURITY.md](SECURITY.md) for detailed security recommendations.

## Architecture Overview

```
┌─────────────┐
│   Grafana   │ ← Visualization
└──────┬──────┘
       │
┌──────▼──────┐
│ Prometheus  │ ← Metrics storage & alerting
└──────┬──────┘
       │
┌──────▼──────┐
│  Telegraf   │ ← Metrics collection
└──────┬──────┘
       │
       ├─→ System metrics (CPU, RAM, disk)
       ├─→ Lynis reports
       ├─→ OpenSCAP reports
       └─→ Atomic Red Team results
```

## Getting Help

- **Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Security**: See [SECURITY.md](SECURITY.md)
- **Changes**: See [CHANGELOG.md](CHANGELOG.md)
- **Full docs**: See [README.md](README.md)

## Useful Links

- [Prometheus Query Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Atomic Red Team](https://github.com/redcanaryco/atomic-red-team)
- [OpenSCAP](https://www.open-scap.org/)
- [Lynis](https://cisofy.com/lynis/)

---

**Ready to dive deeper?** Check out the [full README](README.md) for comprehensive documentation.
