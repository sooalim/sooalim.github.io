<#
.SYNOPSIS
    Sets up the RAG Agent environment after infrastructure deployment.

.DESCRIPTION
    This script configures the RAG Agent environment including:
    - Azure Cognitive Search indexes
    - Storage account containers and initial data
    - Function app configuration
    - Key vault secrets
    - Application settings and environment variables

.PARAMETER EnvironmentName
    The environment name (dev, uat, prod).

.PARAMETER ResourceGroupName
    The name of the resource group containing the deployed resources.

.PARAMETER ProjectName
    The name of the project.

.PARAMETER ConfigFile
    Path to the configuration file containing environment setup parameters.

.PARAMETER SkipSearchIndexCreation
    Skip creation of search indexes.

.PARAMETER SkipDataInitialization
    Skip initialization of sample data.

.EXAMPLE
    .\setup-environment.ps1 -EnvironmentName "dev" -ResourceGroupName "rg-rag-agent-dev" -ProjectName "rag-agent"

.EXAMPLE
    .\setup-environment.ps1 -ConfigFile "config-prod.json" -SkipDataInitialization

.NOTES
    Author: RAG Agent Team
    Version: 1.0
    Requires: Azure PowerShell module
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory = $true)]
    [string]$EnvironmentName,
    
    [Parameter(Mandatory = $true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory = $true)]
    [string]$ProjectName,
    
    [Parameter(Mandatory = $false)]
    [string]$ConfigFile,
    
    [Parameter(Mandatory = $false)]
    [switch]$SkipSearchIndexCreation,
    
    [Parameter(Mandatory = $false)]
    [switch]$SkipDataInitialization
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Import required modules
try {
    Import-Module Az.Resources -Force
    Import-Module Az.Storage -Force
    Import-Module Az.KeyVault -Force
    Import-Module Az.CognitiveServices -Force
    Import-Module Az.Search -Force
    Import-Module Az.Functions -Force
    Import-Module Az.Websites -Force
}
catch {
    Write-Error "Failed to import required Azure PowerShell modules."
    exit 1
}

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    $originalColor = $Host.UI.RawUI.ForegroundColor
    $Host.UI.RawUI.ForegroundColor = $Color
    Write-Output $Message
    $Host.UI.RawUI.ForegroundColor = $originalColor
}

# Function to get resource names based on naming convention
function Get-ResourceNames {
    param(
        [string]$ProjectName,
        [string]$Environment
    )
    
    $uniqueSuffix = (Get-AzResourceGroup -Name $ResourceGroupName).Tags.UniqueSuffix
    if (-not $uniqueSuffix) {
        # Generate suffix if not available
        $uniqueSuffix = -join ((1..6) | ForEach-Object { Get-Random -Maximum 36 | ForEach-Object { [char]($_ + if ($_ -lt 10) { 48 } else { 55 }) } })
    }
    
    return @{
        StorageAccount = "st$($ProjectName.Replace('-', ''))$($Environment)$uniqueSuffix"
        FunctionApp = "func-$ProjectName-$Environment-$uniqueSuffix"
        SearchService = "srch-$ProjectName-$Environment-$uniqueSuffix"
        KeyVault = "kv-$ProjectName-$Environment-$uniqueSuffix"
        CognitiveServices = "cs-$ProjectName-$Environment-$uniqueSuffix"
    }
}

