#!/bin/bash
set -euo pipefail

# Run shell script tests with bats

echo "[TEST] Running shell script tests with bats..."

# Check if bats is installed
if ! command -v bats &> /dev/null; then
    echo "[ERROR] bats is not installed"
    echo "Install with: brew install bats-core (macOS) or apt-get install bats (Linux)"
    exit 1
fi

# Run bats tests
if [ -d "tests/shell" ]; then
    echo "Running bats tests from tests/shell/..."
    bats tests/shell/*.bats
    echo "[SUCCESS] Shell tests completed"
else
    echo "[WARN] No shell tests found in tests/shell/"
    exit 0
fi
