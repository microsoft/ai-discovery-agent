
param appServicePlanId string
param resourceToken string
param location string = resourceGroup().location
param tags object = {}
param appSubnetId string
param storageAccountName string
param logAnalyticsWorkspaceId string
param azureOpenAIName string
param acrName string
param acrLoginServer string
param containerImageName string
param applicationInsightsConnectionString string


var siteConfig = {
  acrUseManagedIdentityCreds: true
  ftpsState: 'Disabled'
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

var sharedAppSettingsProperties = {
        AZURE_OPENAI_ENDPOINT: 'https://${azureOpenAIName}.openai.azure.com/'
        AZURE_OPENAI_API_VERSION: '2025-01-01-preview'
        AZURE_STORAGE_ACCOUNT_URL: storageAccount.properties.primaryEndpoints.blob
        APPLICATIONINSIGHTS_CONNECTION_STRING: applicationInsightsConnectionString

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

        DOCKER_REGISTRY_SERVER_URL: 'https://${acrLoginServer}'
      }

var appSettingsProperties = union(sharedAppSettingsProperties, {
        CHAINLIT_AUTH_SECRET: base64('${resourceToken}-${guid(subscription().subscriptionId,resourceGroup().id,web.name,'prod')}')
        OTEL_SERVICE_NAME: 'production'
})

var appSettingsPropertiesStaging = union(sharedAppSettingsProperties, {
        CHAINLIT_AUTH_SECRET: base64('${resourceToken}-${guid(subscription().subscriptionId,resourceGroup().id,web.name,'staging')}')
        OTEL_SERVICE_NAME: 'staging'
        LOG_LEVEL: 'debug'
})



resource storageAccount 'Microsoft.Storage/storageAccounts@2025-01-01' existing = {
  name: storageAccountName
}

resource siteContainer 'Microsoft.Web/sites/sitecontainers@2024-11-01' = {
  parent: web
  name: 'main'
  properties: {
    isMain: true
    image: '${acrLoginServer}/${containerImageName}'
    targetPort: '8000'
    authType: 'SystemIdentity'
    userManagedIdentityClientId: 'SystemIdentity'
  }
}

resource siteContainerStaging 'Microsoft.Web/sites/slots/sitecontainers@2024-11-01' = {
  parent: web::stagingSlot
  name: 'main'
  properties: {
    isMain: true
    image: '${acrLoginServer}/${containerImageName}'
    targetPort: '8000'
    authType: 'SystemIdentity'
    userManagedIdentityClientId: 'SystemIdentity'
  }
}

resource web 'Microsoft.Web/sites@2024-11-01' = {
  //checkov:skip=CKV_AZURE_17
  //checkov:skip=CKV_AZURE_212
  //checkov:skip=CKV_AZURE_222
  //checkov:skip=CKV_AZURE_225
  name: 'web-${resourceToken}'
  location: location
  tags: union(tags, { 'azd-service-name': 'web' })
  kind: 'app,linux,container'
  properties: {
    serverFarmId: appServicePlanId
    siteConfig: siteConfig
    httpsOnly: true
    virtualNetworkSubnetId: appSubnetId
  }

  identity: {
    type: 'SystemAssigned'
  }

  resource appSettings 'config' = {
    name: 'appsettings'
    properties: appSettingsProperties
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
      serverFarmId: appServicePlanId
      siteConfig: siteConfig
      httpsOnly: true
      virtualNetworkSubnetId: appSubnetId
    }
    identity: {
      type: 'SystemAssigned'
    }

    resource stagingAppSettings 'config' = {
      name: 'appsettings'
      properties: appSettingsPropertiesStaging
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



resource diagnosticLogs_prod 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: '${web.name}-${resourceToken}'
  scope: web
  properties: {
    workspaceId: logAnalyticsWorkspaceId
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
    workspaceId: logAnalyticsWorkspaceId
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

resource azureOpenAI 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' existing = {
  name: azureOpenAIName
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

// Role definition: Storage Blob Data Contributor (built-in)
var storageBlobDataContributorRoleId = resourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')

// Grant Web App managed identity access to blobs
resource storageBlobDataContributorForAppService 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(storageAccount.id, web.id, storageBlobDataContributorRoleId)
  properties: {
    roleDefinitionId: storageBlobDataContributorRoleId
    principalId: web.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Grant Web App managed identity access to blobs
resource storageBlobDataContributorForStagingAppService 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(storageAccount.id, web::stagingSlot.id, storageBlobDataContributorRoleId)
  properties: {
    roleDefinitionId: storageBlobDataContributorRoleId
    principalId: web::stagingSlot.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

module acrPullRoleForAppService 'acr.role.bicep' = {
  name: 'acr-role-assignment-appservice-${resourceToken}'
  params: {
    containerRegistryName: acrName
    principalId: web.identity.principalId
    principalType: 'ServicePrincipal'
    push: false
  }
}

module acrPullRoleForStagingSlot 'acr.role.bicep' = {
  name: 'acr-role-assignment-stagingslot-${resourceToken}'
  params: {
    containerRegistryName: acrName
    principalId: web::stagingSlot.identity.principalId
    principalType: 'ServicePrincipal'
    push: false
  }
}

output id string = web.id
output name string = web.name
output principalId string = web.identity.principalId
output stagingSlotPrincipalId string = web::stagingSlot.identity.principalId
output defaultHostName string = web.properties.defaultHostName
output stagingSlotDefaultHostName string = web::stagingSlot.properties.defaultHostName
