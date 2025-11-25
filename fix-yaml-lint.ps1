# Fix YAML linting errors
Write-Host "Fixing YAML lint errors..." -ForegroundColor Cyan

# Get all YAML files
$yamlFiles = Get-ChildItem -Recurse -Include *.yml,*.yaml | Where-Object { 
    $_.FullName -notmatch '\\node_modules\\' -and 
    $_.FullName -notmatch '\\venv\\' -and
    $_.FullName -notmatch '\\build\\' -and
    $_.FullName -notmatch '\\.git\\'
}

Write-Host "`nRemoving trailing whitespace from $($yamlFiles.Count) YAML files..." -ForegroundColor Yellow

$fixedCount = 0
foreach ($file in $yamlFiles) {
    $content = Get-Content $file.FullName -Raw
    $newContent = $content -replace '[ \t]+(\r?\n)', '$1'
    
    if ($content -ne $newContent) {
        Set-Content -Path $file.FullName -Value $newContent -NoNewline
        Write-Host "  Fixed: $($file.Name)" -ForegroundColor Green
        $fixedCount++
    }
}

Write-Host "`nFixed $fixedCount files" -ForegroundColor Green
Write-Host "`nRemaining issues to fix manually:" -ForegroundColor Yellow
Write-Host "- Indentation errors in k8s manifests (19 errors)" -ForegroundColor Gray
Write-Host "- Line length in playbooks/scan-hosts.yml:77 (165 > 120 chars)" -ForegroundColor Gray
Write-Host "- Document start warnings (optional - can be ignored)" -ForegroundColor Gray
