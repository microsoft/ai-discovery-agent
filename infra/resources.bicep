@description('prefix used in some resource names to make them unique')
param namePrefix string
param location string
@minLength(3)
@maxLength(22)
param resourceToken string
param tags object
param principalId string
param principalType string
param repository string
param clientIpAddress string
param environment string = 'prod'

var publicNetworkAccess = environment == 'prod' ? 'Disabled' : 'Enabled'

var abbrs = loadJsonContent('./abbreviations.json')

module vnet './modules/vnet.bicep' = {
  name: 'vnet-${resourceToken}'
  params: {
    namePrefix: namePrefix
  }
}

resource azureOpenAI 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  name: '${abbrs.cognitiveServicesAccounts}${resourceToken}'
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: '${abbrs.cognitiveServicesAccounts}${resourceToken}'
    disableLocalAuth: true
    publicNetworkAccess: publicNetworkAccess
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
      virtualNetworkRules: []
      ipRules: (clientIpAddress != '' && environment != 'prod') ? [{ value: clientIpAddress }] : []
    }
  }
}

module azureOpenAIPe './modules/privateendpoint.bicep' = {
  name: '${namePrefix}-deployment-openai-pe'
  params: {
    location: location
    name: '${namePrefix}-deployment-openai-pe'
    privateLinkServiceId: azureOpenAI.id
    subnetId: vnet.outputs.privateSubnetId
    targetSubResource: 'account'
    vnetId: vnet.outputs.vnetId
  }
}

var deployments = [
  {
    name: 'gpt-4o'
    skuName: 'GlobalStandard'
    modelVersion: '2024-08-06'
  }
  {
    name: 'text-embedding-ada-002'
    skuName: 'Standard'
    modelVersion: '2'
  }
  {
    name: 'o4-mini'
    skuName: 'GlobalStandard'
    modelVersion: '2025-04-16'
  }
  {
    name: 'gpt-4.1-nano'
    skuName: 'GlobalStandard'
    modelVersion: '2025-04-14'
  }
]

@batchSize(1)
resource azureOpenAIModel 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = [
  for deployment in deployments: {
    name: deployment.name
    parent: azureOpenAI
    sku: {
      name: deployment.skuName
      capacity: 100
    }
    properties: {
      model: {
        format: 'OpenAI'
        name: deployment.name
        version: deployment.modelVersion
      }
    }
  }
]

// Azure Container Registry
module acr './modules/acr.bicep' = {
  name: 'acr-${resourceToken}'
  params: {
    location: location
    resourceToken: resourceToken
    tags: tags
    principalId: principalId
    principalType: principalType
  }
}

// Log Analytics Workspace (needed by Container Apps Environment)
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-${resourceToken}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
  }
  tags: union(tags, { 'azd-service-name': 'loganalytics' })
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-${resourceToken}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    RetentionInDays: 30
    WorkspaceResourceId: logAnalyticsWorkspace.id
  }
  tags: union(tags, { 'azd-service-name': 'appinsights' })
}

// Storage account - simplified version for Container Apps
resource storageAccount 'Microsoft.Storage/storageAccounts@2025-01-01' = {
  name: substring('st${uniqueString(resourceGroup().id)}', 0, 15)
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: publicNetworkAccess == 'Enabled' ? 'Enabled' : 'Disabled'
    networkAcls: publicNetworkAccess == 'Enabled' ? {
      defaultAction: 'Allow'
    } : {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
      ipRules: (clientIpAddress != '') ? [{ value: clientIpAddress, action: 'Allow' }] : []
    }
  }
  tags: union(tags, { 'azd-service-name': 'storage' })
}

resource storageContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2025-01-01' = {
  name: '${storageAccount.name}/default/conversations'
  properties: {
    publicAccess: 'None'
  }
}

// Private endpoint for storage (if in production)
module storagePe './modules/privateendpoint.bicep' = if (publicNetworkAccess == 'Disabled') {
  name: '${namePrefix}-storage-pe'
  params: {
    location: location
    name: '${namePrefix}-storage-pe'
    privateLinkServiceId: storageAccount.id
    subnetId: vnet.outputs.privateSubnetId
    targetSubResource: 'blob'
    vnetId: vnet.outputs.vnetId
  }
}

// Container Apps
module containerApps './modules/containerapp.bicep' = {
  name: 'containerapp-${resourceToken}'
  params: {
    location: location
    namePrefix: namePrefix
    resourceToken: resourceToken
    tags: tags
    containerAppSubnetId: vnet.outputs.containerAppSubnetId
    azureOpenAIEndpoint: 'https://${azureOpenAI.name}.openai.azure.com/'
    azureOpenAIApiVersion: '2025-01-01-preview'
    storageAccountBlobEndpoint: storageAccount.properties.primaryEndpoints.blob
    applicationInsightsConnectionString: applicationInsights.properties.ConnectionString
    logAnalyticsWorkspaceId: logAnalyticsWorkspace.id
    acrName: acr.outputs.acrName
    imageName: 'ai-discovery-agent'
    imageTag: 'latest'
  }
  dependsOn: [
    azureOpenAIModel
    storageContainer
  ]
}

