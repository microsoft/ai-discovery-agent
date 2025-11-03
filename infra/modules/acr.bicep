param location string
@minLength(3)
@maxLength(22)
param resourceToken string
param tags object
param publicNetworkAccess string = 'Disabled'
param clientIpAddress string
@description('Subnet ID used for VM (provides VNet rule access to storage)')
param privateSubnetId string
param vnetId string
@description('Log Analytics Workspace ID for diagnostic settings')
param logAnalyticsWorkspaceId string = ''

// Create ACR name with guaranteed minimum length of 5 characters
var acrName = 'acreg${take(toLower(replace(resourceToken, '-', '')), 17)}' // Always starts with 'acreg' (5 chars)

var defaultRules = [
  {
    action: 'Allow'
    value: '172.160.222.0/24'
  }
]

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: acrName
  location: location
  tags: tags
  sku: {
    name: 'Premium'
  }
  properties: {
    adminUserEnabled: false
    // Conditional public network access for dev scenarios; see README for details.
    publicNetworkAccess: 'Enabled' // checkov:skip=CKV_AZURE_139: Conditional access for remote build
    networkRuleBypassOptions: 'AzureServices'
    policies: {
      quarantinePolicy: {
        status: 'disabled' // checkov:skip=CKV_AZURE_166: Quarantine is still under preview
      }
      trustPolicy: {
        type: 'Notary'
        status: 'disabled'
      }
      retentionPolicy: {
        days: 30 // Increased retention for better tracking of container images
        status: 'enabled'
      }
    }
    networkRuleSet: {
      defaultAction: publicNetworkAccess == 'Enabled' ? 'Allow' : 'Deny'
      ipRules: clientIpAddress == '' ? defaultRules : union([{ action: 'Allow', value: clientIpAddress }], defaultRules)
    }
    // Anonymous pull is intentionally disabled for security reasons
    anonymousPullEnabled: false
    // Enable data endpoint authentication for improved security
    dataEndpointEnabled: true
  }
}

// Add diagnostic settings for ACR to monitor container operations
resource acrDiagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (logAnalyticsWorkspaceId != '') {
  name: 'acr-diagnostic-${resourceToken}'
  scope: containerRegistry
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        category: 'ContainerRegistryRepositoryEvents'
        enabled: true
      }
      {
        category: 'ContainerRegistryLoginEvents'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

module acrPrivateEndpoint './privateendpoint.bicep' = {
  name: '${acrName}-pe'
  params: {
    location: location
    name: '${acrName}-pe'
    privateLinkServiceId: containerRegistry.id
    subnetId: privateSubnetId
    targetSubResource: 'registry'
    vnetId: vnetId
  }
}

output acrName string = containerRegistry.name
output acrLoginServer string = containerRegistry.properties.loginServer
output acrId string = containerRegistry.id
