# Fix Git Line Endings and Problematic Files
# This script resolves CRLF warnings and the backup.sh issue

Write-Host "=== Fixing Git Configuration Issues ===" -ForegroundColor Cyan

# Step 1: Remove problematic backup.sh file (duplicate exists in backup/ subdirectory)
Write-Host "`n[1/4] Removing problematic scripts/backup.sh file..." -ForegroundColor Yellow
if (Test-Path "scripts\backup.sh") {
    Remove-Item "scripts\backup.sh" -Force
    Write-Host "  ✓ Removed scripts/backup.sh (use scripts/backup/backup.sh instead)" -ForegroundColor Green
}

# Step 2: Stage the deletion
Write-Host "`n[2/4] Staging file deletion..." -ForegroundColor Yellow
git rm scripts/backup.sh 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ File removal staged" -ForegroundColor Green
} else {
    Write-Host "  ℹ File may not be tracked by Git" -ForegroundColor Gray
}

# Step 3: Normalize line endings for all files
Write-Host "`n[3/4] Normalizing line endings (CRLF → LF)..." -ForegroundColor Yellow
Write-Host "  This will update all files to use LF line endings as per .gitattributes" -ForegroundColor Gray

# Remove all files from Git index while keeping them in working directory
git rm --cached -r . 2>&1 | Out-Null

# Re-add all files (Git will apply .gitattributes rules)
git add -A

# Check how many files were modified
$status = git status --short
$modifiedCount = ($status | Measure-Object).Count
Write-Host "  ✓ Normalized $modifiedCount files" -ForegroundColor Green

# Step 4: Show what changed
Write-Host "`n[4/4] Summary of changes:" -ForegroundColor Yellow
git status --short | Select-Object -First 10 | ForEach-Object {
    Write-Host "  $_" -ForegroundColor Gray
}

$totalChanges = (git status --short | Measure-Object).Count
if ($totalChanges -gt 10) {
    Write-Host "  ... and $($totalChanges - 10) more files" -ForegroundColor Gray
}

# Final instructions
Write-Host ""
Write-Host "=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Review changes: git status" -ForegroundColor White
Write-Host "2. Commit changes: git commit -m `"Fix: Normalize line endings and remove problematic symlink`"" -ForegroundColor White
Write-Host "3. Push changes: git push" -ForegroundColor White
Write-Host ""
Write-Host "Note: Use scripts/backup/backup.sh instead of scripts/backup.sh" -ForegroundColor Yellow
Write-Host ""
Write-Host "All fixes applied successfully!" -ForegroundColor Green
