<#
.SYNOPSIS
    Deploys the RAG Agent infrastructure to Azure using Bicep templates.

.DESCRIPTION
    This script deploys the complete RAG Agent infrastructure including:
    - Azure Storage Account
    - Azure Cognitive Services (OpenAI, Form Recognizer, Text Analytics)
    - Azure Cognitive Search
    - Azure Functions
    - Key Vault
    - Application Insights
    - Log Analytics Workspace

.PARAMETER SubscriptionId
    The Azure subscription ID to deploy to.

.PARAMETER ResourceGroupName
    The name of the resource group to deploy to.

.PARAMETER Location
    The Azure region to deploy to.

.PARAMETER Environment
    The environment name (dev, uat, prod).

.PARAMETER ProjectName
    The name of the project.

.PARAMETER OpenAIApiKey
    The OpenAI API key (secure string).

.PARAMETER ConfigFile
    Path to the configuration file containing deployment parameters.

.PARAMETER WhatIf
    Runs the deployment in what-if mode to preview changes.

.PARAMETER Force
    Forces the deployment without confirmation prompts.

.EXAMPLE
    .\deploy-infrastructure.ps1 -SubscriptionId "12345678-1234-1234-1234-123456789012" -ResourceGroupName "rg-rag-agent-dev" -Location "East US 2" -Environment "dev" -ProjectName "rag-agent"

.EXAMPLE
    .\deploy-infrastructure.ps1 -ConfigFile "config-prod.json" -WhatIf

