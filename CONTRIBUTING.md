# Contributing to test-hard

Thank you for considering contributing to this project.

## Getting Started

### Prerequisites

- Python 3.11+
- Podman and podman-compose
- pre-commit
- Make

### Development Setup

```bash
# Clone the repository
git clone https://github.com/alexbergh/test-hard.git
cd test-hard

# Install development dependencies
make install-dev

# Create environment file
make setup

# Run pre-commit hooks
pre-commit run --all-files
```

## Development Workflow

1. **Fork** the repository
2. **Create a branch** from `develop`: `git checkout -b feature/your-feature develop`
3. **Make changes** and add tests
4. **Run tests:** `make test-all`
5. **Run linters:** `pre-commit run --all-files`
6. **Commit** with a clear message (see Commit Convention below)
7. **Push** and open a Pull Request against `develop`

## Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new scanning capability
fix: resolve false positive in Lynis parser
docs: update deployment guide
chore: bump dependency versions
refactor: simplify metric extraction
test: add unit tests for OpenSCAP parser
ci: fix yamllint configuration
security: harden container capabilities
```

## Code Style

- **Python:** Enforced by Ruff (formatting and linting). Configuration in `pyproject.toml`.
- **Shell:** Validated by ShellCheck. Use `#!/usr/bin/env bash` shebangs.
- **YAML:** Validated by yamllint. Configuration in `.yamllint.yml`.
- **Containers:** Validated by hadolint. Use `Containerfile` (not `Dockerfile`).
- **No emojis** in code, documentation, or output.

## Testing

```bash
make test-unit          # Unit tests only
make test-integration   # Integration tests (requires Podman)
make test-all           # All tests
make coverage           # Tests with coverage report
```

### Test Structure

- `tests/unit/` -- Pure Python tests, no external dependencies
- `tests/integration/` -- Tests requiring running containers

## Project Structure

| Directory | Purpose |
|-----------|---------|
| `scripts/` | Scanning and parsing scripts |
| `dashboard/` | FastAPI backend + React frontend |
| `k8s/` | Kubernetes manifests (base + overlays) |
| `prometheus/` | Prometheus and Alertmanager configs |
| `grafana/` | Dashboards and datasource configs |
| `scanners/` | Scanner container entrypoints |
| `tests/` | Unit and integration tests |
| `.github/workflows/` | CI/CD pipelines |

## Pull Request Guidelines

- Target the `develop` branch (not `main`)
- Include tests for new functionality
- Update documentation if behavior changes
- Ensure all CI checks pass
- Keep PRs focused on a single concern

## Security

If you find a security vulnerability, please follow the process
described in [SECURITY.md](SECURITY.md). Do not open a public issue.
