#!/usr/bin/env bash
# Semantic versioning bump script
set -euo pipefail

VERSION_FILE="VERSION"
BUMP_TYPE="${1:-patch}"

if [ ! -f "$VERSION_FILE" ]; then
    echo "1.0.0" > "$VERSION_FILE"
    echo "Created VERSION file: 1.0.0"
    exit 0
fi

current=$(cat "$VERSION_FILE")
IFS='.' read -r -a parts <<< "$current"

major="${parts[0]}"
minor="${parts[1]}"
patch="${parts[2]}"

case "$BUMP_TYPE" in
    major)
        major=$((major + 1))
        minor=0
        patch=0
        ;;
    minor)
        minor=$((minor + 1))
        patch=0
        ;;
    patch)
        patch=$((patch + 1))
        ;;
    *)
        echo "Usage: $0 {major|minor|patch}"
        exit 1
        ;;
esac

new_version="$major.$minor.$patch"
echo "$new_version" > "$VERSION_FILE"

echo "Version bumped: $current в†’ $new_version"
echo ""
echo "Next steps:"
echo "  1. Review changes: git diff"
echo "  2. Commit: git add VERSION && git commit -m 'chore: bump version to $new_version'"
echo "  3. Tag: git tag v$new_version"
echo "  4. Push: git push && git push --tags"
