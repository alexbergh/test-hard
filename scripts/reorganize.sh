#!/bin/bash
# Script to reorganize scripts/ directory structure
# Run with: bash scripts/reorganize.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

error() {
    echo "[ERROR] $*" >&2
    exit 1
}

# Check if we're in the right directory
if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    error "Must be run from project root or scripts directory"
fi

log "Starting scripts reorganization..."

# Create new directory structure
log "Creating directory structure..."
mkdir -p "$SCRIPT_DIR/setup"
mkdir -p "$SCRIPT_DIR/scanning"
mkdir -p "$SCRIPT_DIR/parsing"
mkdir -p "$SCRIPT_DIR/monitoring"
mkdir -p "$SCRIPT_DIR/backup"
mkdir -p "$SCRIPT_DIR/testing"
mkdir -p "$SCRIPT_DIR/utils"

# Backup current structure
BACKUP_DIR="$PROJECT_ROOT/scripts_backup_$(date +%Y%m%d_%H%M%S)"
log "Creating backup at $BACKUP_DIR"
cp -r "$SCRIPT_DIR" "$BACKUP_DIR"

# Move files to new locations
log "Moving files to new structure..."

# setup/
mv "$SCRIPT_DIR/install-deps.sh" "$SCRIPT_DIR/setup/" 2>/dev/null || true
mv "$SCRIPT_DIR/setup-secure-user.sh" "$SCRIPT_DIR/setup/" 2>/dev/null || true

# scanning/
mv "$SCRIPT_DIR/run_lynis.sh" "$SCRIPT_DIR/scanning/" 2>/dev/null || true
mv "$SCRIPT_DIR/run_openscap.sh" "$SCRIPT_DIR/scanning/" 2>/dev/null || true
mv "$SCRIPT_DIR/run_atomic_red_team_test.sh" "$SCRIPT_DIR/scanning/" 2>/dev/null || true
mv "$SCRIPT_DIR/run_atomic_red_team_suite.py" "$SCRIPT_DIR/scanning/" 2>/dev/null || true
mv "$SCRIPT_DIR/run_hardening_suite.sh" "$SCRIPT_DIR/scanning/" 2>/dev/null || true
mv "$SCRIPT_DIR/run_all_checks.sh" "$SCRIPT_DIR/scanning/" 2>/dev/null || true
mv "$SCRIPT_DIR/scan-remote-host.sh" "$SCRIPT_DIR/scanning/" 2>/dev/null || true

# parsing/
mv "$SCRIPT_DIR/parse_lynis_log.py" "$SCRIPT_DIR/parsing/" 2>/dev/null || true
mv "$SCRIPT_DIR/parse_lynis_report.py" "$SCRIPT_DIR/parsing/" 2>/dev/null || true
mv "$SCRIPT_DIR/parse_openscap_report.py" "$SCRIPT_DIR/parsing/" 2>/dev/null || true
mv "$SCRIPT_DIR/parse_atomic_red_team_result.py" "$SCRIPT_DIR/parsing/" 2>/dev/null || true

# monitoring/
mv "$SCRIPT_DIR/health_check.sh" "$SCRIPT_DIR/monitoring/" 2>/dev/null || true
mv "$SCRIPT_DIR/measure_docker_improvements.sh" "$SCRIPT_DIR/monitoring/" 2>/dev/null || true

# backup/
mv "$SCRIPT_DIR/backup.sh" "$SCRIPT_DIR/backup/" 2>/dev/null || true

# testing/
mv "$SCRIPT_DIR/test-core-functionality.sh" "$SCRIPT_DIR/testing/" 2>/dev/null || true
mv "$SCRIPT_DIR/run_shell_tests.sh" "$SCRIPT_DIR/testing/" 2>/dev/null || true
mv "$SCRIPT_DIR/verify_fixes.sh" "$SCRIPT_DIR/testing/" 2>/dev/null || true

# utils/
mv "$SCRIPT_DIR/bump-version.sh" "$SCRIPT_DIR/utils/" 2>/dev/null || true

# Create symbolic links for backward compatibility
log "Creating symbolic links for backward compatibility..."
cd "$SCRIPT_DIR"

