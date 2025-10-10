echo "Loading azd .env file from current environment..."

# while IFS='=' read -r key value; do
#     value=$(echo "$value" | sed 's/^"//' | sed 's/"$//')
#     export "$key=$value"
# done <<EOF
# $(azd env get-values)
# EOF

echo "Generating azd .azure.env file from current environment..."
azd env get-values > src/.azure.env
echo "azd .env file loaded successfully."
. src/.azure.env

# Check if GITHUB_SECRET is not set before setting GitHub variables
# This prevents overwriting secrets when running in GitHub Actions
if [ -z "$GITHUB_SECRET" ]; then
    echo "Setting GitHub repository variables from environment..."
    GITHUB_REPOSITORY=$(gh repo view --json nameWithOwner -t "{{.nameWithOwner}}")
    DEPLOYMENT_ENVIRONMENT="dev"

    echo "Creating or updating GitHub repo $GITHUB_REPOSITORY for environment: $DEPLOYMENT_ENVIRONMENT"
    gh api --method PUT -H "Accept: application/vnd.github+json" "repos/${GITHUB_REPOSITORY}/environments/${DEPLOYMENT_ENVIRONMENT}"

    gh variable set AZURE_GH_FED_CLIENT_ID --body "$AZURE_GH_FED_CLIENT_ID" --env "$DEPLOYMENT_ENVIRONMENT"
    gh variable set AZURE_TENANT_ID --body "$AZURE_TENANT_ID" --env "$DEPLOYMENT_ENVIRONMENT"
    gh variable set AZURE_SUBSCRIPTION_ID --body "$AZURE_SUBSCRIPTION_ID" --env "$DEPLOYMENT_ENVIRONMENT"
    gh variable set AZURE_ENV_NAME --body "$AZURE_ENV_NAME" --env "$DEPLOYMENT_ENVIRONMENT"
    gh variable set AZURE_LOCATION --body "$AZURE_LOCATION" --env "$DEPLOYMENT_ENVIRONMENT"
else
    echo "GITHUB_SECRET is set, skipping GitHub variable configuration."
fi


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
