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
param containerImageName string


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

module appServicePlan 'modules/appservice.plan.bicep' = {
  name: 'appserviceplan-${resourceToken}'
  params: {
    resourceToken: resourceToken
    location: location
  }
}

module appServiceSite 'modules/appservice.site.bicep' = {
  name: 'appservice-${resourceToken}'
  params: {
    resourceToken: resourceToken
    location: location
    appServicePlanId: appServicePlan.outputs.id
    acrName: acr.outputs.acrName
    acrLoginServer: acr.outputs.acrLoginServer
    appSubnetId: vnet.outputs.appSubnetId
    tags: tags
    storageAccountName: storage.outputs.storageAccountName
    logAnalyticsWorkspaceId: logAnalyticsWorkspace.id
    azureOpenAIName: azureOpenAI.name
    applicationInsightsConnectionString: applicationInsights.properties.ConnectionString
    containerImageName: containerImageName
  }
}

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
// Encapsulated storage (account, container, private endpoint, role assignments)
module storage 'modules/storage.bicep' = {
  name: 'storage-deployment'
  params: {
    location: location
    namePrefix: namePrefix
    privateSubnetId: vnet.outputs.privateSubnetId
    principalId: principalId
    principalType: principalType
    clientIpAddress: clientIpAddress
    publicNetworkAccess: publicNetworkAccess
    tags: tags
  }
}

module acr 'modules/acr.bicep' = {
  name: 'acr-deployment-${resourceToken}'
  params: {
    location: location
    resourceToken: resourceToken
    tags: tags
    publicNetworkAccess: publicNetworkAccess
    clientIpAddress: clientIpAddress
    privateSubnetId: vnet.outputs.privateSubnetId
  }
}

module acrPushRoleForUser 'modules/acr.role.bicep' = {
  name: 'acr-role-assignment-user-${resourceToken}'
  params: {
    containerRegistryName: acr.outputs.acrName
    principalId: principalId
    principalType: principalType
    push: true
  }
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

output WEB_URI string = 'https://${appServiceSite.outputs.defaultHostName}'
output STAGING_URI string = 'https://${appServiceSite.outputs.stagingSlotDefaultHostName}/staging'
output WEB_APP_NAME string = appServiceSite.outputs.name
output AZURE_OPENAI_ENDPOINT string = 'https://${azureOpenAI.name}.openai.azure.com/'
output AZURE_OPENAI_API_VERSION string = azureOpenAI.apiVersion
output AZURE_GH_FED_CLIENT_ID string = federatedIdentity.outputs.clientId
output AZURE_STORAGE_ACCOUNT_URL string = storage.outputs.storageAccountBlobEndpoint
output CONVERSATION_TITLE_MODEL_DEPLOYMENT string = deployments[3].name
output COGNITIVE_SERVICE_NAME string = azureOpenAI.name
output STORAGE_ACCOUNT_NAME string = storage.outputs.storageAccountName
output APPINSIGHTS_INSTRUMENTATIONKEY string = applicationInsights.properties.InstrumentationKey
output APPLICATIONINSIGHTS_CONNECTION_STRING string = applicationInsights.properties.ConnectionString
output ACR_NAME string = acr.outputs.acrName
output ACR_LOGIN_SERVER string = acr.outputs.acrLoginServer
