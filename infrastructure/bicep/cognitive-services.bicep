@description('Cognitive Services account name')
param cognitiveServicesName string

@description('Location for the Cognitive Services account')
param location string

@description('Tags to be applied to the Cognitive Services account')
param tags object

@description('Cognitive Services SKU')
param skuName string = 'S0'

@description('Azure OpenAI API Key')
@secure()
param openAIApiKey string

@description('Enable public network access')
param publicNetworkAccess string = 'Enabled'

@description('Disable local authentication')
param disableLocalAuth bool = false

// Cognitive Services Multi-Service Account
resource cognitiveServices 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: cognitiveServicesName
  location: location
  tags: tags
  sku: {
    name: skuName
  }
  kind: 'CognitiveServices'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    apiProperties: {}
    customSubDomainName: cognitiveServicesName
    disableLocalAuth: disableLocalAuth
    encryption: {
      keySource: 'Microsoft.CognitiveServices'
    }
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
    }
    publicNetworkAccess: publicNetworkAccess
    restrictOutboundNetworkAccess: false
    userOwnedStorage: []
  }
}

// Azure OpenAI Service
resource openAIService 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: '${cognitiveServicesName}-openai'
  location: location
  tags: tags
  sku: {
    name: 'S0'
  }
  kind: 'OpenAI'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    apiProperties: {}
    customSubDomainName: '${cognitiveServicesName}-openai'
    disableLocalAuth: disableLocalAuth
    encryption: {
      keySource: 'Microsoft.CognitiveServices'
    }
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
    }
    publicNetworkAccess: publicNetworkAccess
    restrictOutboundNetworkAccess: false
    userOwnedStorage: []
  }
}

// OpenAI Deployments
resource gpt35TurboDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openAIService
  name: 'gpt-35-turbo'
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-35-turbo'
      version: '0613'
    }
    scaleSettings: {
      scaleType: 'Standard'
      capacity: 30
    }
  }
}

resource gpt4Deployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openAIService
  name: 'gpt-4'
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4'
      version: '0613'
    }
    scaleSettings: {
      scaleType: 'Standard'
      capacity: 10
    }
  }
}

resource textEmbeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openAIService
  name: 'text-embedding-ada-002'
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-ada-002'
      version: '2'
    }
    scaleSettings: {
      scaleType: 'Standard'
      capacity: 30
    }
  }
}

// Form Recognizer for document processing
resource formRecognizer 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: '${cognitiveServicesName}-formrecognizer'
  location: location
  tags: tags
  sku: {
    name: 'S0'
  }
  kind: 'FormRecognizer'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    apiProperties: {}
    customSubDomainName: '${cognitiveServicesName}-formrecognizer'
    disableLocalAuth: disableLocalAuth
    encryption: {
      keySource: 'Microsoft.CognitiveServices'
    }
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
    }
    publicNetworkAccess: publicNetworkAccess
    restrictOutboundNetworkAccess: false
    userOwnedStorage: []
  }
}

// Text Analytics for additional NLP capabilities
resource textAnalytics 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: '${cognitiveServicesName}-textanalytics'
  location: location
  tags: tags
  sku: {
    name: 'S'
  }
  kind: 'TextAnalytics'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    apiProperties: {}
    customSubDomainName: '${cognitiveServicesName}-textanalytics'
    disableLocalAuth: disableLocalAuth
    encryption: {
      keySource: 'Microsoft.CognitiveServices'
    }
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
    }
    publicNetworkAccess: publicNetworkAccess
    restrictOutboundNetworkAccess: false
    userOwnedStorage: []
  }
}

// Outputs
output cognitiveServicesName string = cognitiveServices.name
output cognitiveServicesId string = cognitiveServices.id
output cognitiveServicesEndpoint string = cognitiveServices.properties.endpoint
output cognitiveServicesKey string = cognitiveServices.listKeys().key1
output openAIServiceName string = openAIService.name
output openAIServiceId string = openAIService.id
output openAIServiceEndpoint string = openAIService.properties.endpoint
output openAIServiceKey string = openAIService.listKeys().key1
output formRecognizerName string = formRecognizer.name
output formRecognizerEndpoint string = formRecognizer.properties.endpoint
output formRecognizerKey string = formRecognizer.listKeys().key1
output textAnalyticsName string = textAnalytics.name
output textAnalyticsEndpoint string = textAnalytics.properties.endpoint
output textAnalyticsKey string = textAnalytics.listKeys().key1