# Function to create search indexes
function New-SearchIndexes {
    param(
        [string]$SearchServiceName,
        [string]$ResourceGroupName
    )
    
    Write-ColorOutput "Creating search indexes..." "Yellow"
    
    # Get search service admin key
    $searchService = Get-AzSearchService -ResourceGroupName $ResourceGroupName -Name $SearchServiceName
    $adminKeys = Get-AzSearchAdminKeyPair -ResourceGroupName $ResourceGroupName -ServiceName $SearchServiceName
    
    $searchEndpoint = "https://$SearchServiceName.search.windows.net"
    $apiKey = $adminKeys.Primary
    
    # Define document index schema
    $documentIndexSchema = @{
        name = "documents"
        fields = @(
            @{
                name = "id"
                type = "Edm.String"
                key = $true
                searchable = $false
                filterable = $true
                retrievable = $true
            },
            @{
                name = "title"
                type = "Edm.String"
                key = $false
                searchable = $true
                filterable = $true
                retrievable = $true
                sortable = $true
            },
            @{
                name = "content"
                type = "Edm.String"
                key = $false
                searchable = $true
                filterable = $false
                retrievable = $true
                sortable = $false
            },
            @{
                name = "content_vector"
                type = "Collection(Edm.Single)"
                key = $false
                searchable = $true
                filterable = $false
                retrievable = $true
                sortable = $false
                dimensions = 1536
                vectorSearchProfile = "vector-profile"
            },
            @{
                name = "metadata"
                type = "Edm.String"
                key = $false
                searchable = $true
                filterable = $true
                retrievable = $true
                sortable = $false
            },
            @{
                name = "source"
                type = "Edm.String"
                key = $false
                searchable = $false
                filterable = $true
                retrievable = $true
                sortable = $true
            },
            @{
                name = "created_date"
                type = "Edm.DateTimeOffset"
                key = $false
                searchable = $false
                filterable = $true
                retrievable = $true
                sortable = $true
            },
            @{
                name = "modified_date"
                type = "Edm.DateTimeOffset"
                key = $false
                searchable = $false
                filterable = $true
                retrievable = $true
                sortable = $true
            }
        )
        vectorSearch = @{
            algorithms = @(
                @{
                    name = "vector-algorithm"
                    kind = "hnsw"
                    hnswParameters = @{
                        metric = "cosine"
                        m = 4
                        efConstruction = 400
                        efSearch = 500
                    }
                }
            )
            profiles = @(
                @{
                    name = "vector-profile"
                    algorithm = "vector-algorithm"
                }
            )
        }
        corsOptions = @{
            allowedOrigins = @("*")
            maxAgeInSeconds = 60
        }
    }
    
    # Create document index
    $headers = @{
        'api-key' = $apiKey
        'Content-Type' = 'application/json'
    }
    
    try {
        $response = Invoke-RestMethod -Uri "$searchEndpoint/indexes?api-version=2023-11-01" -Method POST -Headers $headers -Body ($documentIndexSchema | ConvertTo-Json -Depth 10)
        Write-ColorOutput "Document index created successfully" "Green"
    }
    catch {
        if ($_.Exception.Response.StatusCode -eq 409) {
            Write-ColorOutput "Document index already exists" "Yellow"
        }
        else {
            Write-Error "Failed to create document index: $($_.Exception.Message)"
        }
    }
    
    # Create chunk index schema
    $chunkIndexSchema = @{
        name = "chunks"
        fields = @(
            @{
                name = "id"
                type = "Edm.String"
                key = $true
                searchable = $false
                filterable = $true
                retrievable = $true
            },
            @{
                name = "document_id"
                type = "Edm.String"
                key = $false
                searchable = $false
                filterable = $true
                retrievable = $true
            },
            @{
                name = "chunk_text"
                type = "Edm.String"
                key = $false
                searchable = $true
                filterable = $false
                retrievable = $true
            },
            @{
                name = "chunk_vector"
                type = "Collection(Edm.Single)"
                key = $false
                searchable = $true
                filterable = $false
                retrievable = $true
                dimensions = 1536
                vectorSearchProfile = "vector-profile"
            },
            @{
                name = "chunk_index"
                type = "Edm.Int32"
                key = $false
                searchable = $false
                filterable = $true
                retrievable = $true
                sortable = $true
            },
            @{
                name = "token_count"
                type = "Edm.Int32"
                key = $false
                searchable = $false
                filterable = $true
                retrievable = $true
                sortable = $true
            }
        )
        vectorSearch = @{
            algorithms = @(
                @{
                    name = "vector-algorithm"
                    kind = "hnsw"
                    hnswParameters = @{
                        metric = "cosine"
                        m = 4
                        efConstruction = 400
                        efSearch = 500
                    }
                }
            )
            profiles = @(
                @{
                    name = "vector-profile"
                    algorithm = "vector-algorithm"
                }
            )
        }
        corsOptions = @{
            allowedOrigins = @("*")
            maxAgeInSeconds = 60
        }
    }
    
    # Create chunk index
    try {
        $response = Invoke-RestMethod -Uri "$searchEndpoint/indexes?api-version=2023-11-01" -Method POST -Headers $headers -Body ($chunkIndexSchema | ConvertTo-Json -Depth 10)
        Write-ColorOutput "Chunk index created successfully" "Green"
    }
    catch {
        if ($_.Exception.Response.StatusCode -eq 409) {
            Write-ColorOutput "Chunk index already exists" "Yellow"
        }
        else {
            Write-Error "Failed to create chunk index: $($_.Exception.Message)"
        }
    }
}

