# Security Policy

## Документация по безопасности

- **[Создание пользователей (USER-SETUP.md)](USER-SETUP.md)** - Подробное руководство по безопасному созданию и настройке пользователей
- **[Сканирование реальных хостов (REAL-HOSTS-SCANNING.md)](REAL-HOSTS-SCANNING.md)** - Безопасное сканирование production систем

## Security Improvements

This project implements several security enhancements to protect the monitoring infrastructure:

### 1. Docker Socket Protection

**Issue**: Direct Docker socket access poses significant security risks.

**Solution**: Docker Socket Proxy (`tecnativa/docker-socket-proxy`) is used to limit scanner access:
- Read-only socket access
- Restricted API endpoints (only CONTAINERS, EXEC, IMAGES, INFO)
- No access to VOLUMES, NETWORKS, or POST operations

### 2. User Management and Least Privilege

**КРИТИЧЕСКИ ВАЖНО:** Никогда не запускайте платформу от root или с неограниченными правами!

**Рекомендованные типы пользователей**:
- `hardening-admin` - Администрирование платформы (ограниченный sudo)
- `hardening-scanner` - Запуск сканирований (минимальные права)
- `hardening-service` - Автоматизация через systemd (без sudo)
- `hardening-readonly` - Просмотр отчетов (только чтение)

**Полное руководство**: См. [USER-SETUP.md](USER-SETUP.md) для детальных инструкций по созданию и настройке пользователей.

**Ключевые принципы**:
- **НЕ добавляйте** пользователей в docker group (используйте Docker Socket Proxy)
- **НЕ используйте** полный sudo доступ `ALL=(ALL) ALL`
- **Используйте** SSH ключи вместо паролей
- **Настройте** auditd для мониторинга действий
- **Ротируйте** SSH ключи каждые 90 дней

### 3. Credential Management

**Default Credentials**: Never use default passwords in production!

**Recommended practices**:
```bash
# Generate strong password
openssl rand -base64 32

# Update .env file
cp .env.example .env
nano .env  # Change GF_ADMIN_PASSWORD
```

**Environment Variables**:
- `GF_ADMIN_USER` - Grafana admin username
- `GF_ADMIN_PASSWORD` - Grafana admin password (change immediately!)
- All credentials should be stored in `.env` file (not committed to git)

### 4. Resource Limits

All services have CPU and memory limits to prevent resource exhaustion:
- Telegraf: 0.5 CPU, 256MB RAM
- Prometheus: 1 CPU, 1GB RAM
- Grafana: 0.5 CPU, 512MB RAM
- Scanners: 1 CPU, 512MB RAM each

### 5. Health Monitoring

All critical services implement health checks:
- Prometheus: `/-/healthy` endpoint
- Grafana: `/api/health` endpoint
- Telegraf: `/metrics` endpoint availability
- Alertmanager: `/-/healthy` endpoint

### 6. Network Isolation

Services are isolated in separate networks:
- `default` network: Application services
- `scanner-net` network: Scanner access to Docker proxy

### 7. TLS/SSL Recommendations

**Production Deployment**:
1. Use reverse proxy (nginx/traefik) with Let's Encrypt certificates
2. Enable TLS for all external endpoints
3. Configure Prometheus remote write with TLS
4. Use mTLS for service-to-service communication

Example nginx config:
```nginx
server {
    listen 443 ssl http2;
    server_name monitoring.example.com;
    
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Security Scanning

### OpenSCAP Profiles

Available security profiles:
- `xccdf_org.ssgproject.content_profile_standard` (default)
- `xccdf_org.ssgproject.content_profile_cis` (CIS benchmarks)
- `xccdf_org.ssgproject.content_profile_pci-dss` (PCI-DSS)

Change profile in `OPENSCAP_PROFILE` environment variable.

### Lynis Auditing

Lynis performs comprehensive security audits. Review:
- Hardening index (target: >70)
- Warnings (should be <10)
- Suggestions for improvements

### Atomic Red Team

Tests run in **dry-run mode by default** to prevent system modifications.

To enable real execution:
```bash
ATOMIC_DRY_RUN=false docker compose up
```

**Warning**: Only run real tests in isolated test environments!

## Alert Thresholds

### Security Alerts

| Alert | Threshold | Severity |
|-------|-----------|----------|
| Lynis Score Low | <60 | Warning |
| Lynis Score Critical | <40 | Critical |
| High Lynis Warnings | >10 | Warning |
| OpenSCAP High Failures | >50 | Warning |
| OpenSCAP Critical Failures | >100 | Critical |
| Atomic Test Failure | Any | Warning |

### System Alerts

| Alert | Threshold | Severity |
|-------|-----------|----------|
| High CPU Usage | >80% for 10m | Warning |
| High Memory Usage | >85% for 10m | Warning |
| Low Disk Space | <15% free | Warning |
| Telegraf Down | 2 minutes | Critical |

## Reporting Security Issues

If you discover a security vulnerability:

1. **Do NOT** open a public issue
2. Email security concerns to the maintainers
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

## Security Checklist for Production

### User Management
- [ ] Создан выделенный пользователь (не root)
- [ ] Пользователи НЕ добавлены в docker group
- [ ] Настроены ограниченные sudo права (см. [USER-SETUP.md](USER-SETUP.md))
- [ ] Настроена SSH аутентификация по ключам
- [ ] Включен auditd для мониторинга действий
- [ ] Настроена периодическая ротация SSH ключей

### Credentials & Access
- [ ] Change all default passwords
- [ ] Enable TLS/SSL for all external services
- [ ] Restrict network access (firewall rules)
- [ ] Review and restrict sudo permissions
- [ ] Use Docker Socket Proxy (not direct socket access)

### Monitoring & Maintenance
- [ ] Enable audit logging
- [ ] Regular security scans (weekly)
- [ ] Monitor alert channels
- [ ] Keep all images updated
- [ ] Review and act on security findings
- [ ] Backup configuration and data
- [ ] Document incident response procedures

## Updates and Patching

Regularly update:
```bash
# Pull latest images
docker compose pull

# Rebuild custom images
docker compose build --pull

# Restart services
docker compose up -d
```

## Security Best Practices

1. **Principle of Least Privilege**: Grant minimal required permissions
2. **Defense in Depth**: Multiple security layers
3. **Regular Audits**: Schedule weekly security scans
4. **Incident Response**: Prepare for security incidents
5. **Secure Defaults**: Security enabled by default
6. **Monitoring**: Continuous security monitoring
7. **Updates**: Keep all components updated
8. **Documentation**: Document security configurations

## References

- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Prometheus Security](https://prometheus.io/docs/operating/security/)
