@description('The name of the project')
param projectName string

@description('The deployment environment (dev, uat, prod)')
param environment string

@description('The Azure region for deployment')
param location string = resourceGroup().location

@description('Tags to be applied to all resources')
param tags object = {
  Environment: environment
  Project: projectName
  DeployedBy: 'Bicep'
  CreatedDate: utcNow('yyyy-MM-dd')
}

@description('Azure OpenAI API Key')
@secure()
param openAIApiKey string

@description('Storage account SKU')
param storageAccountSku string = 'Standard_LRS'

@description('Function App service plan SKU')
param functionAppSkuName string = 'Y1'
param functionAppSkuTier string = 'Dynamic'

@description('Search service SKU')
param searchServiceSku string = 'basic'

@description('Enable Application Insights')
param enableApplicationInsights bool = true

@description('Key Vault SKU')
param keyVaultSku string = 'standard'

// Variables
var uniqueSuffix = substring(uniqueString(resourceGroup().id), 0, 6)
var resourceNamePrefix = '${projectName}-${environment}'

// Storage Account
module storageAccount 'storage.bicep' = {
  name: 'storage-deployment'
  params: {
    storageAccountName: 'st${replace(resourceNamePrefix, '-', '')}${uniqueSuffix}'
    location: location
    tags: tags
    skuName: storageAccountSku
  }
}

// Cognitive Services (OpenAI)
module cognitiveServices 'cognitive-services.bicep' = {
  name: 'cognitive-services-deployment'
  params: {
    cognitiveServicesName: 'cs-${resourceNamePrefix}-${uniqueSuffix}'
    location: location
    tags: tags
    openAIApiKey: openAIApiKey
  }
}

// Azure Cognitive Search
module searchService 'search.bicep' = {
  name: 'search-deployment'
  params: {
    searchServiceName: 'srch-${resourceNamePrefix}-${uniqueSuffix}'
    location: location
    tags: tags
    skuName: searchServiceSku
  }
}

// Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: 'kv-${resourceNamePrefix}-${uniqueSuffix}'
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: keyVaultSku
    }
    tenantId: subscription().tenantId
    accessPolicies: []
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enableRbacAuthorization: true
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// Application Insights
resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = if (enableApplicationInsights) {
  name: 'ai-${resourceNamePrefix}-${uniqueSuffix}'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Flow_Type: 'Bluefield'
    Request_Source: 'rest'
    RetentionInDays: 90
    WorkspaceResourceId: logAnalyticsWorkspace.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Log Analytics Workspace
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'law-${resourceNamePrefix}-${uniqueSuffix}'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 90
    features: {
      searchVersion: 1
      legacy: 0
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    workspaceCapping: {
      dailyQuotaGb: -1
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Azure Functions
module functionApp 'functions.bicep' = {
  name: 'functions-deployment'
  params: {
    functionAppName: 'func-${resourceNamePrefix}-${uniqueSuffix}'
    location: location
    tags: tags
    storageAccountName: storageAccount.outputs.storageAccountName
    storageAccountKey: storageAccount.outputs.storageAccountKey
    applicationInsightsKey: enableApplicationInsights ? applicationInsights.properties.InstrumentationKey : ''
    skuName: functionAppSkuName
    skuTier: functionAppSkuTier
    keyVaultName: keyVault.name
  }
}

// Store secrets in Key Vault
resource openAIKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
  parent: keyVault
  name: 'openai-api-key'
  properties: {
    value: openAIApiKey
    attributes: {
      enabled: true
    }
  }
}

resource storageConnectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
  parent: keyVault
  name: 'storage-connection-string'
  properties: {
    value: storageAccount.outputs.storageConnectionString
    attributes: {
      enabled: true
    }
  }
}

resource searchApiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
  parent: keyVault
  name: 'search-api-key'
  properties: {
    value: searchService.outputs.searchApiKey
    attributes: {
      enabled: true
    }
  }
}

// Outputs
output storageAccountName string = storageAccount.outputs.storageAccountName
output storageConnectionString string = storageAccount.outputs.storageConnectionString
output functionAppName string = functionApp.outputs.functionAppName
output searchServiceName string = searchService.outputs.searchServiceName
output searchApiKey string = searchService.outputs.searchApiKey
output keyVaultName string = keyVault.name
output applicationInsightsName string = enableApplicationInsights ? applicationInsights.name : ''
output applicationInsightsKey string = enableApplicationInsights ? applicationInsights.properties.InstrumentationKey : ''
output resourceGroupName string = resourceGroup().name
output cognitiveServicesEndpoint string = cognitiveServices.outputs.cognitiveServicesEndpoint
output cognitiveServicesName string = cognitiveServices.outputs.cognitiveServicesName