# Function to configure storage account
function Set-StorageConfiguration {
    param(
        [string]$StorageAccountName,
        [string]$ResourceGroupName
    )
    
    Write-ColorOutput "Configuring storage account..." "Yellow"
    
    # Get storage account context
    $storageAccount = Get-AzStorageAccount -ResourceGroupName $ResourceGroupName -Name $StorageAccountName
    $ctx = $storageAccount.Context
    
    # Verify containers exist (they should be created by Bicep)
    $containers = @("documents", "processed", "vectors", "logs")
    foreach ($container in $containers) {
        $containerObj = Get-AzStorageContainer -Name $container -Context $ctx -ErrorAction SilentlyContinue
        if (-not $containerObj) {
            Write-ColorOutput "Creating container: $container" "Yellow"
            New-AzStorageContainer -Name $container -Context $ctx -Permission Off
        }
        else {
            Write-ColorOutput "Container already exists: $container" "Cyan"
        }
    }
    
    # Configure CORS for storage account
    $corsRules = @(
        @{
            AllowedOrigins = @("https://portal.azure.com", "https://ms.portal.azure.com")
            AllowedMethods = @("GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS")
            AllowedHeaders = @("*")
            ExposedHeaders = @("*")
            MaxAgeInSeconds = 3600
        }
    )
    
    Set-AzStorageCORSRule -ServiceType Blob -CorsRules $corsRules -Context $ctx
    Write-ColorOutput "Storage account CORS configured" "Green"
}

# Function to configure function app settings
function Set-FunctionAppSettings {
    param(
        [string]$FunctionAppName,
        [string]$ResourceGroupName,
        [hashtable]$ResourceNames
    )
    
    Write-ColorOutput "Configuring function app settings..." "Yellow"
    
    # Get existing app settings
    $functionApp = Get-AzWebApp -ResourceGroupName $ResourceGroupName -Name $FunctionAppName
    $appSettings = $functionApp.SiteConfig.AppSettings
    
    # Create hashtable of current settings
    $currentSettings = @{}
    foreach ($setting in $appSettings) {
        $currentSettings[$setting.Name] = $setting.Value
    }
    
    # Add RAG-specific settings
    $currentSettings["SEARCH_SERVICE_NAME"] = $ResourceNames.SearchService
    $currentSettings["SEARCH_SERVICE_ENDPOINT"] = "https://$($ResourceNames.SearchService).search.windows.net"
    $currentSettings["STORAGE_ACCOUNT_NAME"] = $ResourceNames.StorageAccount
    $currentSettings["COGNITIVE_SERVICES_ENDPOINT"] = "https://$($ResourceNames.CognitiveServices).cognitiveservices.azure.com"
    $currentSettings["DOCUMENTS_CONTAINER"] = "documents"
    $currentSettings["PROCESSED_CONTAINER"] = "processed"
    $currentSettings["VECTORS_CONTAINER"] = "vectors"
    $currentSettings["LOGS_CONTAINER"] = "logs"
    $currentSettings["DOCUMENT_INDEX_NAME"] = "documents"
    $currentSettings["CHUNK_INDEX_NAME"] = "chunks"
    $currentSettings["CHUNK_SIZE"] = "1000"
    $currentSettings["CHUNK_OVERLAP"] = "100"
    $currentSettings["MAX_TOKENS"] = "4000"
    $currentSettings["EMBEDDING_MODEL"] = "text-embedding-ada-002"
    $currentSettings["COMPLETION_MODEL"] = "gpt-35-turbo"
    $currentSettings["TEMPERATURE"] = "0.7"
    $currentSettings["MAX_SEARCH_RESULTS"] = "10"
    $currentSettings["SEARCH_SCORE_THRESHOLD"] = "0.8"
    
    # Update function app settings
    Set-AzWebApp -ResourceGroupName $ResourceGroupName -Name $FunctionAppName -AppSettings $currentSettings
    Write-ColorOutput "Function app settings updated" "Green"
}

