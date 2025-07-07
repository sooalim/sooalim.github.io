@description('Search service name')
param searchServiceName string

@description('Location for the Search service')
param location string

@description('Tags to be applied to the Search service')
param tags object

@description('Search service SKU')
param skuName string = 'basic'

@description('Number of replicas')
param replicaCount int = 1

@description('Number of partitions')
param partitionCount int = 1

@description('Host network access')
param hostingMode string = 'default'

@description('Public network access')
param publicNetworkAccess string = 'enabled'

@description('Semantic search configuration')
param semanticSearch string = 'free'

// Azure Cognitive Search Service
resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: searchServiceName
  location: location
  tags: tags
  sku: {
    name: skuName
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    replicaCount: replicaCount
    partitionCount: partitionCount
    hostingMode: hostingMode
    publicNetworkAccess: publicNetworkAccess
    networkRuleSet: {
      ipRules: []
      bypass: 'None'
    }
    encryptionWithCmk: {
      enforcement: 'Unspecified'
    }
    disableLocalAuth: false
    authOptions: {
      apiKeyOnly: {}
    }
    semanticSearch: semanticSearch
  }
}

// Shared Private Link Resources for secure connections
resource sharedPrivateLink 'Microsoft.Search/searchServices/sharedPrivateLinkResources@2023-11-01' = {
  parent: searchService
  name: 'blob-storage-connection'
  properties: {
    privateLinkResourceId: '/subscriptions/${subscription().subscriptionId}/resourceGroups/${resourceGroup().name}/providers/Microsoft.Storage/storageAccounts/${searchServiceName}storage'
    groupId: 'blob'
    requestMessage: 'Please approve this connection for RAG data indexing'
  }
}

// Outputs
output searchServiceName string = searchService.name
output searchServiceId string = searchService.id
output searchServiceEndpoint string = 'https://${searchService.name}.search.windows.net'
output searchApiKey string = searchService.listAdminKeys().primaryKey
output searchQueryKey string = searchService.listQueryKeys().value[0].key
output searchServicePrincipalId string = searchService.identity.principalId
