# Start script for test-hard platform on Windows (Podman)
# podman-proxy is started separately because podman-compose on Windows
# mangles Unix socket paths (/run/podman/podman.sock -> /mnt/c/run/...)

Write-Host "=== Starting test-hard platform ===" -ForegroundColor Cyan

# 1. Create networks (ignore errors if they already exist)
Write-Host "[1/4] Creating networks..." -ForegroundColor Yellow
podman network create test-hard_default 2>$null
podman network create test-hard_scanner-net 2>$null

# 2. Start podman-proxy manually with correct socket mount
Write-Host "[2/4] Starting podman-proxy..." -ForegroundColor Yellow
podman rm -f podman-proxy 2>$null
podman run -d --name podman-proxy `
  --network test-hard_default `
  -e CONTAINERS=1 -e EXEC=1 -e IMAGES=1 -e INFO=1 `
  -e NETWORKS=1 -e VOLUMES=1 -e POST=1 `
  -e SERVICES=1 -e TASKS=1 -e VERSION=1 `
  -v /run/podman/podman.sock:/var/run/docker.sock:ro `  # Proxy expects this path
  tecnativa/docker-socket-proxy:0.1.2  # External image name

# Connect podman-proxy to scanner-net as well
podman network connect test-hard_scanner-net podman-proxy 2>$null

# Wait for proxy to initialize
Start-Sleep -Seconds 3

# 3. Start all compose services
Write-Host "[3/4] Starting compose services..." -ForegroundColor Yellow
podman-compose up -d

# 4. Verify
Write-Host "[4/4] Checking status..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
podman ps --format "table {{.Names}}\t{{.Status}}"

Write-Host "`n=== Platform started ===" -ForegroundColor Green