// Role assignment for local user to access storage
resource storageRoleForUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(storageAccount.id, principalId, 'StorageBlobDataContributor')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') // Storage Blob Data Contributor
    principalId: principalId
    principalType: principalType
  }
}

// Role assignments for Container Apps to access Storage
resource storageRoleForContainerApp 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(storageAccount.id, containerApps.outputs.containerAppPrincipalId, 'StorageBlobDataContributor')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') // Storage Blob Data Contributor
    principalId: containerApps.outputs.containerAppPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource storageRoleForStagingContainerApp 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(storageAccount.id, containerApps.outputs.containerAppStagingPrincipalId, 'StorageBlobDataContributor')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') // Storage Blob Data Contributor
    principalId: containerApps.outputs.containerAppStagingPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Role assignments for Container Apps to access Azure OpenAI
resource openAIRoleAssignmentForContainerApp 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: azureOpenAI
  name: guid(azureOpenAI.id, containerApps.outputs.containerAppPrincipalId, resourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'))
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: containerApps.outputs.containerAppPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource openAIRoleAssignmentForStagingContainerApp 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: azureOpenAI
  name: guid(azureOpenAI.id, containerApps.outputs.containerAppStagingPrincipalId, resourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'))
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: containerApps.outputs.containerAppStagingPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource openAIRoleAssignmentForLocalUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: azureOpenAI
  name: guid(azureOpenAI.id, principalId, resourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'))
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: principalId
    principalType: principalType
  }
}

module federatedIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.4.1' = {
  name: 'federated-identity-deployment-${resourceToken}'
  params: {
    name: 'gh-federated-id-${resourceToken}'
    location: location
    federatedIdentityCredentials: [
      {
        name: 'github-actions-dev-${resourceToken}'
        issuer: 'https://token.actions.githubusercontent.com'
        subject: 'repo:${repository}:environment:dev'
        audiences: [
          'api://AzureADTokenExchange'
        ]
      }
      {
        name: 'github-actions-release-${resourceToken}'
        issuer: 'https://token.actions.githubusercontent.com'
        subject: 'repo:${repository}:environment:release'
        audiences: [
          'api://AzureADTokenExchange'
        ]
      }
      {
        name: 'github-actions-prod-${resourceToken}'
        issuer: 'https://token.actions.githubusercontent.com'
        subject: 'repo:${repository}:environment:prod'
        audiences: [
          'api://AzureADTokenExchange'
        ]
      }
      {
        name: 'github-actions-main-${resourceToken}'
        issuer: 'https://token.actions.githubusercontent.com'
        subject: 'repo:${repository}:ref:refs/heads/main'
        audiences: [
          'api://AzureADTokenExchange'
        ]
      }
      {
        name: 'github-actions-pr-${resourceToken}'
        issuer: 'https://token.actions.githubusercontent.com'
        subject: 'repo:${repository}:pull_request'
        audiences: [
          'api://AzureADTokenExchange'
        ]
      }
    ]
    tags: tags
  }
}

module roleAssignments 'modules/roleassignments.bicep' = {
  scope: subscription()
  name: 'role-assignments-${resourceToken}'
  params: {
    resourceToken: resourceToken
    principalId: federatedIdentity.outputs.principalId
  }
}

output WEB_URI string = containerApps.outputs.containerAppUrl
output STAGING_URI string = containerApps.outputs.containerAppStagingUrl
output WEB_APP_NAME string = containerApps.outputs.containerAppName
output CONTAINER_APP_ENVIRONMENT_NAME string = containerApps.outputs.containerAppEnvironmentName
output AZURE_CONTAINER_REGISTRY_NAME string = acr.outputs.acrName
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = acr.outputs.acrLoginServer
output AZURE_OPENAI_ENDPOINT string = 'https://${azureOpenAI.name}.openai.azure.com/'
output AZURE_OPENAI_API_VERSION string = azureOpenAI.apiVersion
output AZURE_GH_FED_CLIENT_ID string = federatedIdentity.outputs.clientId
output AZURE_STORAGE_ACCOUNT_URL string = storageAccount.properties.primaryEndpoints.blob
output CONVERSATION_TITLE_MODEL_DEPLOYMENT string = deployments[3].name
output COGNITIVE_SERVICE_NAME string = azureOpenAI.name
output STORAGE_ACCOUNT_NAME string = storageAccount.name
output APPINSIGHTS_INSTRUMENTATIONKEY string = applicationInsights.properties.InstrumentationKey
output APPLICATIONINSIGHTS_CONNECTION_STRING string = applicationInsights.properties.ConnectionString
