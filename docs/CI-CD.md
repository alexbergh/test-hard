# CI/CD Pipeline Documentation

Complete guide to the Continuous Integration and Continuous Deployment pipeline.

## Overview

The test-hard project uses GitHub Actions for CI/CD with the following workflows:

- **CI Pipeline** (`.github/workflows/ci.yml`) - Code quality, testing, security scanning
- **CD Pipeline** (`.github/workflows/cd.yml`) - Automated deployments
- **Dependency Updates** (`.github/workflows/dependency-update.yml`) - Weekly dependency checks

## CI Pipeline

### Workflow Stages

```
┌─────────────┐
│   Lint      │ ← Code quality checks
└──────┬──────┘
       │
┌──────▼──────┐
│  Validate   │ ← Configuration validation
└──────┬──────┘
       │
┌──────▼──────┐
│ Unit Tests  │ ← Fast unit tests
└──────┬──────┘
       │
┌──────▼──────────┐
│ Integration     │ ← Docker Compose tests
│     Tests       │
└──────┬──────────┘
       │
┌──────▼──────────┐
│   Security      │ ← Trivy vulnerability scan
│   Scanning      │
└──────┬──────────┘
       │
┌──────▼──────┐
│   Build     │ ← Build & tag Docker images
└─────────────┘
```

### Trigger Conditions

```yaml
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  workflow_dispatch:  # Manual trigger
```

### Jobs Breakdown

#### 1. Lint Job

**Purpose**: Ensure code quality and style consistency

**Steps**:
- Checkout code
- Install pre-commit
- Run all pre-commit hooks

**Tools**:
- Black (Python formatting)
- Flake8 (linting)
- isort (import sorting)
- shellcheck (shell script linting)
- yamllint (YAML validation)
- Hadolint (Dockerfile linting)

**Failure Conditions**:
- Code style violations
- Linting errors
- Invalid YAML/JSON

#### 2. Validate Job

**Purpose**: Validate all configuration files

**Checks**:
```bash
make validate
- docker-compose.yml syntax
- prometheus.yml validity
- alert.rules.yml syntax
- Python script compilation
```

#### 3. Unit Tests

**Purpose**: Fast, isolated tests

**Coverage Target**: 80%

**Commands**:
```bash
pytest tests/unit/ -v --cov=scripts --cov-report=xml
```

**Artifacts**:
- Code coverage report (uploaded to Codecov)

#### 4. Integration Tests

**Purpose**: End-to-end testing with Docker

**Steps**:
1. Build all Docker images
2. Start Docker Compose stack
3. Wait for services to be healthy (45s)
4. Run health checks
5. Execute integration tests
6. Cleanup

**Timeout**: 30 minutes

#### 5. Security Scan

**Purpose**: Identify vulnerabilities

**Tools**:
- Trivy (filesystem and Docker image scanning)

**Severity Levels**:
- HIGH
- CRITICAL

**Output**: SARIF format uploaded to GitHub Security

#### 6. Build Job

**Purpose**: Build and tag Docker images

**Conditions**: Only on `main` branch

**Process**:
```bash
export VERSION=$(cat VERSION)
docker compose build
docker tag test-hard/openscap-scanner:latest test-hard/openscap-scanner:$VERSION
# ... tag other images
```

## CD Pipeline

### Deployment Stages

```
main branch push
      │
      ▼
┌─────────────┐
│   Staging   │ ← Automatic deployment
└──────┬──────┘
       │
   Manual approval
       │
       ▼
┌─────────────┐
│ Production  │ ← Manual trigger or tag
└─────────────┘
```

### Staging Deployment

**Trigger**: Push to `main` branch

**Steps**:
1. Checkout code
2. Read VERSION file
3. Deploy to staging environment
4. Run smoke tests
5. Send notification

**Smoke Tests**:
```bash
curl -f https://staging.example.com/health
```

### Production Deployment

**Trigger**: 
- Git tag `v*` (e.g., `v1.0.0`)
- Manual workflow dispatch

**Steps**:
1. Create backup
2. Deploy to production
3. Run smoke tests
4. Rollback on failure
5. Send notification (Slack/Teams)

**Environment Protection**:
- Requires manual approval
- Restricted to maintainers only

## Local CI Simulation

Run CI checks locally before pushing:

```bash
# Install dependencies
make install-dev

# Run all CI checks
make ci

# Individual checks
make lint
make test-unit
make test-integration
make validate
```

## Branch Strategy

### Branch Protection Rules

**main**:
- Require PR before merge
- Require CI checks to pass
- Require code review (1 approver)
- No force push
- Include administrators

**develop**:
- Require CI checks to pass
- Allow force push with lease

### Workflow

```
feature/xxx → develop → main → production
                  ↓        ↓
              staging    tags (v1.0.0)
```

