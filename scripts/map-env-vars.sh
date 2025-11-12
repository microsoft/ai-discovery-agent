#!/bin/sh
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

    echo "Creating or updating GitHub repo $GITHUB_REPOSITORY for environment: $DEPLOYMENT_ENVIRONMENT"
    result=$(gh api --method PUT -H "Accept: application/vnd.github+json" "repos/${GITHUB_REPOSITORY}/environments/${DEPLOYMENT_ENVIRONMENT}" 2>&1)
    if [ $? -ne 0 ]; then
        echo "Error creating/updating GitHub environment: $result"
        if echo "$result" | grep -q "404"; then
            echo "404 error is normal - you may not have permissions to create environments. This is expected in some configurations, just check if the variables were set correctly in the next steps."
        fi
    else
        echo "GitHub environment $DEPLOYMENT_ENVIRONMENT created or updated successfully."
    fi
    gh variable set AZURE_GH_FED_CLIENT_ID --body "$AZURE_GH_FED_CLIENT_ID" --env "$DEPLOYMENT_ENVIRONMENT"
    gh variable set AZURE_TENANT_ID --body "$AZURE_TENANT_ID" --env "$DEPLOYMENT_ENVIRONMENT"
    gh variable set AZURE_SUBSCRIPTION_ID --body "$AZURE_SUBSCRIPTION_ID" --env "$DEPLOYMENT_ENVIRONMENT"
    gh variable set AZURE_ENV_NAME --body "$AZURE_ENV_NAME" --env "$DEPLOYMENT_ENVIRONMENT"
    gh variable set AZURE_LOCATION --body "$AZURE_LOCATION" --env "$DEPLOYMENT_ENVIRONMENT"
else
    echo "GITHUB_SECRET is set, skipping GitHub variable configuration."
fi
