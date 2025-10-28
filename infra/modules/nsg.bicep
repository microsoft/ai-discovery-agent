@description('Network Security Group for App Service subnet')
param location string = resourceGroup().location
param namePrefix string

resource appSubnetNsg 'Microsoft.Network/networkSecurityGroups@2023-05-01' = {
  name: '${namePrefix}-app-subnet-nsg'
  location: location
  properties: {
    securityRules: [
      {
        name: 'AllowOutboundHTTPS'
        properties: {
          description: 'Allow outbound HTTPS for OAuth providers'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '443'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: 'Internet'
          access: 'Allow'
          priority: 100
          direction: 'Outbound'
        }
      }
      {
        name: 'AllowOutboundDNS'
        properties: {
          description: 'Allow outbound DNS'
          protocol: 'Udp'
          sourcePortRange: '*'
          destinationPortRange: '53'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: 'Internet'
          access: 'Allow'
          priority: 110
          direction: 'Outbound'
        }
      }
      {
        name: 'AllowVnetInbound'
        properties: {
          description: 'Allow inbound from VNet'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: 'VirtualNetwork'
          access: 'Allow'
          priority: 120
          direction: 'Inbound'
        }
      }
      {
        name: 'AllowAzureLoadBalancerInbound'
        properties: {
          description: 'Allow Azure Load Balancer'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: 'AzureLoadBalancer'
          destinationAddressPrefix: '*'
          access: 'Allow'
          priority: 130
          direction: 'Inbound'
        }
      }
    ]
  }
}

output nsgId string = appSubnetNsg.id
output nsgName string = appSubnetNsg.name
