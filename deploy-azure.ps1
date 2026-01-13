# ============================================================
# Azure Deployment Script for AI Agent RAG Backend
# ============================================================
# This script automates the Azure deployment process
# Prerequisites: Azure CLI installed and logged in
# Run: .\deploy-azure.ps1

param(
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "ai-agent-rg",

    [Parameter(Mandatory=$false)]
    [string]$Location = "eastus",

    [Parameter(Mandatory=$false)]
    [string]$AppName = "ai-agent-rag-backend",

    [Parameter(Mandatory=$false)]
    [string]$AcrName = "aiagentacr$(Get-Random -Maximum 9999)"
)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI Agent RAG Backend - Azure Deployment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Azure CLI is installed
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Host "[OK] Azure CLI found: $($azVersion.'azure-cli')" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Azure CLI not found. Please install it from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Red
    exit 1
}

# Check if logged in
$account = az account show --output json 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "[INFO] Not logged in. Running 'az login'..." -ForegroundColor Yellow
    az login
    $account = az account show --output json | ConvertFrom-Json
}
Write-Host "[OK] Logged in as: $($account.user.name)" -ForegroundColor Green
Write-Host "[OK] Subscription: $($account.name)" -ForegroundColor Green
Write-Host ""

# Step 1: Create Resource Group
Write-Host "Step 1: Creating Resource Group..." -ForegroundColor Yellow
az group create --name $ResourceGroup --location $Location --output none
Write-Host "[OK] Resource Group '$ResourceGroup' created in '$Location'" -ForegroundColor Green

# Step 2: Create Azure Container Registry
Write-Host ""
Write-Host "Step 2: Creating Azure Container Registry..." -ForegroundColor Yellow
az acr create --name $AcrName --resource-group $ResourceGroup --sku Basic --admin-enabled true --output none
Write-Host "[OK] Container Registry '$AcrName' created" -ForegroundColor Green

# Step 3: Build and Push Docker Image
Write-Host ""
Write-Host "Step 3: Building and Pushing Docker Image..." -ForegroundColor Yellow
az acr login --name $AcrName
docker build -t "$AcrName.azurecr.io/${AppName}:latest" .
docker push "$AcrName.azurecr.io/${AppName}:latest"
Write-Host "[OK] Docker image pushed to ACR" -ForegroundColor Green

# Step 4: Create App Service Plan
Write-Host ""
Write-Host "Step 4: Creating App Service Plan..." -ForegroundColor Yellow
$planName = "${AppName}-plan"
az appservice plan create --name $planName --resource-group $ResourceGroup --is-linux --sku B1 --output none
Write-Host "[OK] App Service Plan '$planName' created" -ForegroundColor Green

# Step 5: Create Web App
Write-Host ""
Write-Host "Step 5: Creating Web App..." -ForegroundColor Yellow
az webapp create `
    --name $AppName `
    --resource-group $ResourceGroup `
    --plan $planName `
    --deployment-container-image-name "$AcrName.azurecr.io/${AppName}:latest" `
    --output none

# Configure ACR credentials
$acrPassword = az acr credential show --name $AcrName --query "passwords[0].value" -o tsv
az webapp config container set `
    --name $AppName `
    --resource-group $ResourceGroup `
    --docker-custom-image-name "$AcrName.azurecr.io/${AppName}:latest" `
    --docker-registry-server-url "https://$AcrName.azurecr.io" `
    --docker-registry-server-user $AcrName `
    --docker-registry-server-password $acrPassword `
    --output none

Write-Host "[OK] Web App '$AppName' created" -ForegroundColor Green

# Step 6: Configure App Settings
Write-Host ""
Write-Host "Step 6: Configuring App Settings..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Please enter your Azure OpenAI credentials:" -ForegroundColor Cyan

$apiKey = Read-Host "Azure OpenAI API Key"
$endpoint = Read-Host "Azure OpenAI Endpoint (e.g., https://myresource.openai.azure.com/)"
$deploymentName = Read-Host "Chat Model Deployment Name (e.g., gpt-4)"
$embeddingDeployment = Read-Host "Embedding Model Deployment Name (e.g., text-embedding-ada-002)"
$searchEndpoint = Read-Host "Azure AI Search Endpoint (e.g., https://mysearch.search.windows.net)"
$searchKey = Read-Host "Azure AI Search Admin Key"
$searchIndex = Read-Host "Azure AI Search Index Name (default: rag-index)"

if (-not $searchIndex) { $searchIndex = "rag-index" }

az webapp config appsettings set `
    --name $AppName `
    --resource-group $ResourceGroup `
    --settings `
        AZURE_OPENAI_API_KEY="$apiKey" `
        AZURE_OPENAI_ENDPOINT="$endpoint" `
        AZURE_OPENAI_DEPLOYMENT_NAME="$deploymentName" `
        AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME="$embeddingDeployment" `
        AZURE_OPENAI_API_VERSION="2024-02-15-preview" `
        AZURE_SEARCH_SERVICE_ENDPOINT="$searchEndpoint" `
        AZURE_SEARCH_ADMIN_KEY="$searchKey" `
        AZURE_SEARCH_INDEX_NAME="$searchIndex" `
        WEBSITES_PORT="8000" `
    --output none

Write-Host "[OK] App settings configured" -ForegroundColor Green

# Step 7: Get the URL
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
$appUrl = az webapp show --name $AppName --resource-group $ResourceGroup --query "defaultHostName" -o tsv
Write-Host ""
Write-Host "Your app is now live at:" -ForegroundColor White
Write-Host "  https://$appUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "API Documentation:" -ForegroundColor White
Write-Host "  https://$appUrl/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "To view logs:" -ForegroundColor Yellow
Write-Host "  az webapp log tail --name $AppName --resource-group $ResourceGroup"
Write-Host ""
