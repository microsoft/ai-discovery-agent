using './main.bicep'

param name = readEnvironmentVariable('AZURE_ENV_NAME') // The environment name, for example dev
param location = readEnvironmentVariable('AZURE_LOCATION') // Azure region to deploy resources to
param principalId = readEnvironmentVariable('AZURE_PRINCIPAL_ID')
param principalType = readEnvironmentVariable('AZURE_PRINCIPAL_TYPE', 'User') // 'User' or 'ServicePrincipal'
param repository = readEnvironmentVariable('GITHUB_REPOSITORY', 'microsoft/ai-discovery-agent') // GitHub repository name
param clientIpAddress = readEnvironmentVariable('CLIENT_IP_ADDRESS', '') // Current client IP address for development network access
