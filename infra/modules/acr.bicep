param location string
@minLength(3)
@maxLength(22)
param resourceToken string
param tags object
param publicNetworkAccess string = 'Disabled'
param clientIpAddress string
@description('Subnet ID used for VM (provides VNet rule access to storage)')
param privateSubnetId string

// Ensure ACR name is at least 5 characters and only alphanumeric
var acrName = 'cr${toLower(replace(resourceToken, '-', ''))}'

var defaultRules = [{
  action: 'Allow'
  value: '172.160.222.0/24'
}]

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: acrName
  location: location
  tags: tags
  sku: {
    name: 'Premium'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
    policies: {
      quarantinePolicy: {
        status: 'disabled'
      }
      trustPolicy: {
        type: 'Notary'
        status: 'disabled'
      }
      retentionPolicy: {
        days: 7
        status: 'disabled'
      }
    }
    networkRuleSet:{
      defaultAction: publicNetworkAccess == 'Enabled' ? 'Allow' : 'Deny'
      ipRules: clientIpAddress == '' ? defaultRules : union([{ action: 'Allow', value: clientIpAddress }], defaultRules)
    }
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
    vnetId: substring(privateSubnetId, 0, lastIndexOf(privateSubnetId, '/subnets')) // derive vnet id if module expects it
  }
}

output acrName string = containerRegistry.name
output acrLoginServer string = containerRegistry.properties.loginServer
output acrId string = containerRegistry.id
