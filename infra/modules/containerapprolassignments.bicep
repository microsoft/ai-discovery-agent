param storageAccountName string
param azureOpenAIName string
param containerAppPrincipalId string
param containerAppStagingPrincipalId string

resource storageAccount 'Microsoft.Storage/storageAccounts@2025-01-01' existing = {
  name: storageAccountName
}

resource azureOpenAI 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' existing = {
  name: azureOpenAIName
}

var storageBlobDataContributorRoleId = resourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')

// Role assignments for Container Apps to access Storage
resource storageRoleForContainerApp 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(storageAccount.id, containerAppPrincipalId, storageBlobDataContributorRoleId)
  properties: {
    roleDefinitionId: storageBlobDataContributorRoleId
    principalId: containerAppPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource storageRoleForStagingContainerApp 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(storageAccount.id, containerAppStagingPrincipalId, storageBlobDataContributorRoleId)
  properties: {
    roleDefinitionId: storageBlobDataContributorRoleId
    principalId: containerAppStagingPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Role assignments for Container Apps to access Azure OpenAI
resource openAIRoleAssignmentForContainerApp 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: azureOpenAI
  name: guid(azureOpenAI.id, containerAppPrincipalId, resourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'))
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: containerAppPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource openAIRoleAssignmentForStagingContainerApp 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: azureOpenAI
  name: guid(azureOpenAI.id, containerAppStagingPrincipalId, resourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'))
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: containerAppStagingPrincipalId
    principalType: 'ServicePrincipal'
  }
}
