# Container Deployment Migration Summary

This document summarizes the changes made to migrate from Python-based deployment to container-based deployment with sidecar containers in Azure App Service.

## Overview

The migration addresses the following key requirements:
- Use Docker containers instead of Python deployment
- Build containers using Azure Container Registry (ACR) with private endpoints
- Deploy to Azure App Service using sidecar containers
- Update containers using REST API since traditional webhooks don't work with sidecar containers

## Key Changes Made

### 1. GitHub Actions Workflow (.github/workflows/02-ci-cd.yml)

**Major Changes:**
- Replaced `azure/webapps-deploy@v3.0.6` with ACR build and sidecar container update approach
- Added container image building using `az acr build` (works with private ACR endpoints)
- Implemented sidecar container updates using Azure REST API
- Added extended warmup and health checks for container startup
- Separated staging and production deployment steps

**Key Features:**
- Uses `az acr build` to build images remotely in ACR (bypasses private endpoint limitations)
- Updates sidecar containers via REST API calls to Azure Resource Manager
- Implements proper container restart and health verification
- Supports both staging and production slot updates

### 2. Predeploy Script (scripts/predeploy.sh)

**Complete Rewrite:**
- Migrated from Python package deployment to container-based workflow
- Added comprehensive error handling and environment variable validation
- Implemented staging slot container updates with health checks
- Added optional production slot updates (controlled by `UPDATE_PRODUCTION` flag)
- Enhanced logging and progress tracking

**Key Features:**
- Builds unique container images with git SHA and timestamp tags
- Updates sidecar containers using Azure REST API
- Includes health check verification for both staging and production
- Provides detailed deployment feedback and URL outputs

### 3. Infrastructure Updates (Bicep Templates)

**ACR Module (infra/modules/acr.bicep):**
- Enhanced container registry configuration with better retention policies (30 days)
- Added diagnostic settings for monitoring container operations
- Improved ACR name generation to ensure minimum length requirements
- Added support for data endpoint authentication

**Main Resources (infra/resources.bicep):**
- Added Log Analytics workspace integration for ACR diagnostic settings
- Enhanced monitoring capabilities for container registry operations

### 4. Sidecar Container Configuration

**How It Works:**
- Uses Azure App Service sidecar containers (LinuxFxVersion=sitecontainers)
- Main container configured with `isMain: true`, target port 8000
- Authentication via System Managed Identity
- Container images pulled from private ACR using managed identity credentials

**Update Mechanism:**
- Traditional `az webapp config container set` doesn't work with sidecar containers
- Uses Azure REST API to update `Microsoft.Web/sites/sitecontainers` resources
- Requires app restart after container image updates
- Both staging and production slots supported

## Deployment Workflow

### 1. Build Phase
```bash
az acr build \
  --registry $ACR_NAME \
  --image $IMAGE_TAG \
  --file src/Dockerfile \
  src/
```

### 2. Staging Update
```bash
az rest --method PUT \
  --url "https://management.azure.com/.../sitecontainers/main?api-version=2024-11-01" \
  --body '{"properties": {"image": "...", "isMain": true, "targetPort": "8000", ...}}'
```

### 3. Health Verification
```bash
curl -f --connect-timeout 30 --max-time 60 "$STAGING_URL/health"
```

### 4. Production Update (Optional)
- Same REST API call to production slot
- Extended health checks with 15 retry attempts

## Key Benefits

1. **Private ACR Support**: Uses `az acr build` which works with private endpoints
2. **Better Security**: Leverages managed identity for ACR authentication
3. **Improved Monitoring**: Added diagnostic settings for container operations
4. **Reliable Updates**: REST API approach is more reliable than webhooks for sidecar containers
5. **Health Verification**: Comprehensive health checking before declaring deployment successful
6. **Scalable Architecture**: Supports both staging and production deployments

## Environment Variables Required

For the new deployment workflow, ensure these environment variables are set:

```bash
# Required for deployment
ACR_NAME                    # Azure Container Registry name
WEB_APP_NAME               # App Service name
RESOURCE_GROUP_NAME        # Resource group name
AZURE_SUBSCRIPTION_ID      # Azure subscription ID

# Optional
CONTAINER_IMAGE_NAME       # Container image name (default: aida:latest)
UPDATE_PRODUCTION         # Set to "true" to update production slot
```

## Testing and Validation

The migration maintains backward compatibility while providing:
- Faster container-based deployments
- Better observability through Log Analytics integration
- More reliable updates using REST API instead of webhooks
- Enhanced health checking and verification

## Migration Impact

This migration changes the deployment model from:
- **Before**: Python code deployment with source-to-cloud builds
- **After**: Container-based deployment with pre-built images

The change improves reliability, security, and observability while working correctly with private Azure Container Registry endpoints and sidecar container configurations.
