#!/bin/bash

# Container-based deployment script for Azure App Service with Sidecar containers
# This script builds and pushes the container image to ACR, then updates the sidecar containers

set -e  # Exit on any error

# Default values
CONTAINER_IMAGE_NAME=${CONTAINER_IMAGE_NAME:-"aida"}
API_VERSION="2024-11-01"

# Check required environment variables
if [ -z "$ACR_NAME" ]; then
    echo "Error: ACR_NAME environment variable is required"
    exit 1
fi

if [ -z "$WEB_APP_NAME" ]; then
    echo "Error: WEB_APP_NAME environment variable is required"
    exit 1
fi

if [ -z "$RESOURCE_GROUP_NAME" ]; then
    echo "Error: RESOURCE_GROUP_NAME environment variable is required"
    exit 1
fi

if [ -z "$AZURE_SUBSCRIPTION_ID" ]; then
    echo "Error: AZURE_SUBSCRIPTION_ID environment variable is required"
    exit 1
fi

# Generate unique image tag
TIMESTAMP=$(date +%s)
GIT_SHA=${GITHUB_SHA:-$(git rev-parse --short HEAD 2>/dev/null || echo "local")}
IMAGE_TAG="${CONTAINER_IMAGE_NAME}:${GIT_SHA::8}-${TIMESTAMP}"

echo "Starting container-based deployment..."
echo "Container Image: $IMAGE_TAG"
echo "ACR: $ACR_NAME"
echo "Web App: $WEB_APP_NAME"
echo "Resource Group: $RESOURCE_GROUP_NAME"

# Change to source directory
cd src

echo "Building and pushing container image to ACR..."
# Use ACR build to work with private endpoints
az acr build \
    --registry "$ACR_NAME" \
    --image "$IMAGE_TAG" \
    --file Dockerfile \
    .

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP_NAME" --query loginServer --output tsv)
FULL_IMAGE_NAME="${ACR_LOGIN_SERVER}/${IMAGE_TAG}"

echo "Container image built and pushed: $FULL_IMAGE_NAME"

# Update staging slot sidecar container
echo "Updating sidecar container in staging slot..."
az rest --method PUT \
    --url "https://management.azure.com/subscriptions/${AZURE_SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP_NAME}/providers/Microsoft.Web/sites/${WEB_APP_NAME}/slots/staging/sitecontainers/main?api-version=${API_VERSION}" \
    --body '{
        "properties": {
            "image": "'$FULL_IMAGE_NAME'",
            "isMain": true,
            "targetPort": "8000",
            "authType": "SystemIdentity",
            "userManagedIdentityClientId": "SystemIdentity",
            "inheritAppSettingsAndConnectionStrings": true
        }
    }'

echo "Staging sidecar container updated successfully!"

# Restart staging slot to apply changes
echo "Restarting staging slot..."
az webapp restart \
    --name "$WEB_APP_NAME" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --slot staging

# Wait for staging to be ready
echo "Waiting for staging slot to be ready..."
sleep 30

# Verify staging deployment
STAGING_URL="https://${WEB_APP_NAME}-staging.azurewebsites.net"
echo "Verifying staging deployment at $STAGING_URL"

for i in {1..10}; do
    echo "Health check attempt $i/10..."
    if curl -f -s --connect-timeout 30 --max-time 60 "$STAGING_URL/health"; then
        echo "Staging deployment verified successfully!"
        break
    else
        echo "Health check attempt $i failed, retrying in 10 seconds..."
        sleep 10
    fi
done

# Optional: Update production slot as well
if [ "$UPDATE_PRODUCTION" = "true" ]; then
    echo "Updating sidecar container in production slot..."
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
        }'

    echo "Production sidecar container updated successfully!"

    # Restart production app to apply changes
    echo "Restarting production app..."
    az webapp restart \
        --name "$WEB_APP_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME"

    # Verify production deployment
    echo "Waiting for production deployment to complete..."
    sleep 60

    PROD_URL="https://${WEB_APP_NAME}.azurewebsites.net"
    echo "Verifying production deployment at $PROD_URL"

    for i in {1..15}; do
        echo "Production health check attempt $i/15..."
        if curl -f -s --connect-timeout 30 --max-time 60 "$PROD_URL/health"; then
            echo "Production deployment verified successfully!"
            break
        else
            echo "Production health check attempt $i failed, retrying in 30 seconds..."
            sleep 30
        fi
    done
fi

echo "Container deployment completed successfully!"
echo "Staging URL: $STAGING_URL"
if [ "$UPDATE_PRODUCTION" = "true" ]; then
    echo "Production URL: $PROD_URL"
fi