# Function to initialize sample data
function Initialize-SampleData {
    param(
        [string]$StorageAccountName,
        [string]$ResourceGroupName
    )
    
    Write-ColorOutput "Initializing sample data..." "Yellow"
    
    # Get storage account context
    $storageAccount = Get-AzStorageAccount -ResourceGroupName $ResourceGroupName -Name $StorageAccountName
    $ctx = $storageAccount.Context
    
    # Create sample documents
    $sampleDocuments = @(
        @{
            Name = "sample-document-1.txt"
            Content = @"
# RAG Agent Documentation

## Overview
This document provides an overview of the RAG (Retrieval-Augmented Generation) agent system.

## Architecture
The RAG agent consists of several components:
- Data extraction pipeline
- Vector embedding generation
- Search and retrieval system
- Response generation

## Features
- Intelligent document processing
- Semantic search capabilities
- Context-aware responses
- Continuous learning and improvement

## Usage
To use the RAG agent, submit queries through the chat interface. The system will:
1. Process your query
2. Search relevant documents
3. Generate contextual responses
4. Provide source citations
"@
        },
        @{
            Name = "sample-document-2.txt"
            Content = @"
# Technical Implementation Guide

## Data Processing Pipeline
The data processing pipeline handles document ingestion and preparation:

### Document Extraction
- Supports multiple file formats (PDF, Word, HTML, Text)
- Extracts text content and metadata
- Handles tables, images, and structured data

### Text Chunking
- Implements semantic chunking strategies
- Maintains context across chunks
- Optimizes chunk size for embedding models

### Vector Embedding
- Uses Azure OpenAI embedding models
- Generates high-dimensional vector representations
- Stores embeddings in Azure Cognitive Search

## Search and Retrieval
The system uses hybrid search combining:
- Semantic vector search
- Keyword-based search
- Relevance scoring and ranking

## Response Generation
- Contextual prompt engineering
- Citation and source tracking
- Quality control and filtering
"@
        }
    )
    
    # Upload sample documents
    foreach ($doc in $sampleDocuments) {
        $blob = Set-AzStorageBlobContent -File ($doc.Content | Out-String) -Container "documents" -Blob $doc.Name -Context $ctx -Force
        Write-ColorOutput "Uploaded sample document: $($doc.Name)" "Green"
    }
    
    Write-ColorOutput "Sample data initialization completed" "Green"
}

# Function to test environment setup
function Test-EnvironmentSetup {
    param(
        [hashtable]$ResourceNames,
        [string]$ResourceGroupName
    )
    
    Write-ColorOutput "Testing environment setup..." "Yellow"
    
    $testResults = @()
    
    # Test storage account
    try {
        $storageAccount = Get-AzStorageAccount -ResourceGroupName $ResourceGroupName -Name $ResourceNames.StorageAccount
        $testResults += @{ Service = "Storage Account"; Status = "Success"; Message = "Storage account accessible" }
    }
    catch {
        $testResults += @{ Service = "Storage Account"; Status = "Failed"; Message = $_.Exception.Message }
    }
    
    # Test function app
    try {
        $functionApp = Get-AzWebApp -ResourceGroupName $ResourceGroupName -Name $ResourceNames.FunctionApp
        $testResults += @{ Service = "Function App"; Status = "Success"; Message = "Function app accessible" }
    }
    catch {
        $testResults += @{ Service = "Function App"; Status = "Failed"; Message = $_.Exception.Message }
    }
    
    # Test search service
    try {
        $searchService = Get-AzSearchService -ResourceGroupName $ResourceGroupName -Name $ResourceNames.SearchService
        $testResults += @{ Service = "Search Service"; Status = "Success"; Message = "Search service accessible" }
    }
    catch {
        $testResults += @{ Service = "Search Service"; Status = "Failed"; Message = $_.Exception.Message }
    }
    
    # Test key vault
    try {
        $keyVault = Get-AzKeyVault -ResourceGroupName $ResourceGroupName -VaultName $ResourceNames.KeyVault
        $testResults += @{ Service = "Key Vault"; Status = "Success"; Message = "Key vault accessible" }
    }
    catch {
        $testResults += @{ Service = "Key Vault"; Status = "Failed"; Message = $_.Exception.Message }
    }
    
    # Display test results
    Write-ColorOutput "Environment Test Results:" "Cyan"
    Write-ColorOutput "========================" "Cyan"
    foreach ($result in $testResults) {
        $color = if ($result.Status -eq "Success") { "Green" } else { "Red" }
        Write-ColorOutput "$($result.Service): $($result.Status) - $($result.Message)" $color
    }
    
    $failedTests = $testResults | Where-Object { $_.Status -eq "Failed" }
    if ($failedTests.Count -gt 0) {
        Write-Error "Environment setup validation failed. Please check the failed services."
        return $false
    }
    else {
        Write-ColorOutput "All environment tests passed!" "Green"
        return $true
    }
}

