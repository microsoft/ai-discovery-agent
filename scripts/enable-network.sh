#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source "$SCRIPT_DIR/../src/.azure.env"
source "$SCRIPT_DIR/../src/.env"

# run only when $GITHUB_SECRET is not set to avoid overwriting secrets in GitHub Actions
if [ -z "$GITHUB_SECRET" ]; then
    # Enable public network access for development purposes
    # This way private endpoints are enabled for production by default (Secure by Default)
    # but during development we can access resources without private endpoints
    echo "Enabling public network access for development..."
    az storage account update --name "$STORAGE_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP_NAME" --public-network-access Enabled --default-action Allow -o table
    az resource update --ids "/subscriptions/$AZURE_SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.CognitiveServices/accounts/$COGNITIVE_SERVICE_NAME" --set properties.publicNetworkAccess="Enabled" --set properties.networkAcls.defaultAction="Allow" -o table
    echo "Public network access enabled."
else
    echo "GITHUB_SECRET is set, skipping development config."
fi