# setup/
ln -sf setup/install-deps.sh install-deps.sh 2>/dev/null || true
ln -sf setup/setup-secure-user.sh setup-secure-user.sh 2>/dev/null || true

# scanning/
ln -sf scanning/run_lynis.sh run_lynis.sh 2>/dev/null || true
ln -sf scanning/run_openscap.sh run_openscap.sh 2>/dev/null || true
ln -sf scanning/run_atomic_red_team_test.sh run_atomic_red_team_test.sh 2>/dev/null || true
ln -sf scanning/run_atomic_red_team_suite.py run_atomic_red_team_suite.py 2>/dev/null || true
ln -sf scanning/run_hardening_suite.sh run_hardening_suite.sh 2>/dev/null || true
ln -sf scanning/run_all_checks.sh run_all_checks.sh 2>/dev/null || true
ln -sf scanning/scan-remote-host.sh scan-remote-host.sh 2>/dev/null || true

# parsing/
ln -sf parsing/parse_lynis_log.py parse_lynis_log.py 2>/dev/null || true
ln -sf parsing/parse_lynis_report.py parse_lynis_report.py 2>/dev/null || true
ln -sf parsing/parse_openscap_report.py parse_openscap_report.py 2>/dev/null || true
ln -sf parsing/parse_atomic_red_team_result.py parse_atomic_red_team_result.py 2>/dev/null || true

# monitoring/
ln -sf monitoring/health_check.sh health_check.sh 2>/dev/null || true
ln -sf monitoring/measure_docker_improvements.sh measure_docker_improvements.sh 2>/dev/null || true

# backup/
ln -sf backup/backup.sh backup.sh 2>/dev/null || true

# testing/
ln -sf testing/test-core-functionality.sh test-core-functionality.sh 2>/dev/null || true
ln -sf testing/run_shell_tests.sh run_shell_tests.sh 2>/dev/null || true
ln -sf testing/verify_fixes.sh verify_fixes.sh 2>/dev/null || true

# utils/
ln -sf utils/bump-version.sh bump-version.sh 2>/dev/null || true

# Create README files for each category
log "Creating category README files..."

cat > "$SCRIPT_DIR/setup/README.md" << 'EOF'
# Setup Scripts

РЎРєСЂРёРїС‚С‹ РґР»СЏ СѓСЃС‚Р°РЅРѕРІРєРё Рё РїРµСЂРІРѕРЅР°С‡Р°Р»СЊРЅРѕР№ РЅР°СЃС‚СЂРѕР№РєРё СЃРёСЃС‚РµРјС‹.

## Р¤Р°Р№Р»С‹

- `install-deps.sh` - РЈСЃС‚Р°РЅРѕРІРєР° Python Р·Р°РІРёСЃРёРјРѕСЃС‚РµР№ Рё pre-commit hooks
- `setup-secure-user.sh` - РЎРѕР·РґР°РЅРёРµ Р±РµР·РѕРїР°СЃРЅС‹С… РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№ РґР»СЏ СЃРєР°РЅРёСЂРѕРІР°РЅРёСЏ
EOF

cat > "$SCRIPT_DIR/scanning/README.md" << 'EOF'
# Scanning Scripts

РЎРєСЂРёРїС‚С‹ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ security СЃРєР°РЅРёСЂРѕРІР°РЅРёСЏ.

## Р¤Р°Р№Р»С‹

- `run_lynis.sh` - Р—Р°РїСѓСЃРє Lynis СЃРєР°РЅРёСЂРѕРІР°РЅРёСЏ
- `run_openscap.sh` - Р—Р°РїСѓСЃРє OpenSCAP СЃРєР°РЅРёСЂРѕРІР°РЅРёСЏ
- `run_atomic_red_team_test.sh` - Р—Р°РїСѓСЃРє Atomic Red Team С‚РµСЃС‚РѕРІ
- `run_atomic_red_team_suite.py` - Python РѕР±РµСЂС‚РєР° РґР»СЏ ART С‚РµСЃС‚РѕРІ
- `run_hardening_suite.sh` - Р—Р°РїСѓСЃРє РїРѕР»РЅРѕРіРѕ РЅР°Р±РѕСЂР° РїСЂРѕРІРµСЂРѕРє
- `run_all_checks.sh` - Р—Р°РїСѓСЃРє РІСЃРµС… РІРёРґРѕРІ СЃРєР°РЅРёСЂРѕРІР°РЅРёСЏ
- `scan-remote-host.sh` - РЎРєР°РЅРёСЂРѕРІР°РЅРёРµ СѓРґР°Р»РµРЅРЅС‹С… С…РѕСЃС‚РѕРІ РїРѕ SSH
EOF

