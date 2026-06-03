# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x.x   | Yes       |
| < 1.0   | No        |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it
responsibly. **Do not open a public GitHub issue.**

### How to Report

1. **Email:** Send a detailed description to the project maintainer via
   GitHub private vulnerability reporting (Settings > Security > Advisories).
2. **GitHub Security Advisories:** Use the "Report a vulnerability" button
   on the Security tab of this repository.

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Affected components (scripts, containers, K8s manifests, dashboard, etc.)
- Potential impact assessment
- Suggested fix (if available)

### Response Timeline

- **Acknowledgment:** Within 48 hours
- **Initial assessment:** Within 5 business days
- **Fix for critical issues:** Within 14 days
- **Fix for high issues:** Within 30 days

### Scope

The following are in scope for security reports:

- Container security (Containerfile, podman-compose configurations)
- Kubernetes manifests and RBAC policies
- Python backend code (dashboard, scanning scripts)
- Secrets management (`.env`, `.secrets` handling)
- CI/CD pipeline security (GitHub Actions workflows)
- Authentication and authorization in the dashboard API
- Network policies and service isolation

### Out of Scope

- Third-party dependencies (report to upstream maintainers)
- Vulnerabilities in base container images (Fedora, Debian, Ubuntu, CentOS)
- Issues that require physical access to the host system
- Social engineering attacks

## Security Practices

This project follows these security practices:

- **No hardcoded secrets:** All credentials use environment variables or
  placeholder values
- **Container isolation:** Scanners use capability-based permissions instead
  of privileged mode
- **Network segmentation:** Kubernetes NetworkPolicies restrict inter-service
  communication
- **Automated scanning:** Trivy, CodeQL, Bandit, and TruffleHog run in CI
- **Dependency management:** Dependabot monitors for vulnerable dependencies
- **Image signing:** Container images are signed with Cosign via Sigstore
- **SBOM generation:** CycloneDX and SPDX SBOMs are generated for every release
