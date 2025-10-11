# Check if GITHUB_SECRET is not set before setting GitHub variables
# This prevents running this script when running in GitHub Actions
# The script is intended for local development environment setup.
if [ -z "$GITHUB_SECRET" ]; then
    echo "Finding current CLIENT_IP_ADDRESS (for development network permissions)..."
    azd env set CLIENT_IP_ADDRESS $(curl ifconfig.me 2>/dev/null | tr -d '\r')
fi

$repo_name = gh repo view --json nameWithOwner -t '{{.nameWithOwner}}'
azd env set GITHUB_REPOSITORY "$repo_name"
