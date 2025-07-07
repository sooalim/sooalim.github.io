@description('Function App name')
param functionAppName string

@description('Location for the Function App')
param location string

@description('Tags to be applied to the Function App')
param tags object

@description('Storage account name for Function App')
param storageAccountName string

@description('Storage account key for Function App')
@secure()
param storageAccountKey string

@description('Application Insights instrumentation key')
@secure()
param applicationInsightsKey string

@description('Key Vault name for secrets')
param keyVaultName string

@description('Function App SKU name')
param skuName string = 'Y1'

@description('Function App SKU tier')
param skuTier string = 'Dynamic'

@description('Python runtime version')
param pythonVersion string = '3.11'

@description('Enable managed identity')
param enableManagedIdentity bool = true

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: 'asp-${functionAppName}'
  location: location
  tags: tags
  sku: {
    name: skuName
    tier: skuTier
  }
  kind: 'functionapp'
  properties: {
    reserved: true // Required for Linux
  }
}

// Function App
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  tags: tags
  kind: 'functionapp,linux'
  identity: enableManagedIdentity ? {
    type: 'SystemAssigned'
  } : null
  properties: {
    serverFarmId: appServicePlan.id
    reserved: true
    isXenon: false
    hyperV: false
    vnetRouteAllEnabled: false
    vnetImagePullEnabled: false
    vnetContentShareEnabled: false
    siteConfig: {
      numberOfWorkers: 1
      linuxFxVersion: 'Python|${pythonVersion}'
      acrUseManagedIdentityCreds: false
      alwaysOn: false
      http20Enabled: false
      functionAppScaleLimit: 200
      minimumElasticInstanceCount: 0
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};AccountKey=${storageAccountKey};EndpointSuffix=core.windows.net'
        }
        {
          name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};AccountKey=${storageAccountKey};EndpointSuffix=core.windows.net'
        }
        {
          name: 'WEBSITE_CONTENTSHARE'
          value: toLower(functionAppName)
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: applicationInsightsKey
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: 'InstrumentationKey=${applicationInsightsKey}'
        }
        {
          name: 'PYTHON_ISOLATE_WORKER_DEPENDENCIES'
          value: '1'
        }
        {
          name: 'KEY_VAULT_NAME'
          value: keyVaultName
        }
        {
          name: 'AZURE_CLIENT_ID'
          value: enableManagedIdentity ? functionApp.identity.principalId : ''
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: '1'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: '1'
        }
      ]
      cors: {
        allowedOrigins: [
          'https://portal.azure.com'
          'https://ms.portal.azure.com'
        ]
        supportCredentials: false
      }
      use32BitWorkerProcess: false
      ftpsState: 'FtpsOnly'
      netFrameworkVersion: 'v6.0'
      powerShellVersion: '~7'
      preWarmedInstanceCount: 0
      publicNetworkAccess: 'Enabled'
    }
    scmSiteAlsoStopped: false
    clientAffinityEnabled: false
    clientCertEnabled: false
    clientCertMode: 'Required'
    hostNamesDisabled: false
    containerSize: 1536
    dailyMemoryTimeQuota: 0
    httpsOnly: true
    redundancyMode: 'None'
    publicNetworkAccess: 'Enabled'
    storageAccountRequired: false
    keyVaultReferenceIdentity: 'SystemAssigned'
  }
}

// Function App Slots (for deployment)
resource functionAppSlot 'Microsoft.Web/sites/slots@2023-01-01' = {
  parent: functionApp
  name: 'staging'
  location: location
  tags: tags
  kind: 'functionapp,linux'
  identity: enableManagedIdentity ? {
    type: 'SystemAssigned'
  } : null
  properties: {
    serverFarmId: appServicePlan.id
    reserved: true
    isXenon: false
    hyperV: false
    vnetRouteAllEnabled: false
    vnetImagePullEnabled: false
    vnetContentShareEnabled: false
    siteConfig: {
      numberOfWorkers: 1
      linuxFxVersion: 'Python|${pythonVersion}'
      acrUseManagedIdentityCreds: false
      alwaysOn: false
      http20Enabled: false
      functionAppScaleLimit: 200
      minimumElasticInstanceCount: 0
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};AccountKey=${storageAccountKey};EndpointSuffix=core.windows.net'
        }
        {
          name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};AccountKey=${storageAccountKey};EndpointSuffix=core.windows.net'
        }
        {
          name: 'WEBSITE_CONTENTSHARE'
          value: toLower('${functionAppName}-staging')
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: applicationInsightsKey
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: 'InstrumentationKey=${applicationInsightsKey}'
        }
        {
          name: 'PYTHON_ISOLATE_WORKER_DEPENDENCIES'
          value: '1'
        }
        {
          name: 'KEY_VAULT_NAME'
          value: keyVaultName
        }
        {
          name: 'AZURE_CLIENT_ID'
          value: enableManagedIdentity ? functionAppSlot.identity.principalId : ''
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: '1'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: '1'
        }
      ]
      cors: {
        allowedOrigins: [
          'https://portal.azure.com'
          'https://ms.portal.azure.com'
        ]
        supportCredentials: false
      }
      use32BitWorkerProcess: false
      ftpsState: 'FtpsOnly'
      netFrameworkVersion: 'v6.0'
      powerShellVersion: '~7'
      preWarmedInstanceCount: 0
      publicNetworkAccess: 'Enabled'
    }
    scmSiteAlsoStopped: false
    clientAffinityEnabled: false
    clientCertEnabled: false
    clientCertMode: 'Required'
    hostNamesDisabled: false
    containerSize: 1536
    dailyMemoryTimeQuota: 0
    httpsOnly: true
    redundancyMode: 'None'
    publicNetworkAccess: 'Enabled'
    storageAccountRequired: false
    keyVaultReferenceIdentity: 'SystemAssigned'
  }
}

// Key Vault access for managed identity
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' existing = {
  name: keyVaultName
}

resource keyVaultAccessPolicy 'Microsoft.KeyVault/vaults/accessPolicies@2023-02-01' = if (enableManagedIdentity) {
  parent: keyVault
  name: 'add'
  properties: {
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: functionApp.identity.principalId
        permissions: {
          secrets: [
            'get'
            'list'
          ]
        }
      }
    ]
  }
}

// Outputs
output functionAppName string = functionApp.name
output functionAppId string = functionApp.id
output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
output functionAppPrincipalId string = enableManagedIdentity ? functionApp.identity.principalId : ''
output appServicePlanName string = appServicePlan.name
output appServicePlanId string = appServicePlan.id
output stagingSlotName string = functionAppSlot.name
output stagingSlotUrl string = 'https://${functionAppSlot.properties.defaultHostName}'