cat > "$SCRIPT_DIR/parsing/README.md" << 'EOF'
# Parsing Scripts

РџР°СЂСЃРµСЂС‹ РґР»СЏ РѕР±СЂР°Р±РѕС‚РєРё РѕС‚С‡РµС‚РѕРІ СЃРєР°РЅРёСЂРѕРІР°РЅРёСЏ Рё РєРѕРЅРІРµСЂС‚Р°С†РёРё РІ Prometheus РјРµС‚СЂРёРєРё.

## Р¤Р°Р№Р»С‹

- `parse_lynis_log.py` - РџР°СЂСЃРёРЅРі Lynis Р»РѕРіРѕРІ
- `parse_lynis_report.py` - РџР°СЂСЃРёРЅРі Lynis РѕС‚С‡РµС‚РѕРІ
- `parse_openscap_report.py` - РџР°СЂСЃРёРЅРі OpenSCAP XML РѕС‚С‡РµС‚РѕРІ
- `parse_atomic_red_team_result.py` - РџР°СЂСЃРёРЅРі СЂРµР·СѓР»СЊС‚Р°С‚РѕРІ Atomic Red Team
EOF

cat > "$SCRIPT_DIR/monitoring/README.md" << 'EOF'
# Monitoring Scripts

РЎРєСЂРёРїС‚С‹ РґР»СЏ РјРѕРЅРёС‚РѕСЂРёРЅРіР° Рё РїСЂРѕРІРµСЂРєРё Р·РґРѕСЂРѕРІСЊСЏ СЃРёСЃС‚РµРјС‹.

## Р¤Р°Р№Р»С‹

- `health_check.sh` - РџСЂРѕРІРµСЂРєР° Р·РґРѕСЂРѕРІСЊСЏ РІСЃРµС… СЃРµСЂРІРёСЃРѕРІ
- `measure_docker_improvements.sh` - РР·РјРµСЂРµРЅРёРµ СѓР»СѓС‡С€РµРЅРёР№ Docker СЃР±РѕСЂРєРё
EOF

cat > "$SCRIPT_DIR/backup/README.md" << 'EOF'
# Backup Scripts

РЎРєСЂРёРїС‚С‹ РґР»СЏ СЂРµР·РµСЂРІРЅРѕРіРѕ РєРѕРїРёСЂРѕРІР°РЅРёСЏ Рё РІРѕСЃСЃС‚Р°РЅРѕРІР»РµРЅРёСЏ.

## Р¤Р°Р№Р»С‹

- `backup.sh` - РЎРѕР·РґР°РЅРёРµ backup РєРѕРЅС„РёРіСѓСЂР°С†РёРё Рё РґР°РЅРЅС‹С…
EOF

cat > "$SCRIPT_DIR/testing/README.md" << 'EOF'
# Testing Scripts

РЎРєСЂРёРїС‚С‹ РґР»СЏ С‚РµСЃС‚РёСЂРѕРІР°РЅРёСЏ С„СѓРЅРєС†РёРѕРЅР°Р»СЊРЅРѕСЃС‚Рё РїР»Р°С‚С„РѕСЂРјС‹.

## Р¤Р°Р№Р»С‹

- `test-core-functionality.sh` - РўРµСЃС‚ РѕСЃРЅРѕРІРЅРѕР№ С„СѓРЅРєС†РёРѕРЅР°Р»СЊРЅРѕСЃС‚Рё
- `run_shell_tests.sh` - Р—Р°РїСѓСЃРє bats С‚РµСЃС‚РѕРІ
- `verify_fixes.sh` - РџСЂРѕРІРµСЂРєР° РїСЂРёРјРµРЅРµРЅРЅС‹С… РёСЃРїСЂР°РІР»РµРЅРёР№
EOF

