# Git Line Ending and File Issues - Fix Instructions

## Problem Summary
1. **CRLF to LF warnings**: Files have Windows line endings (CRLF) but `.gitattributes` enforces Unix line endings (LF)
2. **scripts/backup.sh error**: This file is problematic and should be removed (duplicate exists at `scripts/backup/backup.sh`)

## Solution

Run these commands in PowerShell from the repository root:

### Step 1: Remove problematic file
```powershell
# Remove the problematic backup.sh file (duplicate exists in backup/ subdirectory)
del scripts\backup.sh
git rm scripts/backup.sh
```

### Step 2: Normalize all line endings
```powershell
# Remove all files from Git index (keeping them in working directory)
git rm --cached -r .

# Re-add all files - Git will apply .gitattributes rules and convert CRLF to LF
git add -A

# Check what changed
git status
```

### Step 3: Commit the changes
```powershell
git commit -m "Fix: Normalize line endings and remove problematic symlink"
```

### Step 4: Push changes
```powershell
git push
```

## What This Does

1. **Removes duplicate file**: `scripts/backup.sh` is removed. Use `scripts/backup/backup.sh` instead
2. **Normalizes line endings**: All text files are converted from CRLF (Windows) to LF (Unix) as per `.gitattributes`
3. **Resolves warnings**: After committing, the CRLF warnings will disappear

## Note

- The warnings are expected behavior when Git normalizes line endings
- Your `.gitattributes` is properly configured with `eol=lf` for consistency across platforms
- After these changes, new files will automatically use LF line endings
