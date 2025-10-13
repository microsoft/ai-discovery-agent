@description('Location for all storage-related resources')
param location string
@description('Name prefix used for derived resource names')
param namePrefix string
@description('Subnet ID used for VM (provides VNet rule access to storage)')
param privateSubnetId string
@description('Principal ID of the Web App managed identity (SystemAssigned)')
param webPrincipalId string
@description('Resource ID of the Web App (used for role assignment GUID)')
param webId string
@description('Principal ID of the Web App managed identity (SystemAssigned)')
param stagingWebPrincipalId string
@description('Resource ID of the Web App (used for role assignment GUID)')
param stagingWebId string
@description('Principal ID (e.g. user / group) receiving Storage Blob Data Contributor')
param principalId string
@description('Principal type corresponding to principalId (e.g. User, Group, ServicePrincipal)')
param principalType string
@description('Client IP address to allow access if public network access is disabled')
param clientIpAddress string
@allowed([
  'Standard_LRS'
  'Standard_GRS'
  'Standard_ZRS'
])
@description('Storage replication SKU')
param storageSku string = 'Standard_LRS'

// Storage account hosting conversation persistence container
resource storageAccount 'Microsoft.Storage/storageAccounts@2025-01-01' = {
  //checkov:skip=CKV_AZURE_206
  name: substring('st${uniqueString(resourceGroup().id)}', 0, 15)
  location: location
  sku: {
    name: storageSku
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    encryption: {
      services: {
        blob: { enabled: true }
        file: { enabled: true }
      }
      keySource: 'Microsoft.Storage'
    }
    publicNetworkAccess: 'Disabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Deny'
      virtualNetworkRules: []
      // Allow access from client IP while developing if specified
      ipRules: clientIpAddress == '' ? [] : [{ action: 'Allow', value: clientIpAddress }]
    }
  }
}

// Private endpoint (file subresource adequate for blob & file DNS resolution when needed)
module storagePrivateEndpoint './privateendpoint.bicep' = {
  name: '${namePrefix}-deployment-storage-pe'
  params: {
    location: location
    name: '${namePrefix}-deployment-storage-pe'
    privateLinkServiceId: storageAccount.id
    subnetId: privateSubnetId
    targetSubResource: 'blob'
    vnetId: substring(privateSubnetId, 0, lastIndexOf(privateSubnetId, '/subnets')) // derive vnet id if module expects it
  }
}

resource storageBlobService 'Microsoft.Storage/storageAccounts/blobServices@2021-09-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}
// Container for conversation persistence (no public access)
resource conversationsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2021-09-01' = {
  name: '${storageAccount.name}/default/conversations'
  properties: {
    publicAccess: 'None'
  }
}

// Role definition: Storage Blob Data Contributor (built-in)
var storageBlobDataContributorRoleId = resourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')

// Grant Web App managed identity access to blobs
resource storageBlobDataContributorForAppService 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(storageAccount.id, webPrincipalId, storageBlobDataContributorRoleId)
  properties: {
    roleDefinitionId: storageBlobDataContributorRoleId
    principalId: webPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Grant Web App managed identity access to blobs
resource storageBlobDataContributorForStagingAppService 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(storageAccount.id, stagingWebPrincipalId, storageBlobDataContributorRoleId)
  properties: {
    roleDefinitionId: storageBlobDataContributorRoleId
    principalId: stagingWebPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Grant specified principal (user/group) blob contributor access
resource storageBlobDataContributorForUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(storageAccount.id, principalId, storageBlobDataContributorRoleId)
  properties: {
    roleDefinitionId: storageBlobDataContributorRoleId
    principalId: principalId
    principalType: principalType
  }
}

@description('Blob endpoint URL for the storage account')
output storageAccountBlobEndpoint string = storageAccount.properties.primaryEndpoints.blob
@description('Storage account resource ID')
output storageAccountId string = storageAccount.id
@description('Conversation container resource name (<account>/default/conversations)')
output conversationsContainerName string = conversationsContainer.name
@description('Storage account name')
output storageAccountName string = storageAccount.name
