param location string
param namePrefix string
param resourceToken string
param tags object
param containerAppSubnetId string
param azureOpenAIEndpoint string
param azureOpenAIApiVersion string
param storageAccountBlobEndpoint string
param applicationInsightsConnectionString string
param logAnalyticsWorkspaceId string
param acrName string
param imageName string
param imageTag string = 'latest'

// Container Apps Environment
resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${namePrefix}-cae'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: reference(logAnalyticsWorkspaceId, '2023-09-01').customerId
        sharedKey: listKeys(logAnalyticsWorkspaceId, '2023-09-01').primarySharedKey
      }
    }
    vnetConfiguration: {
      infrastructureSubnetId: containerAppSubnetId
      internal: false
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}

// Container App - Production
resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-${resourceToken}'
  location: location
  tags: union(tags, { 'azd-service-name': 'web' })
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppEnvironment.id
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      registries: [
        {
          server: '${acrName}.azurecr.io'
          identity: 'system'
        }
      ]
      secrets: [
        {
          name: 'chainlit-auth-secret-prod'
          value: base64('${resourceToken}-${guid(subscription().subscriptionId, resourceGroup().id, 'ca-${resourceToken}', 'prod')}')
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'ai-discovery-agent'
          image: '${acrName}.azurecr.io/${imageName}:${imageTag}'
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
          probes: [
            {
              type: 'liveness'
              httpGet: {
                path: '/health'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 60
              periodSeconds: 30
              timeoutSeconds: 30
              failureThreshold: 3
            }
            {
              type: 'readiness'
              httpGet: {
                path: '/health'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 30
              periodSeconds: 10
              timeoutSeconds: 10
              failureThreshold: 3
            }
          ]
          env: [
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: azureOpenAIEndpoint
            }
            {
              name: 'AZURE_OPENAI_API_VERSION'
              value: azureOpenAIApiVersion
            }
            {
              name: 'CHAINLIT_AUTH_SECRET'
              secretRef: 'chainlit-auth-secret-prod'
            }
            {
              name: 'AZURE_STORAGE_ACCOUNT_URL'
              value: storageAccountBlobEndpoint
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: applicationInsightsConnectionString
            }
            {
              name: 'OTEL_SERVICE_NAME'
              value: 'production'
            }
            {
              name: 'PYTHONUNBUFFERED'
              value: '1'
            }
            {
              name: 'PYTHONIOENCODING'
              value: 'utf-8'
            }
            {
              name: 'PYTHONDONTWRITEBYTECODE'
              value: '1'
            }
            {
              name: 'WEB_CONCURRENCY'
              value: '1'
            }
            {
              name: 'WORKER_CONNECTIONS'
              value: '1000'
            }
            {
              name: 'WORKER_TIMEOUT'
              value: '1200'
            }
            {
              name: 'PORT'
              value: '8000'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

// Container App - Staging
resource containerAppStaging 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-${resourceToken}-staging'
  location: location
  tags: union(tags, { 'azd-service-name': 'web-staging' })
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppEnvironment.id
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      registries: [
        {
          server: '${acrName}.azurecr.io'
          identity: 'system'
        }
      ]
      secrets: [
        {
          name: 'chainlit-auth-secret-staging'
          value: base64('${resourceToken}-${guid(subscription().subscriptionId, resourceGroup().id, 'ca-${resourceToken}', 'staging')}')
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'ai-discovery-agent'
          image: '${acrName}.azurecr.io/${imageName}:${imageTag}'
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
          probes: [
            {
              type: 'liveness'
              httpGet: {
                path: '/health'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 60
              periodSeconds: 30
              timeoutSeconds: 30
              failureThreshold: 3
            }
            {
              type: 'readiness'
              httpGet: {
                path: '/health'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 30
              periodSeconds: 10
              timeoutSeconds: 10
              failureThreshold: 3
            }
          ]
          env: [
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: azureOpenAIEndpoint
            }
            {
              name: 'AZURE_OPENAI_API_VERSION'
              value: azureOpenAIApiVersion
            }
            {
              name: 'CHAINLIT_AUTH_SECRET'
              secretRef: 'chainlit-auth-secret-staging'
            }
            {
              name: 'AZURE_STORAGE_ACCOUNT_URL'
              value: storageAccountBlobEndpoint
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: applicationInsightsConnectionString
            }
            {
              name: 'OTEL_SERVICE_NAME'
              value: 'staging'
            }
            {
              name: 'PYTHONUNBUFFERED'
              value: '1'
            }
            {
              name: 'PYTHONIOENCODING'
              value: 'utf-8'
            }
            {
              name: 'PYTHONDONTWRITEBYTECODE'
              value: '1'
            }
            {
              name: 'WEB_CONCURRENCY'
              value: '1'
            }
            {
              name: 'WORKER_CONNECTIONS'
              value: '1000'
            }
            {
              name: 'WORKER_TIMEOUT'
              value: '1200'
            }
            {
              name: 'PORT'
              value: '8000'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

output containerAppEnvironmentId string = containerAppEnvironment.id
output containerAppEnvironmentName string = containerAppEnvironment.name
output containerAppId string = containerApp.id
output containerAppName string = containerApp.name
output containerAppFqdn string = containerApp.properties.configuration.ingress.fqdn
output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output containerAppPrincipalId string = containerApp.identity.principalId
output containerAppStagingId string = containerAppStaging.id
output containerAppStagingName string = containerAppStaging.name
output containerAppStagingFqdn string = containerAppStaging.properties.configuration.ingress.fqdn
output containerAppStagingUrl string = 'https://${containerAppStaging.properties.configuration.ingress.fqdn}'
output containerAppStagingPrincipalId string = containerAppStaging.identity.principalId