# Main execution
try {
    Write-ColorOutput "Starting RAG Agent Environment Setup" "Cyan"
    Write-ColorOutput "====================================" "Cyan"
    
    # Get resource names
    $resourceNames = Get-ResourceNames -ProjectName $ProjectName -Environment $EnvironmentName
    
    Write-ColorOutput "Resource Names:" "Cyan"
    foreach ($resource in $resourceNames.GetEnumerator()) {
        Write-ColorOutput "$($resource.Key): $($resource.Value)" "White"
    }
    
    # Configure storage account
    Set-StorageConfiguration -StorageAccountName $resourceNames.StorageAccount -ResourceGroupName $ResourceGroupName
    
    # Create search indexes
    if (-not $SkipSearchIndexCreation) {
        New-SearchIndexes -SearchServiceName $resourceNames.SearchService -ResourceGroupName $ResourceGroupName
    }
    else {
        Write-ColorOutput "Skipping search index creation" "Yellow"
    }
    
    # Configure function app
    Set-FunctionAppSettings -FunctionAppName $resourceNames.FunctionApp -ResourceGroupName $ResourceGroupName -ResourceNames $resourceNames
    
    # Initialize sample data
    if (-not $SkipDataInitialization) {
        Initialize-SampleData -StorageAccountName $resourceNames.StorageAccount -ResourceGroupName $ResourceGroupName
    }
    else {
        Write-ColorOutput "Skipping data initialization" "Yellow"
    }
    
    # Test environment setup
    if (Test-EnvironmentSetup -ResourceNames $resourceNames -ResourceGroupName $ResourceGroupName) {
        Write-ColorOutput "Environment setup completed successfully!" "Green"
        
        # Display summary
        Write-ColorOutput "Environment Setup Summary:" "Cyan"
        Write-ColorOutput "=========================" "Cyan"
        Write-ColorOutput "Environment: $EnvironmentName" "White"
        Write-ColorOutput "Resource Group: $ResourceGroupName" "White"
        Write-ColorOutput "Project: $ProjectName" "White"
        Write-ColorOutput "Storage Account: $($resourceNames.StorageAccount)" "White"
        Write-ColorOutput "Function App: $($resourceNames.FunctionApp)" "White"
        Write-ColorOutput "Search Service: $($resourceNames.SearchService)" "White"
        Write-ColorOutput "Key Vault: $($resourceNames.KeyVault)" "White"
        
        Write-ColorOutput "Next steps:" "Yellow"
        Write-ColorOutput "1. Deploy function app code" "White"
        Write-ColorOutput "2. Configure Copilot Studio integration" "White"
        Write-ColorOutput "3. Set up monitoring and alerts" "White"
        Write-ColorOutput "4. Begin UAT testing" "White"
    }
    else {
        Write-Error "Environment setup validation failed"
        exit 1
    }
}
catch {
    Write-Error "Environment setup failed with error: $($_.Exception.Message)"
    exit 1
}
finally {
    Write-ColorOutput "Environment setup script completed." "Cyan"
}
