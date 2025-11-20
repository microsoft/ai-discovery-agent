#!/bin/bash
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

# Script to increment patch version, run checks, and prepare for release

set -e  # Exit on error

echo "🔧 Incrementing patch version in pyproject.toml..."

# Get current version and increment patch
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo "Current version: $CURRENT_VERSION"

# Split version into major.minor.patch
IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR="${VERSION_PARTS[0]}"
MINOR="${VERSION_PARTS[1]}"
PATCH="${VERSION_PARTS[2]}"

# Increment patch
NEW_PATCH=$((PATCH + 1))
NEW_VERSION="$MAJOR.$MINOR.$NEW_PATCH"

echo "New version: $NEW_VERSION"

# Update version in pyproject.toml
sed -i "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml

echo "✅ Version updated to $NEW_VERSION"

echo ""
echo "📝 Generating NOTICE file (runtime dependencies only)..."
./scripts/generate-notice.sh --no-dev

echo ""
echo "🔍 Running pre-commit hooks..."
uv run pre-commit run --all-files -c .tools/.pre-commit-config.yaml

echo ""
echo "🧹 Running Ruff linter..."
uv run ruff check .

echo ""
echo "🎨 Running Black formatter..."
uv run black .

echo ""
echo "©️ Checking copyright headers..."
./scripts/check-copyright-headers.sh

echo ""
echo "✨ All checks completed successfully!"
echo "Version bumped from $CURRENT_VERSION to $NEW_VERSION"
echo ""
echo "Next steps:"
echo "1. Review changes with: git diff"
echo "2. Commit changes: git add -A && git commit -m 'chore: bump version to $NEW_VERSION'"
echo "3. Create tag: git tag v$NEW_VERSION"
echo "4. Push changes: git push && git push --tags"