# Release Process

This document describes the automated release process for the AI Discovery Agent project.

## Overview

The project uses an automated release pipeline (`.github/workflows/10-release.yml`) that:

1. Triggers on pull requests and pushes to the `main` branch
2. Extracts the version number from `src/pyproject.toml`
3. Creates a GitHub release with a version tag
4. Builds the package using `uv build`
5. Signs the distribution artifacts with [Sigstore](https://www.sigstore.dev/)
6. Uploads signed artifacts to the GitHub release

## Version Management

The version number is stored in `src/pyproject.toml`:

```toml
[project]
name = "aida"
version = "0.7.1"  # <-- Update this for new releases
```

### Version Format

Versions must follow [Semantic Versioning](https://semver.org/) (X.Y.Z):

- **X**: Major version (breaking changes)
- **Y**: Minor version (new features, backwards compatible)
- **Z**: Patch version (bug fixes, backwards compatible)

## Release Workflow

### For Pull Requests

When a PR is opened targeting the `main` branch, the workflow:

1. **Validates** the version format in `pyproject.toml`
2. **Builds** the package to ensure it compiles correctly
3. **Posts a comment** on the PR with release preview information

Example PR comment:

```
## 🚀 Release Preview

This PR will trigger a release when merged to main.

**Version**: `0.7.1`
**Tag**: `v0.7.1`

The release pipeline will:
1. ✅ Build the package with `uv build`
2. ✅ Sign the tar.gz with sigstore
3. ✅ Create a GitHub release with tag `v0.7.1`
4. ✅ Upload signed artifacts

> **Note**: If tag `v0.7.1` already exists, a `v0.7.1-patch` tag will be created instead.
```

### For Pushes to Main

When code is pushed to `main` (typically after merging a PR), the workflow:

1. **Extracts** the version from `pyproject.toml`
2. **Checks** if the tag `vX.Y.Z` already exists
   - If it exists, creates a `vX.Y.Z-patch` tag instead
   - If both exist, the workflow fails with an error
3. **Builds** the package with `uv build`
4. **Signs** the `.tar.gz` file using Sigstore
5. **Creates** a GitHub release with the tag and uploads:
   - Source distribution (`.tar.gz`)
   - Sigstore signature (`.tar.gz.sigstore`)
   - Wheel distribution (`.whl`)

## Tag Conflict Resolution

If a tag already exists for the current version:

1. The workflow automatically creates a `-patch` suffix tag (e.g., `v0.7.1-patch`)
2. The release is marked as a **prerelease**
3. A warning is added to the release notes

**Important**: If both `vX.Y.Z` and `vX.Y.Z-patch` exist, the workflow will fail. In this case:

1. Update the version in `src/pyproject.toml` to a new version number
2. Commit and push the change
3. The workflow will run again with the new version

## Making a Release

### Step 1: Update the Version

1. Open `src/pyproject.toml`
2. Update the version number:
   ```toml
   version = "0.8.0"  # New version
   ```
3. Commit the change:
   ```bash
   git add src/pyproject.toml
   git commit -m "Bump version to 0.8.0"
   ```

### Step 2: Create a Pull Request

1. Push your changes to a branch
2. Open a pull request targeting `main`
3. Review the automated release preview comment
4. Ensure all CI checks pass

### Step 3: Merge to Main

1. Once approved, merge the PR to `main`
2. The release workflow automatically triggers
3. Monitor the workflow at: https://github.com/microsoft/ai-discovery-agent/actions/workflows/10-release.yml

### Step 4: Verify the Release

1. Go to: https://github.com/microsoft/ai-discovery-agent/releases
2. Verify the new release is created with:
   - Correct version tag
   - Source distribution (`.tar.gz`)
   - Signature file (`.tar.gz.sigstore`)
   - Wheel distribution (`.whl`)

## Verifying Signed Artifacts

The release artifacts are signed with [Sigstore](https://www.sigstore.dev/), a keyless signing solution.

### Install Sigstore

```bash
pip install sigstore
```

### Verify a Release Artifact

```bash
# Download the artifact and signature from the release
wget https://github.com/microsoft/ai-discovery-agent/releases/download/v0.7.1/aida-0.7.1.tar.gz
wget https://github.com/microsoft/ai-discovery-agent/releases/download/v0.7.1/aida-0.7.1.tar.gz.sigstore

# Verify the signature
sigstore verify identity aida-0.7.1.tar.gz \
  --cert-identity "https://github.com/microsoft/ai-discovery-agent/.github/workflows/10-release.yml@refs/heads/main" \
  --cert-oidc-issuer "https://token.actions.githubusercontent.com"
```

Expected output:
```
✓ Signature verified successfully
```

## Troubleshooting

### Workflow Fails: "Tag already exists"

**Problem**: Both `vX.Y.Z` and `vX.Y.Z-patch` tags exist.

**Solution**: Update the version in `src/pyproject.toml` to a new version number.

### Workflow Fails: "Invalid version format"

**Problem**: Version doesn't follow semantic versioning (X.Y.Z).

**Solution**: Update the version in `src/pyproject.toml` to match the format `X.Y.Z` (e.g., `0.8.0`).

### Build Fails

**Problem**: Package build fails during `uv build`.

**Solution**: 
1. Test the build locally: `cd src && uv build`
2. Fix any errors in the source code or `pyproject.toml`
3. Commit and push the fixes

### Signature Verification Fails

**Problem**: `sigstore verify` fails for a release artifact.

**Solution**: Ensure you're using the correct certificate identity and OIDC issuer. The identity should match the workflow file path and branch.

## Security Considerations

1. **Sigstore Signing**: All artifacts are signed transparently using Sigstore, providing:
   - Tamper-proof signatures
   - Public certificate transparency logs
   - Keyless signing (no private keys to manage)

2. **GitHub Actions Security**: 
   - Workflow uses `id-token: write` permission for Sigstore OIDC authentication
   - Artifacts are built in isolated GitHub runners
   - Only `main` branch can trigger releases

3. **Supply Chain Security**:
   - Build process is reproducible
   - All dependencies are locked in `uv.lock`
   - Signatures are publicly verifiable

## Related Documentation

- [GitHub Actions Workflows](../.github/workflows/)
- [Contributing Guidelines](../CONTRIBUTING.md)
- [Security Policy](../SECURITY.md)
- [Sigstore Documentation](https://docs.sigstore.dev/)
