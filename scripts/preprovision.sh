# Check if GITHUB_SECRET is not set before setting GitHub variables
# This prevents running this script when running in GitHub Actions
# The script is intended for local development environment setup.
if [ -z "$GITHUB_SECRET" ]; then
    echo "Finding current CLIENT_IP_ADDRESS (for development network permissions)..."
    azd env set CLIENT_IP_ADDRESS $(curl ifconfig.me 2>/dev/null | tr -d '\r')
fi

if [ -n "$WEB_APP_NAME" ]; then
    echo "Fetching OAUTH_ settings from Web App: $WEB_APP_NAME ..."
    oauth_values=$(az webapp config appsettings list -n "$WEB_APP_NAME" -g "$RESOURCE_GROUP_NAME" --query "[] | [? contains(name,'OAUTH_')]")
    azd env set OAUTH_SETTINGS "$oauth_values"
else
    echo "WEB_APP_NAME is not set. Skipping fetching OAUTH_ settings."
fi


repo_name=$(gh repo view --json nameWithOwner -t '{{.nameWithOwner}}')
azd env set GITHUB_REPOSITORY "$repo_name"
