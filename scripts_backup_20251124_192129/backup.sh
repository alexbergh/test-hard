#!/usr/bin/env bash
# Backup script for test-hard monitoring platform
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="test-hard-backup-$TIMESTAMP"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

error() {
    echo "[ERROR] $*" >&2
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

log "Starting backup: $BACKUP_NAME"

# Create temporary backup directory
TEMP_BACKUP="$BACKUP_DIR/$BACKUP_NAME"
mkdir -p "$TEMP_BACKUP"

# Backup configuration files
log "Backing up configuration files..."
mkdir -p "$TEMP_BACKUP/config"
cp -r "$PROJECT_ROOT/.env" "$TEMP_BACKUP/config/" 2>/dev/null || log "[WARN] No .env file found"
cp -r "$PROJECT_ROOT/docker-compose.yml" "$TEMP_BACKUP/config/"
cp -r "$PROJECT_ROOT/prometheus" "$TEMP_BACKUP/config/"
cp -r "$PROJECT_ROOT/grafana/provisioning" "$TEMP_BACKUP/config/"
cp -r "$PROJECT_ROOT/telegraf" "$TEMP_BACKUP/config/"
cp -r "$PROJECT_ROOT/atomic-red-team" "$TEMP_BACKUP/config/"
log "[OK] Configuration files backed up"

# Backup Prometheus data
if [ -d "$PROJECT_ROOT/prometheus-data" ]; then
    log "Backing up Prometheus data..."
    cp -r "$PROJECT_ROOT/prometheus-data" "$TEMP_BACKUP/"
    log "[OK] Prometheus data backed up"
else
    log "[WARN] No Prometheus data found (docker volume)"
fi

# Backup Grafana data
if [ -d "$PROJECT_ROOT/grafana-data" ]; then
    log "Backing up Grafana data..."
    cp -r "$PROJECT_ROOT/grafana-data" "$TEMP_BACKUP/"
    log "[OK] Grafana data backed up"
else
    log "[WARN] No Grafana data found (docker volume)"
fi

# Backup reports
if [ -d "$PROJECT_ROOT/reports" ]; then
    log "Backing up reports..."
    cp -r "$PROJECT_ROOT/reports" "$TEMP_BACKUP/"
    log "[OK] Reports backed up"
fi

# Backup Atomic Red Team results
if [ -d "$PROJECT_ROOT/art-storage" ]; then
    log "Backing up Atomic Red Team results..."
    cp -r "$PROJECT_ROOT/art-storage" "$TEMP_BACKUP/"
    log "[OK] ART results backed up"
fi

# Export Docker volumes if they exist
log "Exporting Docker volumes..."
COMPOSE_BIN="${COMPOSE_BIN:-docker compose}"

if $COMPOSE_BIN ps prometheus >/dev/null 2>&1; then
    log "Exporting Prometheus volume..."
    docker run --rm \
        -v test-hard_prometheus-data:/data \
        -v "$TEMP_BACKUP":/backup \
        alpine tar czf /backup/prometheus-volume.tar.gz -C /data . 2>/dev/null || \
        log "[WARN] Failed to export Prometheus volume"
fi

if $COMPOSE_BIN ps grafana >/dev/null 2>&1; then
    log "Exporting Grafana volume..."
    docker run --rm \
        -v test-hard_grafana-data:/data \
        -v "$TEMP_BACKUP":/backup \
        alpine tar czf /backup/grafana-volume.tar.gz -C /data . 2>/dev/null || \
        log "[WARN] Failed to export Grafana volume"
fi

# Create metadata file
log "Creating backup metadata..."
cat > "$TEMP_BACKUP/metadata.txt" <<EOF
Backup Name: $BACKUP_NAME
Timestamp: $TIMESTAMP
Date: $(date)
Hostname: $(hostname)
Docker Version: $(docker --version)
Docker Compose Version: $($COMPOSE_BIN version --short 2>/dev/null || echo "unknown")
Project Path: $PROJECT_ROOT
EOF

# Create tarball
log "Creating backup archive..."
cd "$BACKUP_DIR"
tar czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME"

# Remove temporary directory
rm -rf "$TEMP_BACKUP"

# Calculate size
BACKUP_SIZE=$(du -h "$BACKUP_NAME.tar.gz" | awk '{print $1}')

log ""
log "[SUCCESS] Backup completed successfully!"
log "  Archive: $BACKUP_DIR/$BACKUP_NAME.tar.gz"
log "  Size: $BACKUP_SIZE"
log ""

# Optional: Keep only last N backups
KEEP_BACKUPS="${KEEP_BACKUPS:-5}"
if [ "$KEEP_BACKUPS" -gt 0 ]; then
    log "Cleaning up old backups (keeping last $KEEP_BACKUPS)..."
    cd "$BACKUP_DIR"
    ls -t test-hard-backup-*.tar.gz 2>/dev/null | tail -n +$((KEEP_BACKUPS + 1)) | xargs rm -f
    log "[OK] Cleanup complete"
fi

log ""
log "To restore this backup:"
log "  tar xzf $BACKUP_DIR/$BACKUP_NAME.tar.gz -C /tmp"
log "  cd /tmp/$BACKUP_NAME"
log "  # Review and copy files as needed"
log ""
