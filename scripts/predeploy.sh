#!/bin/bash
CONTAINER_IMAGE_NAME=${CONTAINER_IMAGE_NAME:-"aida:latest"}

cd src
# App service relies on the requirements file
# uv pip compile pyproject.toml -o requirements.txt

# Cleanup before building the image
echo "Building and pushing container image to ACR..."
# rm -rf __pycache__
# rm -rf *.pyc
# rm -rf **/*.pyc
# rm -rf .ruff_cache
# rm -rf .venv
az acr build --registry $ACR_NAME --image $CONTAINER_IMAGE_NAME .

az webapp restart --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP_NAME    