.NOTES
    Author: RAG Agent Team
    Version: 1.0
    Requires: Azure PowerShell module
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory = $false)]
    [string]$SubscriptionId,
    
    [Parameter(Mandatory = $false)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory = $false)]
    [string]$Location = "East US 2",
    
    [Parameter(Mandatory = $false)]
    [string]$Environment,
    
    [Parameter(Mandatory = $false)]
    [string]$ProjectName,
    
    [Parameter(Mandatory = $false)]
    [securestring]$OpenAIApiKey,
    
    [Parameter(Mandatory = $false)]
    [string]$ConfigFile,
    
    [Parameter(Mandatory = $false)]
    [switch]$WhatIf,
    
    [Parameter(Mandatory = $false)]
    [switch]$Force
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Import required modules
try {
    Import-Module Az.Accounts -Force
    Import-Module Az.Resources -Force
    Import-Module Az.Storage -Force
    Import-Module Az.KeyVault -Force
    Import-Module Az.CognitiveServices -Force
    Import-Module Az.Search -Force
    Import-Module Az.Functions -Force
    Import-Module Az.Monitor -Force
}
catch {
    Write-Error "Failed to import required Azure PowerShell modules. Please install Az PowerShell module."
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

# Function to load configuration from file
function Load-Configuration {
    param([string]$FilePath)
    
    if (-not (Test-Path $FilePath)) {
        Write-Error "Configuration file not found: $FilePath"
        return $null
    }
    
    try {
        $config = Get-Content $FilePath | ConvertFrom-Json
        Write-ColorOutput "Configuration loaded from: $FilePath" "Green"
        return $config
    }
    catch {
        Write-Error "Failed to parse configuration file: $FilePath"
        return $null
    }
}

# Function to validate parameters
function Test-Parameters {
    param($Config)
    
    $requiredParams = @('SubscriptionId', 'ResourceGroupName', 'Environment', 'ProjectName')
    $missingParams = @()
    
    foreach ($param in $requiredParams) {
        if (-not $Config.$param) {
            $missingParams += $param
        }
    }
    
    if ($missingParams.Count -gt 0) {
        Write-Error "Missing required parameters: $($missingParams -join ', ')"
        return $false
    }
    
    return $true
}

# Function to get secure input
function Get-SecureInput {
    param([string]$Prompt)
    
    $secureString = Read-Host -Prompt $Prompt -AsSecureString
    return $secureString
}

# Function to create resource group
function New-ResourceGroupIfNotExists {
    param(
        [string]$Name,
        [string]$Location
    )
    
    $rg = Get-AzResourceGroup -Name $Name -ErrorAction SilentlyContinue
    if (-not $rg) {
        Write-ColorOutput "Creating resource group: $Name" "Yellow"
        New-AzResourceGroup -Name $Name -Location $Location -Tag @{
            Environment = $script:config.Environment
            Project = $script:config.ProjectName
            CreatedBy = "PowerShell"
            CreatedDate = (Get-Date).ToString("yyyy-MM-dd")
        }
        Write-ColorOutput "Resource group created successfully" "Green"
    }
    else {
        Write-ColorOutput "Resource group already exists: $Name" "Cyan"
    }
}

# Function to deploy Bicep template
function Deploy-BicepTemplate {
    param(
        [string]$TemplateFile,
        [hashtable]$Parameters,
        [string]$ResourceGroupName,
        [string]$DeploymentName,
        [switch]$WhatIf
    )
    
    $deploymentParams = @{
        ResourceGroupName = $ResourceGroupName
        TemplateFile = $TemplateFile
        TemplateParameterObject = $Parameters
        Name = $DeploymentName
        Verbose = $true
    }
    
    if ($WhatIf) {
        Write-ColorOutput "Running deployment in What-If mode..." "Yellow"
        $result = Get-AzResourceGroupDeploymentWhatIfResult @deploymentParams
        Write-Output $result
        return $result
    }
    else {
        Write-ColorOutput "Starting deployment: $DeploymentName" "Yellow"
        $result = New-AzResourceGroupDeployment @deploymentParams
        if ($result.ProvisioningState -eq "Succeeded") {
            Write-ColorOutput "Deployment completed successfully: $DeploymentName" "Green"
        }
        else {
            Write-Error "Deployment failed: $DeploymentName"
        }
        return $result
    }
}

# Function to validate deployment
function Test-DeploymentOutputs {
    param($DeploymentResult)
    
    Write-ColorOutput "Validating deployment outputs..." "Yellow"
    
    $outputs = $DeploymentResult.Outputs
    $validationErrors = @()
    
    # Check required outputs
    $requiredOutputs = @('storageAccountName', 'functionAppName', 'searchServiceName', 'keyVaultName')
    foreach ($output in $requiredOutputs) {
        if (-not $outputs.ContainsKey($output)) {
            $validationErrors += "Missing required output: $output"
        }
    }
    
    # Test storage account
    if ($outputs.ContainsKey('storageAccountName')) {
        $storageAccount = Get-AzStorageAccount -ResourceGroupName $script:config.ResourceGroupName -Name $outputs.storageAccountName.Value -ErrorAction SilentlyContinue
        if (-not $storageAccount) {
            $validationErrors += "Storage account not found: $($outputs.storageAccountName.Value)"
        }
        else {
            Write-ColorOutput "Storage account validated: $($outputs.storageAccountName.Value)" "Green"
        }
    }
    
    # Test function app
    if ($outputs.ContainsKey('functionAppName')) {
        $functionApp = Get-AzWebApp -ResourceGroupName $script:config.ResourceGroupName -Name $outputs.functionAppName.Value -ErrorAction SilentlyContinue
        if (-not $functionApp) {
            $validationErrors += "Function app not found: $($outputs.functionAppName.Value)"
        }
        else {
            Write-ColorOutput "Function app validated: $($outputs.functionAppName.Value)" "Green"
        }
    }
    
    # Test search service
    if ($outputs.ContainsKey('searchServiceName')) {
        $searchService = Get-AzSearchService -ResourceGroupName $script:config.ResourceGroupName -Name $outputs.searchServiceName.Value -ErrorAction SilentlyContinue
        if (-not $searchService) {
            $validationErrors += "Search service not found: $($outputs.searchServiceName.Value)"
        }
        else {
            Write-ColorOutput "Search service validated: $($outputs.searchServiceName.Value)" "Green"
        }
    }
    
    # Test key vault
    if ($outputs.ContainsKey('keyVaultName')) {
        $keyVault = Get-AzKeyVault -ResourceGroupName $script:config.ResourceGroupName -VaultName $outputs.keyVaultName.Value -ErrorAction SilentlyContinue
        if (-not $keyVault) {
            $validationErrors += "Key vault not found: $($outputs.keyVaultName.Value)"
        }
        else {
            Write-ColorOutput "Key vault validated: $($outputs.keyVaultName.Value)" "Green"
        }
    }
    
    if ($validationErrors.Count -gt 0) {
        Write-ColorOutput "Validation errors found:" "Red"
        foreach ($error in $validationErrors) {
            Write-ColorOutput "  - $error" "Red"
        }
        return $false
    }
    else {
        Write-ColorOutput "All deployment outputs validated successfully!" "Green"
        return $true
    }
}

# Function to generate deployment report
function New-DeploymentReport {
    param(
        $DeploymentResult,
        [string]$OutputPath
    )
    
    $report = @{
        DeploymentName = $DeploymentResult.DeploymentName
        ResourceGroupName = $DeploymentResult.ResourceGroupName
        ProvisioningState = $DeploymentResult.ProvisioningState
        Timestamp = $DeploymentResult.Timestamp
        Duration = $DeploymentResult.Duration
        Outputs = $DeploymentResult.Outputs
        Resources = @()
    }
    
    # Get deployed resources
    $resources = Get-AzResource -ResourceGroupName $script:config.ResourceGroupName
    foreach ($resource in $resources) {
        $report.Resources += @{
            Name = $resource.Name
            Type = $resource.ResourceType
            Location = $resource.Location
            Tags = $resource.Tags
        }
    }
    
    # Save report
    $report | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputPath -Encoding UTF8
    Write-ColorOutput "Deployment report saved to: $OutputPath" "Green"
}

# Main execution
try {
    Write-ColorOutput "Starting RAG Agent Infrastructure Deployment" "Cyan"
    Write-ColorOutput "=============================================" "Cyan"
    
    # Load configuration
    if ($ConfigFile) {
        $config = Load-Configuration -FilePath $ConfigFile
        if (-not $config) {
            exit 1
        }
    }
    else {
        $config = @{
            SubscriptionId = $SubscriptionId
            ResourceGroupName = $ResourceGroupName
            Location = $Location
            Environment = $Environment
            ProjectName = $ProjectName
        }
    }
    
    # Validate parameters
    if (-not (Test-Parameters -Config $config)) {
        exit 1
    }
    
    # Get OpenAI API key if not provided
    if (-not $OpenAIApiKey) {
        if ($config.OpenAIApiKey) {
            $OpenAIApiKey = ConvertTo-SecureString -String $config.OpenAIApiKey -AsPlainText -Force
        }
        else {
            $OpenAIApiKey = Get-SecureInput -Prompt "Enter OpenAI API Key"
        }
    }
    
    # Connect to Azure
    Write-ColorOutput "Connecting to Azure..." "Yellow"
    $context = Get-AzContext
    if (-not $context -or $context.Subscription.Id -ne $config.SubscriptionId) {
        Connect-AzAccount -SubscriptionId $config.SubscriptionId
    }
    
    # Set subscription context
    Set-AzContext -SubscriptionId $config.SubscriptionId
    Write-ColorOutput "Using subscription: $($config.SubscriptionId)" "Green"
    
    # Create resource group
    New-ResourceGroupIfNotExists -Name $config.ResourceGroupName -Location $config.Location
    
    # Prepare deployment parameters
    $deploymentParameters = @{
        projectName = $config.ProjectName
        environment = $config.Environment
        location = $config.Location
        openAIApiKey = $OpenAIApiKey
        tags = @{
            Environment = $config.Environment
            Project = $config.ProjectName
            DeployedBy = "PowerShell"
            DeployedDate = (Get-Date).ToString("yyyy-MM-dd")
        }
    }
    
    # Add optional parameters if provided
    if ($config.StorageAccountSku) {
        $deploymentParameters.storageAccountSku = $config.StorageAccountSku
    }
    if ($config.FunctionAppSkuName) {
        $deploymentParameters.functionAppSkuName = $config.FunctionAppSkuName
    }
    if ($config.SearchServiceSku) {
        $deploymentParameters.searchServiceSku = $config.SearchServiceSku
    }
    
    # Get Bicep template path
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
    $templatePath = Join-Path -Path $scriptPath -ChildPath "..\bicep\main.bicep"
    
    if (-not (Test-Path $templatePath)) {
        Write-Error "Bicep template not found: $templatePath"
        exit 1
    }
    
    # Generate deployment name
    $deploymentName = "rag-agent-deployment-$(Get-Date -Format 'yyyyMMddHHmmss')"
    
    # Deploy infrastructure
    if (-not $Force -and -not $WhatIf) {
        $confirmation = Read-Host "Are you sure you want to deploy to $($config.Environment) environment? (y/N)"
        if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
            Write-ColorOutput "Deployment cancelled by user." "Yellow"
            exit 0
        }
    }
    
    $deploymentResult = Deploy-BicepTemplate -TemplateFile $templatePath -Parameters $deploymentParameters -ResourceGroupName $config.ResourceGroupName -DeploymentName $deploymentName -WhatIf:$WhatIf
    
    if (-not $WhatIf) {
        # Validate deployment
        if (Test-DeploymentOutputs -DeploymentResult $deploymentResult) {
            Write-ColorOutput "Deployment validation successful!" "Green"
            
            # Generate deployment report
            $reportPath = "deployment-report-$(Get-Date -Format 'yyyyMMddHHmmss').json"
            New-DeploymentReport -DeploymentResult $deploymentResult -OutputPath $reportPath
            
            # Display key outputs
            Write-ColorOutput "Key Deployment Outputs:" "Cyan"
            Write-ColorOutput "======================" "Cyan"
            foreach ($output in $deploymentResult.Outputs.GetEnumerator()) {
                if ($output.Key -notlike "*key*" -and $output.Key -notlike "*secret*") {
                    Write-ColorOutput "$($output.Key): $($output.Value.Value)" "White"
                }
            }
            
            Write-ColorOutput "Deployment completed successfully!" "Green"
        }
        else {
            Write-Error "Deployment validation failed. Please check the Azure portal for details."
            exit 1
        }
    }
}
catch {
    Write-Error "Deployment failed with error: $($_.Exception.Message)"
    Write-Error "Stack trace: $($_.Exception.StackTrace)"
    exit 1
}
finally {
    Write-ColorOutput "Deployment script completed." "Cyan"
}
