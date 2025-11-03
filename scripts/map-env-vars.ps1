Write-Host "Loading azd .env file from current environment"
foreach ($line in (& azd env get-values)) {
    if ($line -match "([^=]+)=(.*)") {
        $key = $matches[1]
        $value = $matches[2] -replace '^"|"$'
        [Environment]::SetEnvironmentVariable($key, $value)
    }
}

# Check if GITHUB_SECRET is not set before setting GitHub variables
# This prevents overwriting secrets when running in GitHub Actions
if (-not $env:GITHUB_SECRET) {
    Write-Host "Setting GitHub repository variables from environment..."
    gh api --method PUT -H "Accept: application/vnd.github+json" "repos/$env:GITHUB_REPOSITORY/environments/$env:AZURE_ENV_NAME"

    gh variable set AZURE_GH_FED_CLIENT_ID --body "$env:AZURE_GH_FED_CLIENT_ID" --env "$env:AZURE_ENV_NAME"
    gh variable set AZURE_TENANT_ID --body "$env:AZURE_TENANT_ID" --env "$env:AZURE_ENV_NAME"
    gh variable set AZURE_SUBSCRIPTION_ID --body "$env:AZURE_SUBSCRIPTION_ID" --env "$env:AZURE_ENV_NAME"
    gh variable set AZURE_ENV_NAME --body "$env:AZURE_ENV_NAME" --env "$env:AZURE_ENV_NAME"
    gh variable set AZURE_LOCATION --body "$env:AZURE_LOCATION" --env "$env:AZURE_ENV_NAME"
}
else {
    Write-Host "GITHUB_SECRET is set, skipping GitHub variable configuration."
}
