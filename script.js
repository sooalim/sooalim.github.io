// Azure DevOps RAG Agent Template Script
class RAGTemplateManager {
    constructor() {
        this.components = {
            devops: {
                title: 'Azure DevOps Setup',
                description: 'Complete Azure DevOps project configuration including work items, boards, and pipelines',
                files: [
                    'azure-devops/project-template.json',
                    'azure-devops/work-items/epic-template.json',
                    'azure-devops/work-items/feature-templates.json',
                    'azure-devops/work-items/user-story-templates.json',
                    'azure-devops/work-items/task-templates.json',
                    'azure-devops/pipelines/build-pipeline.yml',
                    'azure-devops/pipelines/release-pipeline.yml',
                    'azure-devops/pipelines/infrastructure-pipeline.yml'
                ]
            },
            data: {
                title: 'Data Processing Pipeline',
                description: 'Python scripts and Azure services for data extraction, ingestion, and chunking',
                files: [
                    'src/data-extraction/data_extractor.py',
                    'src/data-extraction/azure_cognitive_processor.py',
                    'src/data-ingestion/chunk_processor.py',
                    'src/data-ingestion/vector_store_manager.py',
                    'src/logic-apps/data-ingestion-workflow.json'
                ]
            },
            infrastructure: {
                title: 'Infrastructure as Code',
                description: 'Bicep templates and PowerShell scripts for Azure resource deployment',
                files: [
                    'infrastructure/bicep/main.bicep',
                    'infrastructure/bicep/storage.bicep',
                    'infrastructure/bicep/cognitive-services.bicep',
                    'infrastructure/bicep/functions.bicep',
                    'infrastructure/bicep/search.bicep',
                    'infrastructure/powershell/deploy-infrastructure.ps1',
                    'infrastructure/powershell/setup-environment.ps1'
                ]
            },
            copilot: {
                title: 'Copilot Studio Configuration',
                description: 'Agent configuration templates and topic definitions for Copilot Studio',
                files: [
                    'src/copilot-studio/agent-configuration.json',
                    'src/copilot-studio/topics-template.json'
                ]
            },
            functions: {
                title: 'Azure Functions',
                description: 'Serverless functions for continuous data refresh and processing',
                files: [
                    'src/azure-functions/data-refresh-function/function_app.py',
                    'src/azure-functions/data-refresh-function/requirements.txt',
                    'src/azure-functions/data-refresh-function/host.json',
                    'src/azure-functions/data-refresh-function/local.settings.json'
                ]
            },
            documentation: {
                title: 'Documentation Templates',
                description: 'Comprehensive documentation templates for all project phases',
                files: [
                    'documentation/project-charter-template.md',
                    'documentation/discovery-session-template.md',
                    'documentation/technical-design-template.md',
                    'documentation/knowledge-transfer-template.md',
                    'documentation/deployment-guide.md',
                    'documentation/testing-strategy.md',
                    'documentation/infrastructure-checklist.md',
                    'documentation/licensing-guide.md',
                    'documentation/mcp-integration-guide.md'
                ]
            }
        };

        this.checklists = {
            infrastructure: {
                title: 'Infrastructure Checklist',
                items: [
                    { name: 'Azure Subscription with appropriate permissions', status: 'pending' },
                    { name: 'Resource Groups created', status: 'pending' },
                    { name: 'Virtual Network and Subnets configured', status: 'pending' },
                    { name: 'Network Security Groups configured', status: 'pending' },
                    { name: 'Azure Active Directory setup', status: 'pending' },
                    { name: 'Key Vault for secrets management', status: 'pending' },
                    { name: 'Storage accounts provisioned', status: 'pending' },
                    { name: 'Cognitive Services enabled', status: 'pending' },
                    { name: 'Azure OpenAI service provisioned', status: 'pending' },
                    { name: 'Azure Cognitive Search configured', status: 'pending' }
                ]
            },
            licensing: {
                title: 'Licensing Requirements',
                items: [
                    { name: 'Microsoft 365 E3 or E5 licenses', status: 'pending' },
                    { name: 'Power Platform licenses (Power Automate, Power Apps)', status: 'pending' },
                    { name: 'Copilot Studio licenses ($200/tenant + $10/user)', status: 'pending' },
                    { name: 'Azure OpenAI service access and quotas', status: 'pending' },
                    { name: 'Azure Cognitive Services licenses', status: 'pending' },
                    { name: 'Azure DevOps licenses', status: 'pending' },
                    { name: 'Visual Studio subscriptions (if applicable)', status: 'pending' },
                    { name: 'Azure Functions consumption plan limits', status: 'pending' },
                    { name: 'Storage account and data transfer quotas', status: 'pending' },
                    { name: 'Cost budgets and spending alerts configured', status: 'pending' }
                ]
            },
            mcp: {
                title: 'MCP Integration Checklist',
                items: [
                    { name: 'Model Context Protocol dependencies installed', status: 'pending' },
                    { name: 'MCP server implementation completed', status: 'pending' },
                    { name: 'Tool definitions for document search', status: 'pending' },
                    { name: 'Tool definitions for content extraction', status: 'pending' },
                    { name: 'Resource definitions for knowledge base', status: 'pending' },
                    { name: 'Authentication and authorization configured', status: 'pending' },
                    { name: 'Rate limiting and throttling implemented', status: 'pending' },
                    { name: 'Caching strategy configured', status: 'pending' },
                    { name: 'Connection pooling for performance', status: 'pending' },
                    { name: 'Usage tracking and analytics', status: 'pending' },
                    { name: 'Integration with external AI tools', status: 'pending' },
                    { name: 'Claude Desktop integration configured', status: 'pending' }
                ]
            }
        };

        this.init();
    }

    init() {
        // Initialize event listeners
        this.setupEventListeners();
        
        // Load saved state if exists
        this.loadState();
        
        // Update UI
        this.updateUI();
    }

