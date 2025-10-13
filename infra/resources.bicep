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

var abbrs = loadJsonContent('./abbreviations.json')
var siteConfig = {
  linuxFxVersion: 'PYTHON|3.12'
  ftpsState: 'Disabled'
  appCommandLine: 'startup.sh'
  healthCheckPath: '/health'
  http20Enabled: true
  minTlsVersion: '1.2'
  alwaysOn: true
  webSocketsEnabled: true
  detailedErrorLoggingEnabled: true
  logsDirectorySizeLimit: 35
  // Performance optimizations
  minimumElasticInstanceCount: 1
  numberOfWorkers: 1
}

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
    publicNetworkAccess: 'Disabled'
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
      virtualNetworkRules: []
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

resource web 'Microsoft.Web/sites@2024-11-01' = {
  //checkov:skip=CKV_AZURE_17
  //checkov:skip=CKV_AZURE_212
  //checkov:skip=CKV_AZURE_222
  //checkov:skip=CKV_AZURE_225
  name: 'web-${resourceToken}'
  location: location
  tags: union(tags, { 'azd-service-name': 'web' })
  kind: 'app,linux'
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: siteConfig
    httpsOnly: true
    virtualNetworkSubnetId: vnet.outputs.appSubnetId
  }
  identity: {
    type: 'SystemAssigned'
  }

  resource appSettings 'config' = {
    name: 'appsettings'
    properties: {
      ENABLE_ORYX_BUILD: 'true'
      SCM_DO_BUILD_DURING_DEPLOYMENT: 'true'
      AZURE_OPENAI_ENDPOINT: 'https://${azureOpenAI.name}.openai.azure.com/'
      AZURE_OPENAI_API_VERSION: '2025-01-01-preview' //azureOpenAI.apiVersion <- does not give the correct value
      CHAINLIT_AUTH_SECRET: base64('${resourceToken}-${guid(subscription().subscriptionId,resourceGroup().id,web.name,'prod')}')
      // Storage account settings (for use with DefaultAzureCredential / Managed Identity)
      AZURE_STORAGE_ACCOUNT_URL: storage.outputs.storageAccountBlobEndpoint
      APPINSIGHTS_INSTRUMENTATIONKEY: applicationInsights.properties.InstrumentationKey // todo: use keyvault '@Microsoft.KeyVault(SecretUri=${keyVault::appInsightsInstrumentationKeyKeyVaultSecret.properties.secretUri})'
      APPLICATIONINSIGHTS_CONNECTION_STRING: applicationInsights.properties.ConnectionString
      OTEL_SERVICE_NAME: 'production'

      // Performance and warmup settings
      WEBSITE_HEALTHCHECK_MAXPINGFAILURES: '3'
      WEBSITE_WARMUP_PATH: '/health'
      WEBSITE_SWAP_WARMUP_PING_PATH: '/health'
      WEBSITE_SWAP_WARMUP_PING_STATUSES: '200'
      WEBSITE_TIME_ZONE: 'UTC'

      // Python optimization settings
      PYTHONUNBUFFERED: '1'
      PYTHONIOENCODING: 'utf-8'
      PYTHONDONTWRITEBYTECODE: '1'

      // Application performance settings
      WEB_CONCURRENCY: '1'
      WORKER_CONNECTIONS: '1000'
      WORKER_TIMEOUT: '1200' // 20 minutes

      // Disable unused features for better performance
      WEBSITE_ENABLE_SYNC_UPDATE_SITE: 'false'
      WEBSITES_ENABLE_APP_SERVICE_STORAGE: 'true'
    }
  }

  resource slotConfigNames 'config' = {
    name: 'slotConfigNames'
    kind: 'string'
    properties: {
      appSettingNames: [
        'OAUTH_GITHUB_CLIENT_ID'
        'OAUTH_GITHUB_CLIENT_SECRET'
        'CHAINLIT_AUTH_SECRET'
        'OTEL_SERVICE_NAME'
      ]
      azureStorageConfigNames: []
      connectionStringNames: []
    }
  }

  resource logs 'config' = {
    name: 'logs'
    properties: {
      applicationLogs: {
        fileSystem: {
          level: 'Verbose'
        }
      }
      detailedErrorMessages: {
        enabled: true
      }
      failedRequestsTracing: {
        enabled: true
      }
      httpLogs: {
        fileSystem: {
          enabled: true
          retentionInDays: 1
          retentionInMb: 35
        }
      }
    }
  }

  // Staging slot for the web app
  resource stagingSlot 'slots' = {
    //checkov:skip=CKV_AZURE_17
    //checkov:skip=CKV_AZURE_212
    //checkov:skip=CKV_AZURE_222
    //checkov:skip=CKV_AZURE_225
    name: 'staging'
    location: location
    kind: 'app,linux'
    properties: {
      serverFarmId: appServicePlan.id
      siteConfig: siteConfig
      httpsOnly: true
      virtualNetworkSubnetId: vnet.outputs.appSubnetId
    }
    identity: {
      type: 'SystemAssigned'
    }

    resource stagingAppSettings 'config' = {
      name: 'appsettings'
      properties: {
        ENABLE_ORYX_BUILD: 'true'
        SCM_DO_BUILD_DURING_DEPLOYMENT: 'true'
        AZURE_OPENAI_ENDPOINT: 'https://${azureOpenAI.name}.openai.azure.com/'
        AZURE_OPENAI_API_VERSION: '2025-01-01-preview'
        CHAINLIT_AUTH_SECRET: base64('${resourceToken}-${guid(subscription().subscriptionId,resourceGroup().id,web.name,'staging')}')
        AZURE_STORAGE_ACCOUNT_URL: storage.outputs.storageAccountBlobEndpoint
        APPLICATIONINSIGHTS_CONNECTION_STRING: applicationInsights.properties.ConnectionString
        OTEL_SERVICE_NAME: 'staging'

        // Performance and warmup settings
        WEBSITE_HEALTHCHECK_MAXPINGFAILURES: '3'
        WEBSITE_WARMUP_PATH: '/health'
        WEBSITE_SWAP_WARMUP_PING_PATH: '/health'
        WEBSITE_SWAP_WARMUP_PING_STATUSES: '200'
        WEBSITE_TIME_ZONE: 'UTC'

        // Python optimization settings
        PYTHONUNBUFFERED: '1'
        PYTHONIOENCODING: 'utf-8'
        PYTHONDONTWRITEBYTECODE: '1'

        // Application performance settings
        WEB_CONCURRENCY: '1'
        WORKER_CONNECTIONS: '1000'
        WORKER_TIMEOUT: '1200'

        // Disable unused features for better performance
        WEBSITE_ENABLE_SYNC_UPDATE_SITE: 'false'
        WEBSITES_ENABLE_APP_SERVICE_STORAGE: 'true'
      }
    }

    resource stagingLogs 'config' = {
      name: 'logs'
      properties: {
        applicationLogs: {
          fileSystem: {
            level: 'Verbose'
          }
        }
        detailedErrorMessages: {
          enabled: true
        }
        failedRequestsTracing: {
          enabled: true
        }
        httpLogs: {
          fileSystem: {
            enabled: true
            retentionInDays: 1
            retentionInMb: 35
          }
        }
      }
    }
  }
}

resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  //checkov:skip=CKV_AZURE_225
  name: 'app-${resourceToken}'
  location: location
  sku: {
    name: 'S1'
    tier: 'Standard'
    capacity: 1
  }
  kind: 'linux'
  properties: {
    reserved: true
    perSiteScaling: false
    elasticScaleEnabled: false
    maximumElasticWorkerCount: 1
    isSpot: false
    targetWorkerCount: 0
    targetWorkerSizeId: 0
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

resource diagnosticLogs_prod 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: '${web.name}-${resourceToken}'
  scope: web
  properties: {
    workspaceId: logAnalyticsWorkspace.id
    logs: [
      { enabled: true, category: 'AppServiceHTTPLogs' }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

resource diagnosticLogs_staging 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: '${web::stagingSlot.name}-${resourceToken}'
  scope: web::stagingSlot
  properties: {
    workspaceId: logAnalyticsWorkspace.id
    logs: [
      { enabled: true, category: 'AppServiceHTTPLogs' }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
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

resource openAIRoleAssignmentForLocalUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: azureOpenAI
  name: guid(azureOpenAI.id, principalId, resourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'))
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: principalId
    principalType: principalType
  }
}

resource openAIRoleAssignmentForAppService 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: azureOpenAI
  name: guid(azureOpenAI.id, web.id, resourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'))
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: web.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource openAIRoleAssignmentForStagingSlot 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: azureOpenAI
  name: guid(azureOpenAI.id, web::stagingSlot.id, resourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'))
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: web::stagingSlot.identity.principalId
    principalType: 'ServicePrincipal'
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
    webPrincipalId: web.identity.principalId
    webId: web.id
    stagingWebId: web::stagingSlot.id
    stagingWebPrincipalId: web::stagingSlot.identity.principalId
    principalId: principalId
    principalType: principalType
    clientIpAddress: clientIpAddress
  }
}

output WEB_URI string = 'https://${web.properties.defaultHostName}'
output STAGING_URI string = 'https://${web::stagingSlot.properties.defaultHostName}'
output WEB_APP_NAME string = web.name
output AZURE_OPENAI_ENDPOINT string = 'https://${azureOpenAI.name}.openai.azure.com/'
output AZURE_OPENAI_API_VERSION string = azureOpenAI.apiVersion
output AZURE_GH_FED_CLIENT_ID string = federatedIdentity.outputs.clientId
output AZURE_STORAGE_ACCOUNT_URL string = storage.outputs.storageAccountBlobEndpoint
output CONVERSATION_TITLE_MODEL_DEPLOYMENT string = deployments[3].name
output COGNITIVE_SERVICE_NAME string = azureOpenAI.name
output STORAGE_ACCOUNT_NAME string = storage.outputs.storageAccountName
output APPINSIGHTS_INSTRUMENTATIONKEY string = applicationInsights.properties.InstrumentationKey
output APPLICATIONINSIGHTS_CONNECTION_STRING string = applicationInsights.properties.ConnectionString
