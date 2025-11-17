#!/bin/sh
# Check if GITHUB_SECRET is not set before setting GitHub variables
# This prevents running this script when running in GitHub Actions
# The script is intended for local development environment setup.
if [ -z "$GITHUB_SECRET" ]; then
    echo "Finding current CLIENT_IP_ADDRESS (for development network permissions)..."
    azd env set CLIENT_IP_ADDRESS "$(dig +short myip.opendns.com @resolver1.opendns.com | tr -d '\r')"
fi

WEB_APP_NAME=$(azd env get-value WEB_APP_NAME)
# If azd env get-value fails, set WEB_APP_NAME to empty string to skip OAuth settings fetch
if [ $? -ne 0 ]; then
    WEB_APP_NAME=""
fi
RESOURCE_GROUP_NAME=$(azd env get-value RESOURCE_GROUP_NAME)
if [ $? -ne 0 ]; then
    RESOURCE_GROUP_NAME=""
fi
if [ -n "$WEB_APP_NAME" ]; then
    echo "Fetching OAUTH_ settings from Web App: $WEB_APP_NAME ..."
    oauth_values=$(az webapp config appsettings list -n "$WEB_APP_NAME" -g "$RESOURCE_GROUP_NAME" --query "[] | [? contains(name,'OAUTH_')]")
    oauth_values_staging=$(az webapp config appsettings list -n "$WEB_APP_NAME" -g "$RESOURCE_GROUP_NAME" --slot staging --query "[] | [? contains(name,'OAUTH_')]")
    oauth_values=$(echo "$oauth_values" | tr -d '\r\n')
    oauth_values_staging=$(echo "$oauth_values_staging" | tr -d '\r\n')

    if [ -n "$oauth_values" ]; then
        echo "OAUTH_ settings fetched for production slot."
        azd env set OAUTH_SETTINGS "$oauth_values"
    else
        echo "No OAUTH_ settings found for production slot."
    fi

    if [ -n "$oauth_values_staging" ]; then
        echo "OAUTH_ settings fetched for staging slot."
        azd env set OAUTH_SETTINGS_STAGING "$oauth_values_staging"
    else
        echo "No OAUTH_ settings found for staging slot."
    fi
else
    echo "WEB_APP_NAME is not set. Skipping fetching OAUTH_ settings."
fi


repo_name=$(gh repo view --json nameWithOwner -t '{{.nameWithOwner}}')
azd env set GITHUB_REPOSITORY "$repo_name"