    setupEventListeners() {
        // Smooth scrolling for navigation links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth'
                    });
                }
            });
        });

        // Add keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'g') {
                e.preventDefault();
                this.generateProject();
            }
        });
    }

    showComponent(componentKey) {
        const component = this.components[componentKey];
        if (!component) return;

        const modal = document.getElementById('componentModal');
        const modalTitle = document.getElementById('componentModalTitle');
        const modalBody = document.getElementById('componentModalBody');

        modalTitle.textContent = component.title;
        modalBody.innerHTML = this.generateComponentContent(component);

        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    generateComponentContent(component) {
        let content = `
            <div class="mb-4">
                <h6>Description</h6>
                <p>${component.description}</p>
            </div>
            <div class="mb-4">
                <h6>Files Included</h6>
                <ul class="list-group">
        `;

        component.files.forEach(file => {
            content += `
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <i class="fas fa-file-code me-2"></i>${file}
                    </div>
                    <div>
                        <button class="btn btn-sm btn-outline-primary me-2" onclick="previewFile('${file}')">
                            <i class="fas fa-eye me-1"></i>Preview
                        </button>
                        <span class="badge bg-primary rounded-pill">Template</span>
                    </div>
                </li>
            `;
        });

        content += `
                </ul>
            </div>
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                These files are part of the comprehensive template and will be customized for your specific project requirements.
            </div>
        `;

        return content;
    }

    showChecklist(checklistKey) {
        const checklist = this.checklists[checklistKey];
        if (!checklist) return;

        const modal = document.getElementById('componentModal');
        const modalTitle = document.getElementById('componentModalTitle');
        const modalBody = document.getElementById('componentModalBody');

        modalTitle.textContent = checklist.title;
        modalBody.innerHTML = this.generateChecklistContent(checklist);

        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    generateChecklistContent(checklist) {
        let content = `
            <div class="mb-4">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h6>Checklist Items</h6>
                    <button class="btn btn-sm btn-outline-primary" onclick="ragTemplate.exportChecklist('${checklist.title}')">
                        <i class="fas fa-download me-1"></i>Export
                    </button>
                </div>
                <div class="checklist-container">
        `;

        checklist.items.forEach((item, index) => {
            const statusIcon = item.status === 'completed' ? 'fa-check-circle text-success' : 'fa-circle text-muted';
            content += `
                <div class="checklist-item">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="item-${index}" ${item.status === 'completed' ? 'checked' : ''}>
                        <label class="form-check-label" for="item-${index}">
                            <i class="fas ${statusIcon} me-2"></i>
                            ${item.name}
                        </label>
                    </div>
                </div>
            `;
        });

        content += `
                </div>
            </div>
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Ensure all items are completed before proceeding with the project implementation.
            </div>
        `;

        return content;
    }

    generateProject() {
        const projectName = prompt('Enter project name:');
        if (!projectName) return;

        this.showProgress('Generating project structure...');
        
        // Simulate project generation
        setTimeout(() => {
            this.showSuccess(`Project "${projectName}" generated successfully!`);
            this.downloadProjectTemplate(projectName);
        }, 2000);
    }

    validateEnvironment() {
        this.showProgress('Validating client environment...');
        
        // Simulate environment validation
        setTimeout(() => {
            const validationResults = {
                azure: true,
                licensing: true,
                network: false,
                security: true
            };
            
            this.showValidationResults(validationResults);
        }, 3000);
    }

    estimateCosts() {
        this.showProgress('Calculating cost estimates...');
        
        // Simulate cost calculation
        setTimeout(() => {
            const costs = {
                azure: 2500,
                licensing: 1200,
                development: 45000,
                total: 48700
            };
            
            this.showCostEstimate(costs);
        }, 2000);
    }

    showProgress(message) {
        const toast = this.createToast('info', message, 0);
        toast.show();
    }

    showSuccess(message) {
        const toast = this.createToast('success', message);
        toast.show();
    }

    showValidationResults(results) {
        const modal = document.getElementById('componentModal');
        const modalTitle = document.getElementById('componentModalTitle');
        const modalBody = document.getElementById('componentModalBody');

        modalTitle.textContent = 'Environment Validation Results';
        modalBody.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <div class="card ${results.azure ? 'border-success' : 'border-danger'}">
                        <div class="card-body">
                            <h6><i class="fas fa-cloud me-2"></i>Azure Services</h6>
                            <span class="badge ${results.azure ? 'bg-success' : 'bg-danger'}">
                                ${results.azure ? 'Ready' : 'Issues Found'}
                            </span>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card ${results.licensing ? 'border-success' : 'border-danger'}">
                        <div class="card-body">
                            <h6><i class="fas fa-key me-2"></i>Licensing</h6>
                            <span class="badge ${results.licensing ? 'bg-success' : 'bg-danger'}">
                                ${results.licensing ? 'Ready' : 'Issues Found'}
                            </span>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card ${results.network ? 'border-success' : 'border-danger'}">
                        <div class="card-body">
                            <h6><i class="fas fa-network-wired me-2"></i>Network</h6>
                            <span class="badge ${results.network ? 'bg-success' : 'bg-danger'}">
                                ${results.network ? 'Ready' : 'Issues Found'}
                            </span>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card ${results.security ? 'border-success' : 'border-danger'}">
                        <div class="card-body">
                            <h6><i class="fas fa-shield-alt me-2"></i>Security</h6>
                            <span class="badge ${results.security ? 'bg-success' : 'bg-danger'}">
                                ${results.security ? 'Ready' : 'Issues Found'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="mt-4">
                <h6>Recommendations</h6>
                <ul class="list-unstyled">
                    ${!results.network ? '<li><i class="fas fa-exclamation-triangle text-warning me-2"></i>Network configuration requires attention</li>' : ''}
                    <li><i class="fas fa-info-circle text-info me-2"></i>Review all components before proceeding</li>
                </ul>
            </div>
        `;

        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    showCostEstimate(costs) {
        const modal = document.getElementById('componentModal');
        const modalTitle = document.getElementById('componentModalTitle');
        const modalBody = document.getElementById('componentModalBody');

        modalTitle.textContent = 'Cost Estimation (6-8 weeks)';
        modalBody.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h6><i class="fas fa-cloud me-2"></i>Azure Services</h6>
                            <h4 class="text-primary">$${costs.azure.toLocaleString()}</h4>
                            <small class="text-muted">Monthly estimate</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h6><i class="fas fa-key me-2"></i>Licensing</h6>
                            <h4 class="text-primary">$${costs.licensing.toLocaleString()}</h4>
                            <small class="text-muted">Monthly estimate</small>
                        </div>
                    </div>
                </div>
            </div>
            <div class="mt-4">
                <div class="card">
                    <div class="card-body">
                        <h6><i class="fas fa-users me-2"></i>Development Services</h6>
                        <h4 class="text-primary">$${costs.development.toLocaleString()}</h4>
                        <small class="text-muted">One-time project cost</small>
                    </div>
                </div>
            </div>
            <div class="mt-4">
                <div class="card border-primary">
                    <div class="card-body">
                        <h6><i class="fas fa-calculator me-2"></i>Total Project Cost</h6>
                        <h3 class="text-primary">$${costs.total.toLocaleString()}</h3>
                        <small class="text-muted">Including 6-8 weeks of development</small>
                    </div>
                </div>
            </div>
            <div class="mt-4 alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                Costs may vary based on specific requirements, data volume, and chosen Azure service tiers.
            </div>
        `;

        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    downloadProjectTemplate(projectName) {
        const template = {
            name: projectName,
            version: '1.0.0',
            description: 'Azure DevOps RAG Agent Project Template',
            created: new Date().toISOString(),
            components: Object.keys(this.components),
            timeline: '6-8 weeks',
            phases: [
                'Discovery & Planning',
                'Data Processing',
                'Agent Development',
                'Deployment & Transfer'
            ]
        };

        const blob = new Blob([JSON.stringify(template, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${projectName.replace(/\s+/g, '-').toLowerCase()}-template.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    createToast(type, message, delay = 3000) {
        const toastContainer = document.getElementById('toastContainer') || this.createToastContainer();
        const toastId = 'toast-' + Date.now();
        
        const toastHtml = `
            <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-body">
                    <i class="fas fa-${this.getToastIcon(type)} me-2"></i>
                    ${message}
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: delay });
        
        if (delay > 0) {
            setTimeout(() => {
                toastElement.remove();
            }, delay + 500);
        }
        
        return toast;
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
        return container;
    }

    getToastIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    loadState() {
        try {
            const savedState = localStorage.getItem('ragTemplateState');
            if (savedState) {
                const state = JSON.parse(savedState);
                // Apply saved state if needed
            }
        } catch (error) {
            console.warn('Failed to load saved state:', error);
        }
    }

    saveState() {
        try {
            const state = {
                checklists: this.checklists,
                lastAccessed: new Date().toISOString()
            };
            localStorage.setItem('ragTemplateState', JSON.stringify(state));
        } catch (error) {
            console.warn('Failed to save state:', error);
        }
    }

    updateUI() {
        // Update any dynamic UI elements
        const now = new Date();
        const timeElements = document.querySelectorAll('[data-time]');
        timeElements.forEach(element => {
            element.textContent = now.toLocaleString();
        });
    }

    exportChecklist(checklistTitle) {
        const checklist = Object.values(this.checklists).find(c => c.title === checklistTitle);
        if (!checklist) return;

        let content = `# ${checklist.title}\n\n`;
        content += `Generated on: ${new Date().toLocaleDateString()}\n\n`;
        
        checklist.items.forEach((item, index) => {
            const status = item.status === 'completed' ? '[x]' : '[ ]';
            content += `${index + 1}. ${status} ${item.name}\n`;
        });

        const blob = new Blob([content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${checklistTitle.replace(/\s+/g, '-').toLowerCase()}.md`;
        a.click();
        URL.revokeObjectURL(url);
    }
}

// Global functions for onclick handlers
let ragTemplate;

function showComponent(componentKey) {
    ragTemplate.showComponent(componentKey);
}

function showChecklist(checklistKey) {
    ragTemplate.showChecklist(checklistKey);
}

function generateProject() {
    ragTemplate.generateProject();
}

function validateEnvironment() {
    ragTemplate.validateEnvironment();
}

function estimateCosts() {
    ragTemplate.estimateCosts();
}

async function downloadAllFiles() {
    try {
        // Show progress
        ragTemplate.showProgress('Preparing template files for download...');
        
        // Import JSZip library dynamically
        if (!window.JSZip) {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js';
            document.head.appendChild(script);
            
            await new Promise((resolve, reject) => {
                script.onload = resolve;
                script.onerror = reject;
            });
        }
        
        const zip = new JSZip();
        
        // Define all template files to include
        const templateFiles = {
            // Azure DevOps files
            'azure-devops/project-template.json': generateProjectTemplate(),
            'azure-devops/work-items/epic-template.json': generateEpicTemplate(),
            'azure-devops/work-items/feature-templates.json': generateFeatureTemplates(),
            'azure-devops/work-items/user-story-templates.json': generateUserStoryTemplates(),
            'azure-devops/work-items/task-templates.json': generateTaskTemplates(),
            'azure-devops/pipelines/build-pipeline.yml': generateBuildPipeline(),
            'azure-devops/pipelines/release-pipeline.yml': generateReleasePipeline(),
            'azure-devops/pipelines/infrastructure-pipeline.yml': generateInfrastructurePipeline(),
            
            // Infrastructure files
            'infrastructure/bicep/main.bicep': generateMainBicep(),
            'infrastructure/bicep/storage.bicep': generateStorageBicep(),
            'infrastructure/bicep/cognitive-services.bicep': generateCognitiveServicesBicep(),
            'infrastructure/bicep/functions.bicep': generateFunctionsBicep(),
            'infrastructure/bicep/search.bicep': generateSearchBicep(),
            'infrastructure/powershell/deploy-infrastructure.ps1': generateDeployScript(),
            'infrastructure/powershell/setup-environment.ps1': generateSetupScript(),
            
            // Documentation files
            'documentation/project-charter-template.md': generateProjectCharter(),
            'documentation/discovery-session-template.md': generateDiscoveryTemplate(),
            'documentation/technical-design-template.md': generateTechnicalDesign(),
            'documentation/knowledge-transfer-template.md': generateKnowledgeTransfer(),
            'documentation/deployment-guide.md': generateDeploymentGuide(),
            'documentation/testing-strategy.md': generateTestingStrategy(),
            'documentation/infrastructure-checklist.md': generateInfrastructureChecklist(),
            'documentation/licensing-guide.md': generateLicensingGuide(),
            'documentation/mcp-integration-guide.md': generateMCPGuide(),
            
            // Source code files
            'src/data-extraction/data_extractor.py': generateDataExtractor(),
            'src/data-extraction/azure_cognitive_processor.py': generateCognitiveProcessor(),
            'src/data-extraction/requirements.txt': generateDataExtractionRequirements(),
            'src/data-ingestion/chunk_processor.py': generateChunkProcessor(),
            'src/data-ingestion/vector_store_manager.py': generateVectorStoreManager(),
            'src/azure-functions/data-refresh-function/function_app.py': generateFunctionApp(),
            'src/azure-functions/data-refresh-function/requirements.txt': generateFunctionRequirements(),
            'src/azure-functions/data-refresh-function/host.json': generateHostJson(),
            'src/azure-functions/data-refresh-function/local.settings.json': generateLocalSettings(),
            
            // Project files
            'README.md': generateReadme(),
            '.gitignore': generateGitignore(),
            'replit.md': generateReplitMd()
        };
        
        // Add all files to zip
        for (const [filePath, content] of Object.entries(templateFiles)) {
            zip.file(filePath, content);
        }
        
        ragTemplate.showProgress('Generating ZIP archive...');
        
        // Generate ZIP file
        const content = await zip.generateAsync({
            type: 'blob',
            compression: 'DEFLATE',
            compressionOptions: {
                level: 6
            }
        });
        
        // Create download link
        const url = window.URL.createObjectURL(content);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'rag-agent-template.zip';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        ragTemplate.showSuccess('Template files downloaded successfully!');
        
    } catch (error) {
        console.error('Error downloading files:', error);
        ragTemplate.createToast('error', 'Error downloading template files. Please try again.');
    }
}

// File generation functions
function generateProjectTemplate() {
    return JSON.stringify({
        "name": "RAG Agent Implementation",
        "description": "Comprehensive RAG agent project using Azure services and Copilot Studio",
        "version": "1.0.0",
        "process": "Microsoft Scrum",
        "visibility": "Private",
        "capabilities": {
            "versioncontrol": {
                "sourceControlType": "Git"
            },
            "workitemtracking": {
                "enabled": true
            },
            "processConfiguration": {
                "bugWorkItemTypeName": "Bug",
                "epicCategoryTypeName": "Epic Category",
                "featureCategoryTypeName": "Feature Category",
                "portfolioBacklogWorkItemTypeName": "Epic",
                "requirementCategoryTypeName": "Requirement Category",
                "requirementWorkItemTypeName": "Product Backlog Item",
                "taskCategoryTypeName": "Task Category",
                "taskWorkItemTypeName": "Task",
                "testCaseCategoryTypeName": "Test Case Category",
                "testCaseWorkItemTypeName": "Test Case"
            }
        }
    }, null, 2);
}

function generateReadme() {
    return `# Azure DevOps RAG Agent Template

A comprehensive project template for building Retrieval-Augmented Generation (RAG) agents using Azure services and Microsoft Copilot Studio.

## Overview

This template provides everything needed for a 6-8 week RAG agent implementation including:
- Complete Azure DevOps project structure
- Infrastructure as Code with Bicep templates
- Python data processing pipeline
- Azure Functions for automation
- Comprehensive documentation
- Infrastructure checklist
- Licensing guide
- MCP integration for future expansion

## Getting Started

1. Review the infrastructure checklist in \`documentation/infrastructure-checklist.md\`
2. Set up Azure subscription and licensing per \`documentation/licensing-guide.md\`
3. Deploy infrastructure using Bicep templates in \`infrastructure/\`
4. Configure Azure DevOps project using templates in \`azure-devops/\`
5. Deploy Azure Functions from \`src/azure-functions/\`
6. Follow deployment guide in \`documentation/deployment-guide.md\`

## Timeline

- **Week 1-2**: Discovery and infrastructure setup
- **Week 3-4**: Data processing implementation
- **Week 5-6**: Agent development and integration
- **Week 7-8**: Testing, deployment, and knowledge transfer

## Support

Refer to the comprehensive documentation in the \`documentation/\` folder for detailed guides and templates.
`;
}

function generateGitignore() {
    return `# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Azure Functions
local.settings.json
.vscode/
.azure/

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Azure
.azure/

# Node modules
node_modules/

# VS Code
.vscode/

# Jupyter Notebook
.ipynb_checkpoints

# pyenv
.python-version

# pipenv
Pipfile.lock

# PEP 582
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json
`;
}

function generateReplitMd() {
    return `# RAG Agent Implementation Project

## Overview

This project is a comprehensive template for building Retrieval-Augmented Generation (RAG) agents using Azure services and Microsoft Copilot Studio. The solution provides a complete end-to-end implementation including data extraction, processing, vector storage, and intelligent query handling with a 6-8 week deployment timeline.

## User Preferences

\`\`\`
Preferred communication style: Simple, everyday language.
\`\`\`
`;
}

// Simplified generators for other files (returning placeholder content)
function generateEpicTemplate() {
    return JSON.stringify({
        "name": "RAG Agent Epic Template",
        "description": "Template for RAG agent implementation epics",
        "workItemType": "Epic"
    }, null, 2);
}

function generateFeatureTemplates() {
    return JSON.stringify({
        "name": "RAG Agent Features",
        "features": [
            "Data Processing Pipeline",
            "Vector Storage Implementation", 
            "Agent Configuration",
            "Integration Testing"
        ]
    }, null, 2);
}

function generateUserStoryTemplates() {
    return JSON.stringify({
        "name": "User Story Templates",
        "stories": [
            "As a user, I want to search documents",
            "As an admin, I want to manage data sources"
        ]
    }, null, 2);
}

function generateTaskTemplates() {
    return JSON.stringify({
        "name": "Task Templates", 
        "tasks": [
            "Setup Azure infrastructure",
            "Configure Copilot Studio",
            "Deploy functions"
        ]
    }, null, 2);
}

function generateBuildPipeline() {
    return `# Build Pipeline for RAG Agent
trigger:
  branches:
    include:
    - main
    - develop

pool:
  vmImage: 'ubuntu-latest'

variables:
  pythonVersion: '3.8'

stages:
- stage: Build
  jobs:
  - job: BuildJob
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(pythonVersion)'
    - script: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
      displayName: 'Install dependencies'
    - script: |
        python -m pytest tests/
      displayName: 'Run tests'
`;
}

function generateReleasePipeline() {
    return `# Release Pipeline for RAG Agent
trigger: none

resources:
  pipelines:
  - pipeline: buildPipeline
    source: RAG-Agent-Build

stages:
- stage: Deploy_UAT
  jobs:
  - deployment: DeployUAT
    environment: 'UAT'
    strategy:
      runOnce:
        deploy:
          steps:
          - task: AzureFunctionApp@1
            inputs:
              azureSubscription: 'Azure-Connection'
              appType: 'functionApp'
              appName: 'rag-agent-uat'
`;
}

function generateInfrastructurePipeline() {
    return `# Infrastructure Pipeline
trigger:
  paths:
    include:
    - infrastructure/*

pool:
  vmImage: 'ubuntu-latest'

stages:
- stage: DeployInfrastructure
  jobs:
  - job: Deploy
    steps:
    - task: AzureCLI@2
      inputs:
        azureSubscription: 'Azure-Connection'
        scriptType: 'bash'
        scriptLocation: 'inlineScript'
        inlineScript: |
          az deployment group create \\
            --resource-group rg-rag-agent \\
            --template-file infrastructure/bicep/main.bicep
`;
}

// Simplified generators for other file types
function generateMainBicep() {
    return `// Main Bicep template for RAG Agent infrastructure
targetScope = 'resourceGroup'

param location string = resourceGroup().location
param environmentName string = 'dev'

// Deploy storage account
module storage 'storage.bicep' = {
  name: 'storage'
  params: {
    location: location
    environmentName: environmentName
  }
}

// Deploy cognitive services  
module cognitiveServices 'cognitive-services.bicep' = {
  name: 'cognitiveServices'
  params: {
    location: location
    environmentName: environmentName
  }
}

// Deploy search service
module search 'search.bicep' = {
  name: 'search'
  params: {
    location: location
    environmentName: environmentName
  }
}

// Deploy functions
module functions 'functions.bicep' = {
  name: 'functions'
  params: {
    location: location
    environmentName: environmentName
    storageAccountName: storage.outputs.storageAccountName
  }
}
`;
}

function generateStorageBicep() {
    return `// Storage account for RAG Agent
param location string
param environmentName string

resource storageAccount 'Microsoft.Storage/storageAccounts@2021-09-01' = {
  name: 'stragagent\${environmentName}\${uniqueString(resourceGroup().id)}'
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
  }
}

output storageAccountName string = storageAccount.name
output storageAccountKey string = listKeys(storageAccount.id, storageAccount.apiVersion).keys[0].value
`;
}

function generateCognitiveServicesBicep() {
    return `// Cognitive Services for RAG Agent
param location string
param environmentName string

resource cognitiveServices 'Microsoft.CognitiveServices/accounts@2021-10-01' = {
  name: 'cog-rag-agent-\${environmentName}'
  location: location
  sku: {
    name: 'S0'
  }
  kind: 'CognitiveServices'
  properties: {
    apiProperties: {}
    customSubDomainName: 'rag-agent-\${environmentName}'
  }
}

output cognitiveServicesEndpoint string = cognitiveServices.properties.endpoint
output cognitiveServicesKey string = listKeys(cognitiveServices.id, cognitiveServices.apiVersion).key1
`;
}

function generateFunctionsBicep() {
    return `// Azure Functions for RAG Agent
param location string
param environmentName string
param storageAccountName string

resource functionApp 'Microsoft.Web/sites@2021-03-01' = {
  name: 'func-rag-agent-\${environmentName}'
  location: location
  kind: 'functionapp'
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=\${storageAccountName};EndpointSuffix=core.windows.net'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
      ]
    }
  }
}

resource appServicePlan 'Microsoft.Web/serverfarms@2021-03-01' = {
  name: 'plan-rag-agent-\${environmentName}'
  location: location
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
}
`;
}

function generateSearchBicep() {
    return `// Azure Cognitive Search for RAG Agent
param location string
param environmentName string

resource searchService 'Microsoft.Search/searchServices@2021-04-01-preview' = {
  name: 'srch-rag-agent-\${environmentName}'
  location: location
  sku: {
    name: 'standard'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    semanticSearch: 'free'
  }
}

output searchServiceName string = searchService.name
output searchServiceKey string = listAdminKeys(searchService.id, searchService.apiVersion).primaryKey
`;
}

// Additional file generators with simplified content
function generateDeployScript() {
    return `# PowerShell script to deploy RAG Agent infrastructure
param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$true)]
    [string]$Location,
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev"
)

Write-Host "Deploying RAG Agent infrastructure..."

# Deploy main Bicep template
az deployment group create \
    --resource-group $ResourceGroupName \
    --template-file ./bicep/main.bicep \
    --parameters environmentName=$Environment location=$Location

Write-Host "Deployment completed!"
`;
}

function generateSetupScript() {
    return `# PowerShell script to setup RAG Agent environment
param(
    [Parameter(Mandatory=$true)]
    [string]$SubscriptionId,
    
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName
)

Write-Host "Setting up RAG Agent environment..."

# Set Azure subscription
az account set --subscription $SubscriptionId

# Create resource group
az group create --name $ResourceGroupName --location "East US"

Write-Host "Environment setup completed!"
`;
}

// Documentation generators with simplified content
function generateProjectCharter() {
    return `# RAG Agent Project Charter

## Project Overview
Implementation of a Retrieval-Augmented Generation agent using Azure services and Microsoft Copilot Studio.

## Objectives
- Deploy scalable RAG infrastructure
- Implement document processing pipeline  
- Configure Copilot Studio integration
- Provide comprehensive documentation

## Timeline
6-8 weeks from discovery to production deployment

## Success Criteria
- Functional RAG agent deployed
- User training completed
- Documentation delivered
- Performance targets met
`;
}

function generateDiscoveryTemplate() {
    return `# Discovery Session Template

## Business Requirements
- [ ] Define use cases
- [ ] Identify stakeholders
- [ ] Document success criteria
- [ ] Review compliance requirements

## Technical Requirements
- [ ] Assess current infrastructure
- [ ] Define data sources
- [ ] Plan integration points
- [ ] Review security requirements

## Resource Planning
- [ ] Team structure
- [ ] Timeline confirmation
- [ ] Budget approval
- [ ] Training needs
`;
}

function generateTechnicalDesign() {
    return `# Technical Design Document

## Architecture Overview
High-level system architecture and component relationships.

## Data Flow
Document ingestion, processing, and retrieval workflows.

## Integration Points
APIs, services, and external system connections.

## Security Design
Authentication, authorization, and data protection.

## Performance Requirements
Scalability, latency, and throughput specifications.
`;
}

function generateKnowledgeTransfer() {
    return `# Knowledge Transfer Template

## System Overview
- Architecture components
- Data flows
- Key integrations

## Operational Procedures
- Deployment process
- Monitoring setup
- Troubleshooting guides

## Maintenance Tasks
- Regular updates
- Performance optimization
- Security reviews

## Support Contacts
- Technical leads
- Vendor contacts
- Escalation procedures
`;
}

function generateDeploymentGuide() {
    return `# Deployment Guide

## Prerequisites
- Azure subscription setup
- Licensing requirements met
- Development environment ready

## Infrastructure Deployment
1. Deploy Bicep templates
2. Configure services
3. Verify connectivity

## Application Deployment
1. Deploy Azure Functions
2. Configure Copilot Studio
3. Test integrations

## Post-Deployment
1. Monitor performance
2. Validate functionality
3. Train users
`;
}

function generateTestingStrategy() {
    return `# Testing Strategy

## Unit Testing
- Component-level tests
- Data processing validation
- API endpoint testing

## Integration Testing
- End-to-end workflows
- Service connectivity
- Performance validation

## User Acceptance Testing
- Business scenario validation
- User interface testing
- Documentation review

## Performance Testing
- Load testing
- Stress testing
- Scalability validation
`;
}

function generateInfrastructureChecklist() {
    return `# Infrastructure Checklist

## Azure Services Setup
- [ ] Subscription configured
- [ ] Resource groups created
- [ ] Storage accounts deployed
- [ ] Cognitive services enabled
- [ ] Search service configured
- [ ] Functions deployed

## Security Configuration
- [ ] Key Vault setup
- [ ] Access policies configured
- [ ] Network security rules
- [ ] SSL certificates

## Monitoring Setup
- [ ] Application Insights
- [ ] Log Analytics
- [ ] Alert rules
- [ ] Dashboards

## Backup and Recovery
- [ ] Backup policies
- [ ] Recovery procedures
- [ ] Disaster recovery plan
`;
}

function generateLicensingGuide() {
    return `# Licensing Requirements

## Microsoft 365
- E3 or E5 licenses for users
- Power Platform access

## Azure Services  
- Subscription with appropriate limits
- OpenAI service access
- Cognitive Services quotas

## Copilot Studio
- $200/tenant + $10/user monthly
- Message limits and overages

## Cost Estimates
- Small org: $2,000-5,000/month
- Medium org: $5,000-15,000/month  
- Large org: $15,000-50,000/month
`;
}

function generateMCPGuide() {
    return `# Model Context Protocol (MCP) Integration

## Overview
MCP enables AI applications to securely access and interact with external data sources and tools.

## Implementation
- MCP server setup
- Tool definitions
- Resource configuration
- Authentication setup

## Integration Examples
- Claude Desktop connection
- Custom AI applications
- Third-party tool access

## Security Considerations
- Authentication and authorization
- Rate limiting
- Data protection
- Audit logging
`;
}

function generateDataExtractor() {
    return `"""
Data Extraction Module for RAG Agent
Handles extraction of text content from various document formats.
"""

import asyncio
import logging
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ExtractedDocument:
    content: str
    metadata: Dict[str, Any]
    
class DataExtractionManager:
    def __init__(self):
        self.extractors = {}
        
    async def extract_from_file(self, file_path: str) -> ExtractedDocument:
        # Implementation for file extraction
        pass
        
    async def extract_from_url(self, url: str) -> ExtractedDocument:
        # Implementation for URL extraction  
        pass
`;
}

function generateCognitiveProcessor() {
    return `"""
Azure Cognitive Services Processor for RAG Agent
Integrates with Azure Cognitive Services for advanced document analysis.
"""

import asyncio
from typing import Dict, Any, List

class CognitiveServicesProcessor:
    def __init__(self, endpoint: str, api_key: str):
        self.endpoint = endpoint
        self.api_key = api_key
        
    async def process_document(self, document_path: str) -> Dict[str, Any]:
        # Implementation for cognitive processing
        pass
        
    async def analyze_text(self, text: str) -> Dict[str, Any]:
        # Implementation for text analysis
        pass
`;
}

function generateDataExtractionRequirements() {
    return `# Data extraction requirements
PyPDF2>=3.0.1
python-docx>=1.0.0
openpyxl>=3.1.0
python-pptx>=0.6.23
beautifulsoup4>=4.12.0
lxml>=4.9.3
html2text>=2020.1.16
azure-ai-formrecognizer>=3.3.0
azure-ai-textanalytics>=5.3.0
requests>=2.31.0
chardet>=5.2.0
python-magic>=0.4.27
`;
}

function generateChunkProcessor() {
    return `"""
Chunk Processor for RAG Agent
Handles intelligent chunking of documents for optimal vector embedding.
"""

from enum import Enum
from typing import List, Dict, Any
from dataclasses import dataclass

class ChunkStrategy(Enum):
    FIXED_SIZE = "fixed_size"
    SENTENCE_BASED = "sentence_based" 
    SEMANTIC_BASED = "semantic_based"

@dataclass
class DocumentChunk:
    content: str
    metadata: Dict[str, Any]

class ChunkProcessor:
    def __init__(self):
        self.strategies = {}
        
    async def process_document(self, text: str, strategy: ChunkStrategy) -> List[DocumentChunk]:
        # Implementation for document chunking
        pass
`;
}

function generateVectorStoreManager() {
    return `"""
Vector Store Manager for RAG Agent
Manages vector embeddings storage and retrieval using Azure Cognitive Search.
"""

from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class VectorDocument:
    id: str
    content: str
    content_vector: List[float]
    metadata: Dict[str, Any]

class AzureSearchVectorStore:
    def __init__(self, endpoint: str, api_key: str):
        self.endpoint = endpoint
        self.api_key = api_key
        
    async def add_documents(self, documents: List[VectorDocument]) -> None:
        # Implementation for adding documents
        pass
        
    async def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        # Implementation for searching documents
        pass
`;
}

function generateFunctionApp() {
    return `"""
Azure Functions App for RAG Agent Data Refresh
Handles automated data refresh operations.
"""

import azure.functions as func
import logging

app = func.FunctionApp()

@app.timer_trigger(schedule="0 0 2 * * *", arg_name="timer")
async def scheduled_data_refresh(timer: func.TimerRequest) -> None:
    logging.info("Starting scheduled data refresh")
    # Implementation for data refresh
    
@app.route(route="refresh-data", auth_level=func.AuthLevel.FUNCTION)
async def manual_data_refresh(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Manual data refresh triggered")
    # Implementation for manual refresh
    return func.HttpResponse("Data refresh completed")

@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse("Healthy")
`;
}

function generateFunctionRequirements() {
    return `# Azure Functions requirements
azure-functions>=1.18.0
azure-functions-worker>=1.8.0
azure-identity>=1.15.0
azure-keyvault-secrets>=4.7.0
azure-storage-blob>=12.19.0
azure-search-documents>=11.4.0
openai>=1.6.0
pandas>=2.1.0
numpy>=1.24.0
requests>=2.31.0
`;
}

function generateHostJson() {
    return JSON.stringify({
        "version": "2.0",
        "logging": {
            "applicationInsights": {
                "samplingSettings": {
                    "isEnabled": true,
                    "excludedTypes": "Request"
                }
            }
        },
        "functionTimeout": "00:30:00",
        "extensions": {
            "http": {
                "routePrefix": "api"
            }
        }
    }, null, 2);
}

function generateLocalSettings() {
    return JSON.stringify({
        "IsEncrypted": false,
        "Values": {
            "AzureWebJobsStorage": "DefaultEndpointsProtocol=https;AccountName=<storage_account>;AccountKey=<key>;EndpointSuffix=core.windows.net",
            "FUNCTIONS_WORKER_RUNTIME": "python",
            "FUNCTIONS_EXTENSION_VERSION": "~4",
            "KEY_VAULT_NAME": "<key_vault_name>",
            "STORAGE_ACCOUNT_NAME": "<storage_account>",
            "SEARCH_SERVICE_NAME": "<search_service>",
            "OPENAI_ENDPOINT": "<openai_endpoint>"
        }
    }, null, 2);
}

// File preview functionality
function previewFile(fileName) {
    const modal = document.getElementById('filePreviewModal');
    const modalTitle = document.getElementById('filePreviewModalTitle');
    const modalBody = document.getElementById('filePreviewModalBody');
    
    // Update modal title
    modalTitle.innerHTML = `<i class="fas fa-file-code me-2"></i>Preview: ${fileName}`;
    
    // Get file content based on file name
    let fileContent = '';
    let language = 'text';
    
    // Map file names to their generator functions
    const fileGenerators = {
        // Documentation files
        'documentation/project-charter-template.md': () => ({ content: generateProjectCharter(), language: 'markdown' }),
        'documentation/discovery-session-template.md': () => ({ content: generateDiscoveryTemplate(), language: 'markdown' }),
        'documentation/technical-design-template.md': () => ({ content: generateTechnicalDesign(), language: 'markdown' }),
        'documentation/knowledge-transfer-template.md': () => ({ content: generateKnowledgeTransfer(), language: 'markdown' }),
        'documentation/deployment-guide.md': () => ({ content: generateDeploymentGuide(), language: 'markdown' }),
        'documentation/testing-strategy.md': () => ({ content: generateTestingStrategy(), language: 'markdown' }),
        'documentation/infrastructure-checklist.md': () => ({ content: generateInfrastructureChecklist(), language: 'markdown' }),
        'documentation/licensing-guide.md': () => ({ content: generateLicensingGuide(), language: 'markdown' }),
        'documentation/mcp-integration-guide.md': () => ({ content: generateMCPGuide(), language: 'markdown' }),
        
        // Azure DevOps files
        'azure-devops/project-template.json': () => ({ content: generateProjectTemplate(), language: 'json' }),
        'azure-devops/work-items/epic-template.json': () => ({ content: generateEpicTemplate(), language: 'json' }),
        'azure-devops/work-items/feature-templates.json': () => ({ content: generateFeatureTemplates(), language: 'json' }),
        'azure-devops/work-items/user-story-templates.json': () => ({ content: generateUserStoryTemplates(), language: 'json' }),
        'azure-devops/work-items/task-templates.json': () => ({ content: generateTaskTemplates(), language: 'json' }),
        'azure-devops/pipelines/build-pipeline.yml': () => ({ content: generateBuildPipeline(), language: 'yaml' }),
        'azure-devops/pipelines/release-pipeline.yml': () => ({ content: generateReleasePipeline(), language: 'yaml' }),
        'azure-devops/pipelines/infrastructure-pipeline.yml': () => ({ content: generateInfrastructurePipeline(), language: 'yaml' }),
        
        // Infrastructure files
        'infrastructure/bicep/main.bicep': () => ({ content: generateMainBicep(), language: 'bicep' }),
        'infrastructure/bicep/storage.bicep': () => ({ content: generateStorageBicep(), language: 'bicep' }),
        'infrastructure/bicep/cognitive-services.bicep': () => ({ content: generateCognitiveServicesBicep(), language: 'bicep' }),
        'infrastructure/bicep/functions.bicep': () => ({ content: generateFunctionsBicep(), language: 'bicep' }),
        'infrastructure/bicep/search.bicep': () => ({ content: generateSearchBicep(), language: 'bicep' }),
        'infrastructure/powershell/deploy-infrastructure.ps1': () => ({ content: generateDeployScript(), language: 'powershell' }),
        'infrastructure/powershell/setup-environment.ps1': () => ({ content: generateSetupScript(), language: 'powershell' }),
        
        // Source code files
        'src/data-extraction/data_extractor.py': () => ({ content: generateDataExtractor(), language: 'python' }),
        'src/data-extraction/azure_cognitive_processor.py': () => ({ content: generateCognitiveProcessor(), language: 'python' }),
        'src/data-extraction/requirements.txt': () => ({ content: generateDataExtractionRequirements(), language: 'text' }),
        'src/data-ingestion/chunk_processor.py': () => ({ content: generateChunkProcessor(), language: 'python' }),
        'src/data-ingestion/vector_store_manager.py': () => ({ content: generateVectorStoreManager(), language: 'python' }),
        'src/azure-functions/data-refresh-function/function_app.py': () => ({ content: generateFunctionApp(), language: 'python' }),
        'src/azure-functions/data-refresh-function/requirements.txt': () => ({ content: generateFunctionRequirements(), language: 'text' }),
        'src/azure-functions/data-refresh-function/host.json': () => ({ content: generateHostJson(), language: 'json' }),
        'src/azure-functions/data-refresh-function/local.settings.json': () => ({ content: generateLocalSettings(), language: 'json' }),
        
        // Project files
        'README.md': () => ({ content: generateReadme(), language: 'markdown' }),
        '.gitignore': () => ({ content: generateGitignore(), language: 'text' }),
        'replit.md': () => ({ content: generateReplitMd(), language: 'markdown' })
    };
    
    // Get file content
    const generator = fileGenerators[fileName];
    if (generator) {
        const result = generator();
        fileContent = result.content;
        language = result.language;
    } else {
        fileContent = `// File content for ${fileName} not found`;
        language = 'text';
    }
    
    // Create preview content with syntax highlighting
    const previewContent = `
        <div class="file-preview">
            <div class="file-info mb-3">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <span class="badge bg-secondary">${language.toUpperCase()}</span>
                        <span class="text-muted ms-2">${fileContent.length} characters</span>
                    </div>
                    <div>
                        <small class="text-muted">Click "Copy Content" to copy to clipboard</small>
                    </div>
                </div>
            </div>
            <div class="code-container">
                <pre><code class="language-${language}">${escapeHtml(fileContent)}</code></pre>
            </div>
        </div>
    `;
    
    modalBody.innerHTML = previewContent;
    
    // Apply syntax highlighting
    if (window.hljs) {
        modalBody.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }
    
    // Store current file content for copying
    window.currentFileContent = fileContent;
    
    // Show modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

// Copy file content to clipboard
function copyFileContent() {
    if (window.currentFileContent) {
        navigator.clipboard.writeText(window.currentFileContent).then(() => {
            ragTemplate.createToast('success', 'File content copied to clipboard!');
        }).catch(err => {
            console.error('Failed to copy content: ', err);
            ragTemplate.createToast('error', 'Failed to copy content to clipboard');
        });
    }
}

// Escape HTML for safe display
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    ragTemplate = new RAGTemplateManager();
});
