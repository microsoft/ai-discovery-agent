#!/bin/bash

# Container-based deployment script for Azure App Service with Sidecar containers
# This script builds and pushes the container image to ACR, then updates the sidecar containers

set -euo pipefail  # Exit on any error, undefined variables, or pipe failures

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# Function to handle errors
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Default values
CONTAINER_IMAGE_NAME="${CONTAINER_IMAGE_NAME:-aida}"
API_VERSION="2024-11-01"

# Check required environment variables
if [ -z "${ACR_NAME:-}" ]; then
    error_exit "ACR_NAME environment variable is required"
fi

if [ -z "${WEB_APP_NAME:-}" ]; then
    error_exit "WEB_APP_NAME environment variable is required"
fi

if [ -z "${RESOURCE_GROUP_NAME:-}" ]; then
    error_exit "RESOURCE_GROUP_NAME environment variable is required"
fi

if [ -z "${AZURE_SUBSCRIPTION_ID:-}" ]; then
    error_exit "AZURE_SUBSCRIPTION_ID environment variable is required"
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    error_exit "jq is required but not installed. Please install jq: https://jqlang.github.io/jq/download/"
fi

# Generate unique image tag
TIMESTAMP=$(date +%s)
GIT_SHA=${GITHUB_SHA:-$(git rev-parse --short HEAD 2>/dev/null || echo "local")}
IMAGE_TAG="${CONTAINER_IMAGE_NAME}:$(echo "$GIT_SHA" | cut -c1-8)-${TIMESTAMP}"
IMAGE_TAG_LATEST="${CONTAINER_IMAGE_NAME}:latest"
IMAGE_TAG_RUN_ID="${CONTAINER_IMAGE_NAME}:run-{{.Run.ID}}"

log "Starting container-based deployment..."
log "Container Image: $IMAGE_TAG"
log "ACR: $ACR_NAME"
log "Web App: $WEB_APP_NAME"
log "Resource Group: $RESOURCE_GROUP_NAME"


log "Building and pushing container image to ACR..."
# Use ACR build to work with private endpoints
az acr build \
    --registry "$ACR_NAME" \
    --image "$IMAGE_TAG" \
    --image "$IMAGE_TAG_LATEST" \
    --image "$IMAGE_TAG_RUN_ID" \
    --file Dockerfile \
    . || error_exit "Failed to build container image in ACR"

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP_NAME" --query loginServer --output tsv) || error_exit "Failed to get ACR login server"
FULL_IMAGE_NAME="${ACR_LOGIN_SERVER}/${IMAGE_TAG}"

log "Successfully built image: $FULL_IMAGE_NAME"

log "Container image built and pushed: $FULL_IMAGE_NAME"

# Update staging slot sidecar container
log "Updating sidecar container in staging slot..."
az rest --method PUT \
    --url "https://management.azure.com/subscriptions/${AZURE_SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP_NAME}/providers/Microsoft.Web/sites/${WEB_APP_NAME}/slots/staging/sitecontainers/main?api-version=${API_VERSION}" \
    --body "$(jq -n \
        --arg image "$FULL_IMAGE_NAME" \
        '{
          properties: {
            image: $image,
            isMain: true,
            targetPort: "8000",
            authType: "SystemIdentity",
            userManagedIdentityClientId: "SystemIdentity",
            inheritAppSettingsAndConnectionStrings: true
          }
        }')" || error_exit "Failed to update staging sidecar container"

log "Staging sidecar container updated successfully!"

# Sending auth config if it exists
if [ -f ./config/auth-config.yaml ]; then
    log "Uploading auth-config.yaml to staging slot..."
    az webapp deploy --resource-group "$RESOURCE_GROUP_NAME" --name "$WEB_APP_NAME" --slot staging --src-path ./config/auth-config.yaml --type=static --target-path /secrets/auth-config.yaml || error_exit "Failed to upload auth-config.yaml"
fi

# Restart staging slot to apply changes
log "Restarting staging slot..."
az webapp restart \
    --name "$WEB_APP_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --slot staging || error_exit "Failed to restart staging slot"

# Wait for staging to be ready
log "Waiting for staging slot to be ready..."
sleep 30

# Verify staging deployment
STAGING_URL="https://${WEB_APP_NAME}-staging.azurewebsites.net"
log "Verifying staging deployment at $STAGING_URL"

for i in {1..10}; do
    log "Health check attempt $i/10..."
    if curl -f -s --connect-timeout 30 --max-time 60 "$STAGING_URL/health"; then
        log "Staging deployment verified successfully!"
        break
    else
        log "Health check attempt $i failed, retrying in 10 seconds..."
        sleep 10
    fi
done

# Optional: Update production slot as well
if [ "${UPDATE_PRODUCTION:-false}" = "true" ]; then
    log "Updating sidecar container in production slot..."
    az rest --method PUT \
        --url "https://management.azure.com/subscriptions/${AZURE_SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP_NAME}/providers/Microsoft.Web/sites/${WEB_APP_NAME}/sitecontainers/main?api-version=${API_VERSION}" \
        --body '{
            "properties": {
                "image": "'$FULL_IMAGE_NAME'",
                "isMain": true,
                "targetPort": "8000",
                "authType": "SystemIdentity",
                "userManagedIdentityClientId": "SystemIdentity",
                "inheritAppSettingsAndConnectionStrings": true
            }
        }' || error_exit "Failed to update production sidecar container"

    log "Production sidecar container updated successfully!"

    # Restart production app to apply changes
    log "Restarting production app..."
    az webapp restart \
        --name "$WEB_APP_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" || error_exit "Failed to restart production app"

    # Verify production deployment
    log "Waiting for production deployment to complete..."
    sleep 60

    PROD_URL="https://${WEB_APP_NAME}.azurewebsites.net"
    log "Verifying production deployment at $PROD_URL"

    for i in {1..15}; do
        log "Production health check attempt $i/15..."
        if curl -f -s --connect-timeout 30 --max-time 60 "$PROD_URL/health"; then
            log "Production deployment verified successfully!"
            break
        else
            log "Production health check attempt $i failed, retrying in 30 seconds..."
            sleep 30
        fi
    done
fi

log "Container deployment completed successfully!"
log "Staging URL: $STAGING_URL"
if [ "${UPDATE_PRODUCTION:-false}" = "true" ]; then
    log "Production URL: $PROD_URL"
fi
