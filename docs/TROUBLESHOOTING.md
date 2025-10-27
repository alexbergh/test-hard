# Troubleshooting Guide

Common issues and their solutions for the test-hard monitoring platform.

## Table of Contents

- [Docker Issues](#docker-issues)
- [Service Health Issues](#service-health-issues)
- [Grafana Issues](#grafana-issues)
- [Prometheus Issues](#prometheus-issues)
- [Scanner Issues](#scanner-issues)
- [Network Issues](#network-issues)
- [Performance Issues](#performance-issues)

---

## Docker Issues

### Docker Compose Not Found

**Symptom**: `docker compose: command not found`

**Solution**:
```bash
# Check Docker Compose version
docker compose version

# If using older Docker, try:
docker-compose version

# Update Makefile to use docker-compose:
export COMPOSE="docker-compose"
make up
```

### Permission Denied on Docker Socket

**Symptom**: `permission denied while trying to connect to the Docker daemon socket`

**Solution**:
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, then verify:
docker ps

# Or use sudo (not recommended for production):
sudo docker compose up -d
```

### Port Already in Use

**Symptom**: `Bind for 0.0.0.0:3000 failed: port is already allocated`

**Solution**:
```bash
# Check what's using the port
sudo lsof -i :3000
# or
sudo ss -tulpn | grep :3000

# Option 1: Stop conflicting service
sudo systemctl stop <service-name>

# Option 2: Change port in .env
echo "GRAFANA_HOST_PORT=3001" >> .env
make restart
```

### Out of Disk Space

**Symptom**: `no space left on device`

**Solution**:
```bash
# Clean up Docker resources
docker system prune -af --volumes

# Check disk usage
df -h
docker system df

# Clean old images
docker image prune -a

# Remove unused volumes
docker volume prune
```

---

## Service Health Issues

### Services Not Starting

**Symptom**: Services remain in "starting" or "unhealthy" state

**Diagnosis**:
```bash
# Check service status
make health

# View logs
make logs

# Check specific service
docker compose logs grafana
docker compose logs prometheus
```

**Solutions**:

1. **Check dependencies**:
   ```bash
   make check-deps
   ```

2. **Validate configurations**:
   ```bash
   make validate
   ```

3. **Check resource limits**:
   ```bash
   docker stats
   ```

4. **Restart services**:
   ```bash
   make restart
   ```

### Health Checks Failing

**Symptom**: Services marked as "unhealthy"

**Solution**:
```bash
# Check health check logs
docker inspect <container-name> | grep -A 10 Health

# Manually test health endpoint
curl -v http://localhost:9090/-/healthy  # Prometheus
curl -v http://localhost:3000/api/health  # Grafana
curl -v http://localhost:9091/metrics     # Telegraf

# Increase health check intervals (temporary)
# Edit docker-compose.yml health check section
```

---

## Grafana Issues

### 401 Unauthorized

**Symptom**: Cannot login to Grafana, receiving 401 errors

**Solutions**:

1. **Wrong credentials**:
   ```bash
   # Check configured credentials
   cat .env | grep GF_ADMIN

   # Reset admin password
   docker compose exec grafana grafana-cli admin reset-admin-password newpassword
   ```

2. **Wrong Grafana instance**:
   ```bash
   # Verify correct container
   docker ps --filter "publish=3000"

   # Check Grafana version
   docker compose exec grafana grafana-cli -v

   # Verify environment variables
   docker compose exec grafana env | grep '^GF_'
   ```

3. **Port conflict**:
   ```bash
   # Check if another Grafana is running
   curl http://localhost:3000/api/health

   # Change port if needed
   echo "GRAFANA_HOST_PORT=3001" >> .env
   make restart
   ```

### Datasource Not Working

**Symptom**: "Bad Gateway" or connection errors in Grafana

**Solution**:
```bash
# Check Prometheus is accessible from Grafana container
docker compose exec grafana wget -O- http://prometheus:9090/api/v1/status/config

# Verify network connectivity
docker network inspect test-hard_default

# Check Prometheus logs
docker compose logs prometheus

# Recreate datasource
# Navigate to Grafana > Configuration > Data Sources > Delete > Re-add
```

### Dashboards Not Loading

**Symptom**: Empty dashboard list or provisioning errors

**Solution**:
```bash
# Check provisioning directory
ls -la grafana/provisioning/dashboards/

# Verify dashboard files
ls -la grafana/dashboards/

# Check Grafana logs for provisioning errors
docker compose logs grafana | grep -i provision

# Restart Grafana to re-provision
docker compose restart grafana
```

---

## Prometheus Issues

### Targets Down

**Symptom**: Telegraf or other targets showing as "DOWN" in Prometheus

**Diagnosis**:
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets'

# Check if Telegraf is responding
curl http://localhost:9091/metrics

# Verify network connectivity
docker compose exec prometheus wget -O- http://telegraf:9091/metrics
```

**Solutions**:

1. **Telegraf not running**:
   ```bash
   docker compose ps telegraf
   docker compose restart telegraf
   ```

2. **Network issues**:
   ```bash
   docker network ls
   docker network inspect test-hard_default
   ```

3. **Configuration error**:
   ```bash
   # Validate Prometheus config
   docker compose exec prometheus promtool check config /etc/prometheus/prometheus.yml
   ```

### High Memory Usage

**Symptom**: Prometheus consuming excessive memory

**Solution**:
```bash
# Check current usage
docker stats prometheus

# Reduce retention
echo "PROMETHEUS_RETENTION_TIME=15d" >> .env
echo "PROMETHEUS_RETENTION_SIZE=5GB" >> .env
make restart

# Check TSDB status
curl http://localhost:9090/api/v1/status/tsdb

# Compact old data
docker compose exec prometheus \
  promtool tsdb create-blocks-from rules /prometheus
```

### Query Timeout

**Symptom**: "Query timeout" errors in Grafana

**Solution**:
```bash
# Increase query timeout in Prometheus
# Edit docker-compose.yml, add to prometheus command:
#   - "--query.timeout=2m"
#   - "--query.max-samples=50000000"

# Optimize queries in Grafana dashboards
# Use shorter time ranges
# Add rate() or increase() for counters
```

---

## Scanner Issues

### OpenSCAP Scanner Fails

**Symptom**: `openscap-scanner` exits with errors

**Diagnosis**:
```bash
# Check scanner logs
docker compose logs openscap-scanner

# Verify targets are running
docker ps | grep target-

# Check datastream files
docker compose exec openscap-scanner ls -la /usr/share/xml/scap/ssg/content/
```

**Solutions**:

1. **Target container not accessible**:
   ```bash
   # Verify docker-proxy is running
   docker compose ps docker-proxy

   # Check scanner can access Docker API
   docker compose exec openscap-scanner \
     env | grep DOCKER_HOST
   ```

2. **Missing datastream**:
   ```bash
   # Check available datastreams in entrypoint.py
   # Verify distribution matches datastream name
   ```

3. **Permission issues**:
   ```bash
   # Ensure reports directory is writable
   chmod 777 reports/
   ```

### Lynis Scanner Issues

**Symptom**: Lynis reports not generated

**Solution**:
```bash
# Run Lynis manually
docker compose run --rm lynis-scanner

# Check if Lynis is installed in targets
docker exec target-debian dpkg -l | grep lynis

# Verify reports directory
ls -la reports/lynis/
```

### Atomic Red Team Failures

**Symptom**: ART tests failing or not executing

**Diagnosis**:
```bash
# Check if running in dry-run mode
grep ATOMIC_DRY_RUN .env

# View ART logs
cat art-storage/latest.json | jq '.scenarios[].tests[] | select(.status=="failed")'
```

**Solutions**:

1. **Prerequisites missing**:
   ```bash
   # Run prereqs mode first
   ./scripts/run_atomic_red_team_test.sh --mode prereqs
   ```

2. **Technique not found**:
   ```bash
   # List available techniques
   find ~/.cache/atomic-red-team -name "T*.yaml"

   # Verify scenarios.yaml technique IDs
   cat atomic-red-team/scenarios.yaml
   ```

3. **Timeout issues**:
   ```bash
   # Increase timeout
   echo "ATOMIC_TIMEOUT=120" >> .env
   ```

---

## Network Issues

### DNS Resolution Fails

**Symptom**: Containers can't resolve service names

**Solution**:
```bash
# Verify Docker DNS
docker compose exec prometheus nslookup telegraf

# Check network configuration
docker network inspect test-hard_default

# Restart Docker daemon
sudo systemctl restart docker
make restart
```

### Cannot Access External Resources

**Symptom**: `--fetch-remote-resources` fails in OpenSCAP

**Solution**:
```bash
# Check DNS and internet connectivity
docker compose exec openscap-scanner ping -c 3 8.8.8.8
docker compose exec openscap-scanner curl -I https://www.redhat.com

# Configure HTTP proxy if needed
# Add to docker-compose.yml environment:
#   HTTP_PROXY: http://proxy.example.com:8080
#   HTTPS_PROXY: http://proxy.example.com:8080
```

---

## Performance Issues

### Slow Scans

**Symptom**: Scans taking very long to complete

**Solutions**:

1. **Increase resources**:
   ```bash
   # Edit docker-compose.yml, increase limits:
   #   cpus: '2.0'
   #   memory: 1G
   ```

2. **Parallelize scans**:
   ```bash
   # Run scanners concurrently
   docker compose run -d openscap-scanner
   docker compose run -d lynis-scanner
   ```

3. **Reduce scope**:
   ```bash
   # Scan fewer targets
   docker compose run openscap-scanner \
     -e TARGET_CONTAINERS="target-ubuntu"
   ```

### High CPU Usage

**Symptom**: System running hot, high load average

**Solution**:
```bash
# Check resource usage
docker stats

# Identify culprit
top -b -n 1 | head -20

# Reduce scan frequency
# Edit telegraf.conf, increase intervals:
#   interval = "120s"  # Instead of 60s

# Limit CPU for resource-intensive services
# Already configured in docker-compose.yml
```

---

## General Debugging

### Enable Debug Logging

```bash
# Python scripts
export LOG_LEVEL=DEBUG
python3 scripts/run_atomic_red_team_suite.py --verbose

# Telegraf
# Edit telegraf.conf: debug = true
docker compose restart telegraf

# Docker Compose
docker compose --verbose up -d
```

### Collect Diagnostics

```bash
# Create diagnostic bundle
mkdir -p diagnostics
docker compose ps > diagnostics/services.txt
docker compose logs > diagnostics/logs.txt
docker stats --no-stream > diagnostics/stats.txt
docker network ls > diagnostics/networks.txt
make health > diagnostics/health.txt 2>&1
cp .env diagnostics/env.txt 2>/dev/null || echo "No .env file"

# Create tarball
tar czf diagnostics-$(date +%Y%m%d-%H%M%S).tar.gz diagnostics/
```

### Reset Everything

```bash
# Nuclear option - complete reset
docker compose down -v
docker system prune -af --volumes
rm -rf reports/* art-storage/*
make setup
make up
```

---

## Getting Help

If you're still stuck:

1. **Check logs thoroughly**:
   ```bash
   docker compose logs --tail=100 --follow
   ```

2. **Search existing issues**: Check GitHub issues for similar problems

3. **Provide details when asking**:
   - Docker version: `docker --version`
   - Docker Compose version: `docker compose version`
   - OS: `uname -a`
   - Relevant logs
   - Steps to reproduce

4. **Diagnostic bundle**: Attach the diagnostics tarball created above
