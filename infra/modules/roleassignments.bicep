targetScope = 'subscription'
param resourceToken string
param principalId string

resource githubActionsContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: subscription()
  name: guid(principalId, 'gh-federated-id-${resourceToken}', resourceId('Microsoft.Authorization/roleDefinitions', 'b24988ac-6180-42a0-ab88-20f7382dd24c'))
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', 'b24988ac-6180-42a0-ab88-20f7382dd24c') // Contributor role
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

resource githubActionsUserAccessAdministratorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: subscription()
  name: guid(principalId, 'gh-federated-id-uaa-${resourceToken}', resourceId('Microsoft.Authorization/roleDefinitions', '18d7d88d-d35e-4fb5-a5c3-7773c20a72d9'))
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '18d7d88d-d35e-4fb5-a5c3-7773c20a72d9') // User Access Administrator role
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}
