#!/bin/bash
set -euo pipefail

# Run shell script tests with bats

echo "🧪 Running shell script tests with bats..."

# Check if bats is installed
if ! command -v bats &> /dev/null; then
    echo "❌ bats is not installed"
    echo "Install with: brew install bats-core (macOS) or apt-get install bats (Linux)"
    exit 1
fi

# Run bats tests
if [ -d "tests/shell" ]; then
    echo "Running bats tests from tests/shell/..."
    bats tests/shell/*.bats
    echo "✅ Shell tests completed"
else
    echo "⚠️  No shell tests found in tests/shell/"
    exit 0
fi
