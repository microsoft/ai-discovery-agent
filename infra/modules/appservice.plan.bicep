param resourceToken string
param location string = resourceGroup().location
param kind string = 'linux'
param sku object = {
    name: 'S1'
    tier: 'Standard'
    capacity: 1
  }
param tags object = {}


resource appServicePlan 'Microsoft.Web/serverfarms@2024-11-01' = {
  //checkov:skip=CKV_AZURE_225
  name: 'app-${resourceToken}'
  location: location
  sku: sku
  kind: kind
  properties: {
    reserved: true
    perSiteScaling: false
    elasticScaleEnabled: false
    maximumElasticWorkerCount: 1
    isSpot: false
    targetWorkerCount: 0
    targetWorkerSizeId: 0
  }
  tags: tags
}

output id string = appServicePlan.id
output name string = appServicePlan.name
