@description('Storage account name')
param storageAccountName string

@description('Location for the storage account')
param location string

@description('Tags to be applied to the storage account')
param tags object

@description('Storage account SKU')
param skuName string = 'Standard_LRS'

@description('Enable blob public access')
param allowBlobPublicAccess bool = false

@description('Enable shared key access')
param allowSharedKeyAccess bool = true

@description('Minimum TLS version')
param minimumTlsVersion string = 'TLS1_2'

// Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: skuName
  }
  kind: 'StorageV2'
  properties: {
    dnsEndpointType: 'Standard'
    defaultToOAuthAuthentication: false
    publicNetworkAccess: 'Enabled'
    allowCrossTenantReplication: false
    minimumTlsVersion: minimumTlsVersion
    allowBlobPublicAccess: allowBlobPublicAccess
    allowSharedKeyAccess: allowSharedKeyAccess
    networkAcls: {
      bypass: 'AzureServices'
      virtualNetworkRules: []
      ipRules: []
      defaultAction: 'Allow'
    }
    supportsHttpsTrafficOnly: true
    encryption: {
      requireInfrastructureEncryption: false
      services: {
        file: {
          keyType: 'Account'
          enabled: true
        }
        blob: {
          keyType: 'Account'
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
    accessTier: 'Hot'
  }
}

// Blob Services
resource blobServices 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    changeFeed: {
      enabled: false
    }
    restorePolicy: {
      enabled: false
    }
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    cors: {
      corsRules: []
    }
    deleteRetentionPolicy: {
      allowPermanentDelete: false
      enabled: true
      days: 7
    }
    isVersioningEnabled: false
  }
}

// Containers
resource documentsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobServices
  name: 'documents'
  properties: {
    immutableStorageWithVersioning: {
      enabled: false
    }
    defaultEncryptionScope: '$account-encryption-key'
    denyEncryptionScopeOverride: false
    publicAccess: 'None'
  }
}

resource processedContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobServices
  name: 'processed'
  properties: {
    immutableStorageWithVersioning: {
      enabled: false
    }
    defaultEncryptionScope: '$account-encryption-key'
    denyEncryptionScopeOverride: false
    publicAccess: 'None'
  }
}

resource vectorsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobServices
  name: 'vectors'
  properties: {
    immutableStorageWithVersioning: {
      enabled: false
    }
    defaultEncryptionScope: '$account-encryption-key'
    denyEncryptionScopeOverride: false
    publicAccess: 'None'
  }
}

resource logsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobServices
  name: 'logs'
  properties: {
    immutableStorageWithVersioning: {
      enabled: false
    }
    defaultEncryptionScope: '$account-encryption-key'
    denyEncryptionScopeOverride: false
    publicAccess: 'None'
  }
}

// File Services
resource fileServices 'Microsoft.Storage/storageAccounts/fileServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    protocolSettings: {
      smb: {
        versions: 'SMB2.1;SMB3.0;SMB3.1.1'
        authenticationMethods: 'NTLMv2;Kerberos'
        kerberosTicketEncryption: 'RC4-HMAC;AES-256'
        channelEncryption: 'AES-128-CCM;AES-128-GCM;AES-256-GCM'
      }
    }
    corsRules: []
    shareDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}

// File Shares
resource configShare 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-01-01' = {
  parent: fileServices
  name: 'config'
  properties: {
    accessTier: 'TransactionOptimized'
    shareQuota: 5120
    enabledProtocols: 'SMB'
  }
}

resource tempShare 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-01-01' = {
  parent: fileServices
  name: 'temp'
  properties: {
    accessTier: 'TransactionOptimized'
    shareQuota: 5120
    enabledProtocols: 'SMB'
  }
}

// Queue Services
resource queueServices 'Microsoft.Storage/storageAccounts/queueServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    corsRules: []
  }
}

// Queues
resource processingQueue 'Microsoft.Storage/storageAccounts/queueServices/queues@2023-01-01' = {
  parent: queueServices
  name: 'data-processing'
  properties: {
    metadata: {}
  }
}

resource refreshQueue 'Microsoft.Storage/storageAccounts/queueServices/queues@2023-01-01' = {
  parent: queueServices
  name: 'data-refresh'
  properties: {
    metadata: {}
  }
}

// Table Services
resource tableServices 'Microsoft.Storage/storageAccounts/tableServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    corsRules: []
  }
}

// Tables
resource metadataTable 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-01-01' = {
  parent: tableServices
  name: 'metadata'
  properties: {}
}

resource processingStatusTable 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-01-01' = {
  parent: tableServices
  name: 'processingstatus'
  properties: {}
}

// Outputs
output storageAccountName string = storageAccount.name
output storageAccountId string = storageAccount.id
output storageConnectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
output storageAccountKey string = storageAccount.listKeys().keys[0].value
output blobEndpoint string = storageAccount.properties.primaryEndpoints.blob
output fileEndpoint string = storageAccount.properties.primaryEndpoints.file
output queueEndpoint string = storageAccount.properties.primaryEndpoints.queue
output tableEndpoint string = storageAccount.properties.primaryEndpoints.table