## Version Management

### Semantic Versioning

Format: `MAJOR.MINOR.PATCH`

**MAJOR**: Breaking changes
**MINOR**: New features (backwards compatible)
**PATCH**: Bug fixes

### Bumping Version

```bash
# Bump patch version (1.0.0 → 1.0.1)
make bump-patch

# Bump minor version (1.0.0 → 1.1.0)
make bump-minor

# Bump major version (1.0.0 → 2.0.0)
make bump-major

# Commit and tag
git add VERSION
git commit -m "chore: bump version to $(cat VERSION)"
git tag v$(cat VERSION)
git push && git push --tags
```

### Automated Releases

Tags trigger:
1. Production deployment
2. GitHub Release creation
3. Changelog attachment
4. Docker image push to registry

## Docker Registry

### Image Tagging Strategy

```
test-hard/service:latest          # Latest build
test-hard/service:1.0.0          # Version tag
test-hard/service:1.0            # Minor version
test-hard/service:1              # Major version
test-hard/service:main-abc123    # Branch + commit
```

### Registry Configuration

**GitHub Container Registry (ghcr.io)**:

```yaml
# In .github/workflows/ci.yml
- name: Login to GHCR
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

## Secrets Management

### Required Secrets

**Repository Secrets**:
- `SLACK_WEBHOOK` - Slack notifications
- `DOCKER_PASSWORD` - Docker registry (if not using GHCR)
- `KUBECONFIG` - Kubernetes access (base64 encoded)

### Environment Secrets

**Staging**:
- `GF_ADMIN_PASSWORD`
- `GRAFANA_DOMAIN`

**Production**:
- `GF_ADMIN_PASSWORD`
- `GRAFANA_DOMAIN`
- `BACKUP_CREDENTIALS`

### Adding Secrets

```bash
# Via GitHub CLI
gh secret set SLACK_WEBHOOK --body "$WEBHOOK_URL"

# Via GitHub UI
Settings → Secrets and variables → Actions → New repository secret
```

## Monitoring CI/CD

### GitHub Actions Dashboard

View workflow runs:
```
https://github.com/[owner]/[repo]/actions
```

### Status Badges

Add to README.md:

```markdown
![CI](https://github.com/[owner]/[repo]/workflows/CI%20Pipeline/badge.svg)
![CD](https://github.com/[owner]/[repo]/workflows/CD%20Pipeline/badge.svg)
[![codecov](https://codecov.io/gh/[owner]/[repo]/branch/main/graph/badge.svg)](https://codecov.io/gh/[owner]/[repo])
```

### Notifications

**Slack Integration**:

```yaml
- name: Notify Slack
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
  if: always()
```

## Troubleshooting

### CI Failures

#### Lint Errors

```bash
# Fix automatically
make format

# Check what would change
make lint
```

#### Test Failures

```bash
# Run tests locally
make test-unit
make test-integration

# Check logs
docker compose logs
```

#### Build Failures

```bash
# Build locally
docker compose build

# Check specific service
docker compose build openscap-scanner
```

### CD Failures

#### Deployment Failed

1. Check workflow logs in GitHub Actions
2. Verify secrets are set correctly
3. Test deployment locally:
   ```bash
   make up-staging  # or up-prod
   ```

#### Rollback Production

```bash
# Via Git
git revert HEAD
git push

# Or restore from backup
./scripts/backup.sh
# Follow restore procedure
```

## Performance Optimization

### Cache Strategy

**Docker Build Cache**:
```yaml
- uses: actions/cache@v3
  with:
    path: /tmp/.buildx-cache
    key: ${{ runner.os }}-buildx-${{ github.sha }}
```

**Python Dependencies**:
```yaml
- uses: actions/setup-python@v5
  with:
    cache: 'pip'
```

**Pre-commit Hooks**:
```yaml
- uses: actions/cache@v3
  with:
    path: ~/.cache/pre-commit
    key: pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}
```

### Parallel Execution

Jobs run in parallel by default unless dependencies are specified:

```yaml
jobs:
  lint:
    # Runs independently
  
  test:
    needs: [lint]  # Waits for lint
```

## Best Practices

### Do

- Run `make ci` before pushing
- Write meaningful commit messages
- Keep CI fast (< 15 minutes)
- Use caching effectively
- Test deployments in staging first
- Monitor CI/CD metrics

### Don't

- Skip CI checks
- Commit broken code
- Push directly to main
- Ignore test failures
- Deploy without testing
- Hardcode secrets

## Metrics

Track these CI/CD metrics:

- **Build time**: < 10 minutes
- **Test pass rate**: > 95%
- **Deployment frequency**: Daily
- **Lead time**: < 1 hour
- **MTTR**: < 30 minutes
- **Change failure rate**: < 15%

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
