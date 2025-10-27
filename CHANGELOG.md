# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2024-10-27

### 🚀 Phase 1 Complete: CI/CD & DevOps Infrastructure

Major milestone: Project is now CI/CD-ready with comprehensive testing and deployment automation.

### Added

#### CI/CD Pipeline (NEW!)
- **GitHub Actions Workflows**: Complete CI/CD automation
  - `.github/workflows/ci.yml` - Lint, test, build, security scan
  - `.github/workflows/cd.yml` - Automated deployments (staging/production)
  - `.github/workflows/dependency-update.yml` - Weekly dependency checks
- **Testing Framework**: Comprehensive pytest-based testing
  - Unit tests for all parsers (`tests/unit/`)
  - Integration tests for Docker Compose stack (`tests/integration/`)
  - Code coverage reporting (Codecov integration)
  - `pytest.ini` configuration
- **Multi-Environment Support**: 
  - `docker-compose.dev.yml` - Development overrides
  - `docker-compose.staging.yml` - Staging configuration
  - `docker-compose.prod.yml` - Production hardening
- **Kubernetes Manifests**: Full k8s deployment (`k8s/`)
  - Base configurations with Kustomize
  - Environment-specific overlays (dev/staging/prod)
  - PersistentVolumeClaims for data persistence
  - Ingress with TLS support
  - Resource requests and limits
- **Version Management**:
  - `VERSION` file (semantic versioning)
  - `scripts/bump-version.sh` - Automated version bumping
  - Makefile commands: `bump-patch`, `bump-minor`, `bump-major`
- **Documentation**:
  - `docs/CI-CD.md` - Complete CI/CD guide
  - `k8s/README.md` - Kubernetes deployment guide

#### Security Enhancements
- **Docker Socket Proxy**: Added `tecnativa/docker-socket-proxy` to limit scanner access to Docker API
  - Read-only socket access
  - Restricted API endpoints
  - Isolated network for scanners
- **Security Documentation**: Added comprehensive `SECURITY.md` with best practices
- **Password Security**: Updated `.env.example` with security warnings and stronger default password

#### Infrastructure Improvements
- **Health Checks**: Added health checks for all critical services
  - Prometheus: `/-/healthy` endpoint monitoring
  - Grafana: `/api/health` endpoint monitoring
  - Telegraf: metrics endpoint availability check
  - Alertmanager: health endpoint monitoring
- **Resource Limits**: Configured CPU and memory limits for all services
  - Prevents resource exhaustion
  - Ensures fair resource distribution
  - Better stability under load
- **Network Isolation**: Implemented separate Docker networks
  - `default` network for application services
  - `scanner-net` network for scanner-to-proxy communication

#### Monitoring & Alerting
- **Expanded Alert Rules**: Added comprehensive alerting in `prometheus/alert.rules.yml`
  - Security hardening alerts (Lynis score thresholds)
  - OpenSCAP compliance alerts
  - Atomic Red Team test failure alerts
  - System resource alerts (CPU, memory, disk)
- **Prometheus Retention**: Configurable retention policies
  - Default: 30 days time-based retention
  - Default: 10GB size-based retention
  - Configurable via environment variables

#### Code Quality
- **Logging Infrastructure**: Replaced `print()` statements with proper logging
  - `run_atomic_red_team_suite.py`: Comprehensive logging with levels
  - `parse_atomic_red_team_result.py`: Error handling and logging
  - `parse_openscap_report.py`: XML parsing error handling and logging
  - `parse_lynis_report.py`: JSON validation and logging
- **Error Handling**: Improved exception handling across all Python scripts
  - Graceful degradation
  - Informative error messages
  - Proper exit codes
- **Type Hints**: Added type annotations to Python functions
- **Pre-commit Hooks**: Added `.pre-commit-config.yaml` for code quality
  - Black code formatting
  - Flake8 linting
  - Shell script checking
  - YAML validation
  - Dockerfile linting

#### Development Tools
- **Makefile Enhancements**: Added new make targets
  - `make check-deps`: Verify required dependencies
  - `make health`: Check service health status
  - `make validate`: Validate configuration files
  - `make test`: Run syntax checks on scripts
  - `make setup`: Initial project setup
- **Configuration Validation**: Added syntax checking for YAML and Python files