cat > "$SCRIPT_DIR/utils/README.md" << 'EOF'
# Utility Scripts

Р’СЃРїРѕРјРѕРіР°С‚РµР»СЊРЅС‹Рµ СѓС‚РёР»РёС‚С‹.

## Р¤Р°Р№Р»С‹

- `bump-version.sh` - РћР±РЅРѕРІР»РµРЅРёРµ РІРµСЂСЃРёРё РїСЂРѕРµРєС‚Р°
EOF

# Update main scripts README
cat > "$SCRIPT_DIR/README.md" << 'EOF'
# Scripts Directory

РЎРєСЂРёРїС‚С‹ РїСЂРѕРµРєС‚Р° РѕСЂРіР°РЅРёР·РѕРІР°РЅС‹ РїРѕ РєР°С‚РµРіРѕСЂРёСЏРј РґР»СЏ СѓР»СѓС‡С€РµРЅРёСЏ РЅР°РІРёРіР°С†РёРё.

## РЎС‚СЂСѓРєС‚СѓСЂР°

```
scripts/
в”њв”Ђв”Ђ setup/          # РЈСЃС‚Р°РЅРѕРІРєР° Рё РЅР°СЃС‚СЂРѕР№РєР°
в”њв”Ђв”Ђ scanning/       # РЎРєСЂРёРїС‚С‹ СЃРєР°РЅРёСЂРѕРІР°РЅРёСЏ
в”њв”Ђв”Ђ parsing/        # РџР°СЂСЃРµСЂС‹ РѕС‚С‡РµС‚РѕРІ
в”њв”Ђв”Ђ monitoring/     # РњРѕРЅРёС‚РѕСЂРёРЅРі Рё health checks
в”њв”Ђв”Ђ backup/         # Backup Рё restore
в”њв”Ђв”Ђ testing/        # РўРµСЃС‚РёСЂРѕРІР°РЅРёРµ
в””в”Ђв”Ђ utils/          # РЈС‚РёР»РёС‚С‹
```

## РћР±СЂР°С‚РЅР°СЏ СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚СЊ

Р’ РєРѕСЂРЅРµ `scripts/` РЅР°С…РѕРґСЏС‚СЃСЏ СЃРёРјРІРѕР»РёС‡РµСЃРєРёРµ СЃСЃС‹Р»РєРё РЅР° С„Р°Р№Р»С‹ РІ РїРѕРґРєР°С‚Р°Р»РѕРіР°С…
РґР»СЏ РѕР±РµСЃРїРµС‡РµРЅРёСЏ РѕР±СЂР°С‚РЅРѕР№ СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚Рё. Р РµРєРѕРјРµРЅРґСѓРµС‚СЃСЏ РѕР±РЅРѕРІРёС‚СЊ СЃСЃС‹Р»РєРё
РЅР° РЅРѕРІС‹Рµ РїСѓС‚Рё.

## РСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ

```bash
# РЎС‚Р°СЂС‹Р№ РїСѓС‚СЊ (СЂР°Р±РѕС‚Р°РµС‚ С‡РµСЂРµР· symlink)
./scripts/health_check.sh

# РќРѕРІС‹Р№ РїСѓС‚СЊ (СЂРµРєРѕРјРµРЅРґСѓРµС‚СЃСЏ)
./scripts/monitoring/health_check.sh
```

## РњРёРіСЂР°С†РёСЏ

РЎРј. [REORGANIZATION_PLAN.md](REORGANIZATION_PLAN.md) РґР»СЏ РґРµС‚Р°Р»РµР№ СЂРµРѕСЂРіР°РЅРёР·Р°С†РёРё.
EOF

log ""
log "[SUCCESS] Reorganization complete!"
log ""
log "Summary:"
log "  - Created new directory structure"
log "  - Moved files to appropriate categories"
log "  - Created symbolic links for backward compatibility"
log "  - Created README files for each category"
log "  - Backup created at: $BACKUP_DIR"
log ""
log "Next steps:"
log "  1. Test that everything works: make test"
log "  2. Update Makefile references to new paths"
log "  3. Update documentation"
log "  4. After testing, remove symbolic links (in future release)"
log ""
