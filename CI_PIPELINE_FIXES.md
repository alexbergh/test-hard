# CI Pipeline Fixes - Script Path Updates

## Problem
CI pipeline was failing because Dockerfiles and configuration files referenced old script paths that no longer existed after the script reorganization.

**Error Example:**
```
ERROR: failed to build: failed to solve: failed to compute cache key: 
"/scripts/parse_atomic_red_team_result.py": not found
```

## Root Cause
Scripts were reorganized into subdirectories:
- `scripts/parsing/` - Parser scripts
- `scripts/scanning/` - Security scanning scripts  
- `scripts/setup/` - Installation scripts
- `scripts/backup/` - Backup utilities
- `scripts/monitoring/` - Monitoring scripts
- `scripts/testing/` - Test scripts
- `scripts/utils/` - Utility scripts

But several files still referenced the old flat structure.

## Files Fixed

### 1. `telegraf/Dockerfile`
**Changed:**
```dockerfile
- COPY scripts/parse_atomic_red_team_result.py /opt/hardening/scripts/parse_atomic_red_team_result.py
+ COPY scripts/parsing/parse_atomic_red_team_result.py /opt/hardening/scripts/parse_atomic_red_team_result.py
```

### 2. `docker/common/hardening-entrypoint.sh`
**Changed:**
```bash
- if ! /opt/hardening/scripts/run_all_checks.sh; then
+ if ! /opt/hardening/scripts/scanning/run_all_checks.sh; then
```

### 3. `playbooks/scan-hosts.yml`
**Changed:**
```yaml
- cmd: "python3 scripts/parse_lynis_report.py {{ reports_dir }}/{{ inventory_hostname }}.log > ..."
+ cmd: "python3 scripts/parsing/parse_lynis_report.py {{ reports_dir }}/{{ inventory_hostname }}.log > ..."
```

### 4. `.github/workflows/cd.yml`
**Changed (comment only):**
```yaml
- # Example: ./scripts/backup.sh
+ # Example: ./scripts/backup/backup.sh
```

### 5. `README.md`
**Updated all script references:**
- `scripts/run_hardening_suite.sh` → `scripts/scanning/run_hardening_suite.sh`
- `scripts/run_lynis.sh` → `scripts/scanning/run_lynis.sh`
- `scripts/parse_lynis_report.py` → `scripts/parsing/parse_lynis_report.py`
- `scripts/run_openscap.sh` → `scripts/scanning/run_openscap.sh`
- `scripts/parse_openscap_report.py` → `scripts/parsing/parse_openscap_report.py`
- `scripts/run_atomic_red_team_test.sh` → `scripts/scanning/run_atomic_red_team_test.sh`
- `scripts/run_atomic_red_team_suite.py` → `scripts/scanning/run_atomic_red_team_suite.py`
- `scripts/parse_atomic_red_team_result.py` → `scripts/parsing/parse_atomic_red_team_result.py`

## Script Organization Reference

```
scripts/
├── backup/
│   └── backup.sh
├── monitoring/
│   ├── health_check.sh
│   └── measure_docker_improvements.sh
├── parsing/
│   ├── parse_atomic_red_team_result.py
│   ├── parse_lynis_log.py
│   ├── parse_lynis_report.py
│   └── parse_openscap_report.py
├── scanning/
│   ├── run_all_checks.sh
│   ├── run_atomic_red_team_suite.py
│   ├── run_atomic_red_team_test.sh
│   ├── run_hardening_suite.sh
│   ├── run_lynis.sh
│   ├── run_openscap.sh
│   └── scan-remote-host.sh
├── setup/
│   ├── install-deps.sh
│   └── setup-secure-user.sh
├── testing/
│   ├── run_shell_tests.sh
│   ├── test-core-functionality.sh
│   └── verify_fixes.sh
└── utils/
    └── bump-version.sh
```

## Next Steps

1. **Commit changes:**
   ```bash
   git commit -m "Fix: Update script paths in Dockerfile, configs, and docs

   - Update telegraf/Dockerfile to use scripts/parsing/
   - Update hardening-entrypoint.sh to use scripts/scanning/
   - Update Ansible playbook to use scripts/parsing/
   - Update README.md with all new script paths
   - Update CI/CD workflow comments

   Resolves CI pipeline build failures caused by script reorganization"
   ```

2. **Push and verify CI:**
   ```bash
   git push
   ```

3. **Monitor CI pipeline** to ensure Docker builds succeed

## Status
✓ All script path references updated
✓ Documentation updated
✓ Changes staged for commit
✓ Ready to push
