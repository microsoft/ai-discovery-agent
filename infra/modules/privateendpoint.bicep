param name string
param location string = resourceGroup().location
param subnetId string
param vnetId string
@description('The resource id of the resource to link with this private link.')
param privateLinkServiceId string
param registrationEnabled bool = false
param endpointName string = 'pe${name}${uniqueString(resourceGroup().id)}'
param zoneName string = ''

@allowed([
  'webpubsub'
  'sites'
  'sites-staging'
  'blob'
  'file'
  'sqlServer'
  'registry'
  'account'
])
param targetSubResource string

var dnsByTarget = {
  webpubsub: 'privatelink.webpubsub.azure.com'
  sites: 'privatelink.azurewebsites.net'
  'sites-staging': 'privatelink.azurewebsites.net'
  blob: 'privatelink.blob.${environment().suffixes.storage}'
  file: 'privatelink.file.${environment().suffixes.storage}'
  sqlServer: 'privatelink${environment().suffixes.sqlServerHostname}' // dont' know why but sqlserverhostname suffix already contains the dot
  registry: 'privatelink.azurecr.io'
  account: 'privatelink.openai.azure.com'
}

resource privateEndpoint 'Microsoft.Network/privateEndpoints@2022-05-01' = {
  name: endpointName
  location: location
  properties: {
    subnet: {
      id: subnetId
    }
    customNetworkInterfaceName: '${endpointName}-nic'
    privateLinkServiceConnections: [
      {
        name: endpointName
        properties: {
          groupIds: [targetSubResource]
          privateLinkServiceId: privateLinkServiceId
        }
      }
    ]
  }
}

resource privateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = if (zoneName == '') {
  name: dnsByTarget[targetSubResource]
  location: 'global'
  dependsOn: [privateEndpoint]
}

resource existingPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' existing = if (zoneName != '') {
  name: zoneName
}

resource privateEndpointDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2022-05-01' = {
  parent: privateEndpoint
  name: '${endpointName}-group'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'privatelink-${endpointName}'
        properties: {
          privateDnsZoneId: (zoneName == '') ? privateDnsZone.id : existingPrivateDnsZone.id
        }
      }
    ]
  }
}

resource vnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = if (zoneName == '') {
  parent: privateDnsZone
  name: '${endpointName}-link' // it's important to keep this name structure, otherwise the link will fail
  location: 'global'
  properties: {
    registrationEnabled: registrationEnabled
    virtualNetwork: {
      id: vnetId
    }
  }
}

output id string = privateEndpoint.id
output name string = privateEndpoint.name

output zoneId string = privateDnsZone.id
output zoneName string = privateDnsZone.name
