# CI Pipeline Fixes - Round 3: The Root Cause

## ✅ CRITICAL FIX - Telegraf Docker Build

### The Problem
```
ERROR: "/scripts/parsing/parse_atomic_red_team_result.py": not found
```

### Root Cause Identified
The `telegraf/Dockerfile.dockerignore` file was excluding all files except a whitelist, but the whitelist referenced the **OLD script path**:

**Before:**
```dockerignore
*
!telegraf/telegraf.conf
!scripts/parse_atomic_red_team_result.py  ← OLD PATH
```

**After:**
```dockerignore
*
!telegraf/telegraf.conf
!scripts/parsing/parse_atomic_red_team_result.py  ← NEW PATH
```

### Why This Happened
1. Scripts were reorganized into subdirectories (`scripts/parsing/`)
2. Dockerfile was updated to reference new path ✓
3. But `.dockerignore` still referenced old path ✗
4. `.dockerignore` excludes EVERYTHING (`*`) then whitelists specific files
5. New path wasn't whitelisted → file excluded from Docker build context → build failed

### Fix Applied
**Commit:** `7dc761a`
```
Fix: Update telegraf dockerignore for reorganized script paths
- Change scripts/parse_atomic_red_team_result.py to scripts/parsing/
```

**Status:** ✅ Fixed and pushed

---

## ⚠️ YAML Lint Errors (Need Fixing)

The YAML linter is now showing **specific errors** instead of failing silently.

### Error Categories

#### 1. Trailing Spaces (39 errors)
Files with trailing whitespace at end of lines:
- `docker-compose.prod.yml` (2 errors)
- `argocd/application-*.yaml` (15 errors)  
- `playbooks/scan-hosts.yml` (13 errors)
- `k8s/**/*.yaml` (0 direct trailing space errors shown)

**Fix:** Remove trailing whitespace from affected lines

#### 2. Indentation Errors (19 errors)
Wrong indentation in Kubernetes manifests:
- `k8s/base/grafana.yaml` (11 errors)
- `k8s/base/prometheus.yaml` (5 errors)
- `k8s/base/telegraf.yaml` (6 errors)
- `k8s/overlays/dev/*.yaml` (2 errors)

**Fix:** Correct YAML indentation (expecting 2-space increments)

#### 3. Document Start Warnings (21 warnings)
Files using `---` document start marker (discouraged by config):
- `.yamllint.yml`
- `playbooks/scan-hosts.yml`
- `k8s/**/*.yaml`

**Fix:** Either:
- Remove `---` markers, OR
- Update `.yamllint.yml` to allow them:
  ```yaml
  document-start:
    present: false  # Change to: present: true
  ```

#### 4. Line Length Warning (1 warning)
- `playbooks/scan-hosts.yml:77` - Line is 165 chars (limit: 120)

**Fix:** Break long line into multiple lines

#### 5. Comment Indentation (1 warning)
- `docker-compose.prod.yml:116` - Comment not aligned

---

## 🔍 Secret Scanning (Still Failing - Non-Critical)

```
Error: BASE and HEAD commits are the same
```

**Status:** Non-blocking workflow configuration issue

**Recommended Fix** (optional):
Update `.github/workflows/security-scan.yml` to skip when no changes:
```yaml
- name: TruffleHog scan
  if: github.event.before != '0000000000000000000000000000000000000000'
  uses: trufflesecurity/trufflehog@main
```

---

## Summary of All Fixes Applied

### Round 1: Script Path Updates
- ✅ Updated `telegraf/Dockerfile`
- ✅ Updated `docker/common/hardening-entrypoint.sh`
- ✅ Updated `playbooks/scan-hosts.yml`
- ✅ Updated `README.md`
- ✅ Updated `.github/workflows/cd.yml`

### Round 2: Docker Workflow Matrix
- ✅ Fixed `.github/workflows/docker-publish.yml` component names
- ✅ Removed non-existent `atomic-test`

### Round 3: Dockerignore Whitelist
- ✅ Fixed `telegraf/Dockerfile.dockerignore` path

---

## Next Steps

### High Priority: Fix YAML Lint
Run this to fix trailing spaces automatically:
```bash
# Remove trailing whitespace
find . -name "*.yml" -o -name "*.yaml" | xargs sed -i 's/[[:space:]]*$//'
```

Or manually fix:
1. Open each file with errors
2. Remove trailing spaces
3. Fix indentation in K8s manifests

### Optional: Configure Document Start
Update `.yamllint.yml`:
```yaml
document-start:
  present: true  # Allow --- markers
```

---

## Expected CI Results After This Fix

- ✅ **Docker Build (Telegraf)** - Should now succeed
- ✅ **Docker Build (Scanners)** - Already working
- ⚠️ **YAML Lint** - Will fail until trailing spaces/indentation fixed
- ⚠️ **Secret Scanning** - Will continue to fail (non-critical)
- ✅ **Code Quality** - Should pass
- ✅ **Security Scanning** - Should pass

---

## Files Modified in This Round

1. `telegraf/Dockerfile.dockerignore` - Updated script path in whitelist
2. `CI_FIXES_ROUND2.md` - Documentation (committed with this fix)

## Verification

Monitor: https://github.com/alexbergh/test-hard/actions

Expected: Telegraf Docker build should complete successfully now that the script is included in the build context.
