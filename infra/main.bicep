targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param name string
param principalId string
param principalType string = 'User'
param repository string = 'microsoft/ai-discovery-agent'
@minLength(1)
@description('Primary location for all resources')
param location string
param clientIpAddress string = ''
@allowed([
  'prod'
  'dev'
])
param environment string

var resourceToken = toLower(uniqueString(subscription().id, name, location))
var tags = { 'azd-env-name': name }

resource resourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: '${name}-rg'
  location: location
  tags: tags
}

module resources 'resources.bicep' = {
  name: 'resources'
  scope: resourceGroup
  params: {
    namePrefix: name
    location: location
    resourceToken: resourceToken
    tags: tags
    principalId: principalId
    principalType: principalType
    repository: repository
    clientIpAddress: clientIpAddress
    environment: environment
  }
}

output AZURE_LOCATION string = location
output AZURE_OPENAI_ENDPOINT string = resources.outputs.AZURE_OPENAI_ENDPOINT
output WEB_APP_NAME string = resources.outputs.WEB_APP_NAME
output WEB_URI string = resources.outputs.WEB_URI
output STAGING_URI string = resources.outputs.STAGING_URI
output AZURE_GH_FED_CLIENT_ID string = resources.outputs.AZURE_GH_FED_CLIENT_ID
output AZURE_TENANT_ID string = subscription().tenantId
output AZURE_STORAGE_ACCOUNT_URL string = resources.outputs.AZURE_STORAGE_ACCOUNT_URL
output CONVERSATION_TITLE_MODEL_DEPLOYMENT string = resources.outputs.CONVERSATION_TITLE_MODEL_DEPLOYMENT
output RESOURCE_GROUP_NAME string = resourceGroup.name
output STORAGE_ACCOUNT_NAME string = resources.outputs.STORAGE_ACCOUNT_NAME
output COGNITIVE_SERVICE_NAME string = resources.outputs.COGNITIVE_SERVICE_NAME
output APPINSIGHTS_INSTRUMENTATIONKEY string = resources.outputs.APPINSIGHTS_INSTRUMENTATIONKEY
output APPLICATIONINSIGHTS_CONNECTION_STRING string = resources.outputs.APPLICATIONINSIGHTS_CONNECTION_STRING
output DEPLOYMENT_ENVIRONMENT string = environment
output ACR_NAME string = resources.outputs.ACR_NAME
output ACR_LOGIN_SERVER string = resources.outputs.ACR_LOGIN_SERVER