### Changed

#### Configuration Updates
- **Telegraf Configuration**: Improved `telegraf/telegraf.conf`
  - Commented out osquery section (requires separate setup)
  - Increased timeout for heavy queries
  - Added logging configuration
  - Better documentation
- **Docker Compose**: Major improvements to `docker-compose.yml`
  - Removed direct Docker socket mounting from scanners
  - Added docker-proxy service
  - Configured health checks for all services
  - Added resource limits
  - Improved service dependencies
- **Makefile**: Updated `MONITORING_SERVICES` to include `docker-proxy`

#### Security Improvements
- **Scanner Isolation**: Scanners now communicate through docker-proxy
  - No direct access to Docker socket
  - Limited API surface
  - Better audit trail
- **Environment Variables**: Expanded `.env.example` with more options
  - Prometheus retention settings
  - Atomic Red Team configuration
  - Grafana log level

### Fixed

#### Bug Fixes
- **XML Parsing**: Added proper error handling for malformed OpenSCAP reports
- **JSON Parsing**: Added validation for Atomic Red Team and Lynis reports
- **File Existence Checks**: Improved handling of missing report files
- **Timeout Issues**: Increased timeouts for resource-intensive operations

#### Code Quality
- **Escaping**: Fixed label value escaping in Prometheus metrics
- **Path Handling**: Improved cross-platform path handling using `pathlib`
- **Error Messages**: More descriptive error messages with context

### Security

#### Critical Fixes
- ⚠️ **Default Credentials**: Changed default Grafana password in example
- ⚠️ **Docker Socket Access**: Restricted via socket proxy
- ⚠️ **Resource Limits**: Prevents DoS via resource exhaustion

#### Recommendations
- Enable TLS for production deployments
- Regularly update Docker images
- Review and rotate credentials
- Monitor security alerts
- Follow SECURITY.md guidelines

### Documentation

#### New Documentation
- `SECURITY.md`: Comprehensive security guide
- `CHANGELOG.md`: Project change history
- Inline code comments improved
- Makefile help improved

#### Updated Documentation
- `README.md`: Updated with new features (will be updated)
- Docker Compose comments
- Script documentation strings
- Configuration file comments

## Migration Guide

### Updating from Previous Version

1. **Backup your data**:
   ```bash
   docker compose down
   cp -r prometheus_data prometheus_data.backup
   cp -r grafana_data grafana_data.backup
   ```

2. **Update configuration**:
   ```bash
   cp .env .env.backup
   # Review new options in .env.example
   ```

3. **Pull new changes**:
   ```bash
   git pull
   docker compose pull
   ```

4. **Update environment**:
   ```bash
   # Update .env with new variables from .env.example
   nano .env
   ```

5. **Restart services**:
   ```bash
   make setup
   make validate
   make up
   make health
   ```

### Breaking Changes

- **Scanner Configuration**: Scanners now use `DOCKER_HOST=tcp://docker-proxy:2375`
  - Update custom scanner scripts if any
- **Telegraf Osquery**: Now commented out by default
  - Uncomment and configure if needed
- **Network Configuration**: New `scanner-net` network
  - Existing deployments will recreate networks

### New Environment Variables

Add to your `.env` file:
```bash
# Prometheus retention
PROMETHEUS_RETENTION_TIME=30d
PROMETHEUS_RETENTION_SIZE=10GB

# Atomic Red Team
ATOMIC_DRY_RUN=true
ATOMIC_TIMEOUT=60

# Grafana logging
GF_LOG_LEVEL=info
```

## Roadmap

### Planned Features

#### High Priority
- [ ] TLS/SSL configuration examples
- [ ] Integration tests
- [ ] Grafana dashboard examples
- [ ] Automated backup solution

#### Medium Priority
- [ ] CI/CD pipeline
- [ ] Docker image vulnerability scanning
- [ ] Log aggregation (ELK/Loki)
- [ ] API authentication for Prometheus/Alertmanager

#### Low Priority
- [ ] Multi-architecture support (ARM64)
- [ ] Kubernetes deployment manifests
- [ ] Web UI for report viewing
- [ ] Custom Grafana plugins

## Contributing

Please read CONTRIBUTING.md (to be created) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the terms specified in the LICENSE file.
