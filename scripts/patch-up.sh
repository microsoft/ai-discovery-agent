#!/bin/bash
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

# Ensure script is run from project root
if [[ ! -f "pyproject.toml" ]]; then
    echo "Error: This script must be run from the project root directory"
    exit 1
fi

# Script to increment patch version, run checks, and prepare for release

echo "🔧 Incrementing patch version in pyproject.toml..."

# Get current version and increment patch
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo "Current version: $CURRENT_VERSION"

# Validate semantic versioning format (X.Y.Z)
if ! echo "$CURRENT_VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
    echo "Error: Version '$CURRENT_VERSION' does not follow semantic versioning (X.Y.Z)"
    exit 1
fi

# Split version into major.minor.patch
IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR="${VERSION_PARTS[0]}"
MINOR="${VERSION_PARTS[1]}"
PATCH="${VERSION_PARTS[2]}"

# Increment patch
NEW_PATCH=$((PATCH + 1))
NEW_VERSION="$MAJOR.$MINOR.$NEW_PATCH"

echo "New version: $NEW_VERSION"

# Update version in pyproject.toml (portable across macOS and Linux)
sed "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml > pyproject.toml.tmp && mv pyproject.toml.tmp pyproject.toml

echo "✅ Version updated to $NEW_VERSION"

echo ""
echo "📝 Generating NOTICE file (runtime dependencies only)..."
./scripts/generate-notice.sh

echo "🎨 Running Black formatter..."
if ! uv run black .; then
    echo "❌ Black formatter failed. Please fix formatting issues."
    exit 1
fi

echo "🧹 Running Ruff linter..."
if ! uv run ruff check .; then
    echo "❌ Ruff linter found issues. Please fix them before proceeding."
    exit 1
fi

echo ""
echo "🔍 Running pre-commit hooks..."
uv run pre-commit run --all-files -c .tools/.pre-commit-config.yaml

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
