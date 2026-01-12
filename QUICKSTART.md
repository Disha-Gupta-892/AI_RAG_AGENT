# ============================================================

# QUICK START & DEPLOYMENT GUIDE

# AI Agent RAG Backend

# ============================================================

## 📋 WHAT YOU NEED

### For Local Testing:

1. Azure subscription (free tier works)
2. Azure OpenAI resource with deployed models
3. Python 3.11+

### For Azure Deployment:

1. All of the above, plus:
2. Azure CLI installed
3. Docker Desktop installed

---

## 🔧 STEP 1: SET UP AZURE OPENAI (5-10 minutes)

### 1.1 Create Azure OpenAI Resource

1. Go to: https://portal.azure.com
2. Search for "Azure OpenAI" in the top search bar
3. Click "Create"
4. Fill in:
   - Subscription: Your subscription
   - Resource group: Create new → "ai-agent-rg"
   - Region: "East US" (or your region)
   - Name: "my-openai-resource" (your choice)
   - Pricing: Standard S0
5. Click "Review + create" → "Create"
6. Wait 2-5 minutes for deployment

### 1.2 Deploy Models (IMPORTANT!)

1. Go to: https://oai.azure.com (Azure OpenAI Studio)
2. Select your resource
3. Click "Deployments" in left menu
4. Deploy GPT-4 (or GPT-3.5-turbo):
   - Click "+ Create new deployment"
   - Model: gpt-4 (or gpt-35-turbo)
   - Deployment name: gpt-4 (REMEMBER THIS!)
   - Click "Create"
5. Deploy Embeddings model:
   - Click "+ Create new deployment"
   - Model: text-embedding-ada-002
   - Deployment name: text-embedding-ada-002 (REMEMBER THIS!)
   - Click "Create"

### 1.3 Get Your Credentials

1. Go back to Azure Portal (https://portal.azure.com)
2. Find your Azure OpenAI resource
3. Click "Keys and Endpoint" in the left menu
4. Copy:
   - Endpoint: https://YOUR-RESOURCE.openai.azure.com/
   - KEY 1: Your secret API key

---

## 🖥️ STEP 2: RUN LOCALLY (5 minutes)

### 2.1 Configure Environment

# In PowerShell, navigate to project:

cd "d:\project first500\ai-agent-rag-backend"

# Copy the environment file:

copy .env.example .env

# Now EDIT the .env file with your Azure OpenAI credentials!

# Open .env and replace:

# - AZURE_OPENAI_API_KEY=your_actual_key_here

# - AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# - AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# - AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=text-embedding-ada-002

### 2.2 Start the Server

# Activate virtual environment (if not already):

.\venv\Scripts\Activate

# Run the server:

uvicorn main:app --reload --host 0.0.0.0 --port 8000

### 2.3 Test It!

Open browser: http://localhost:8000

- Click on suggestion cards to test queries
- Try asking about remote work policy
- Check the RAG badge shows "RAG" for document questions

---

## ☁️ STEP 3: DEPLOY TO AZURE (15-20 minutes)

### Option A: Automated Script (Easier)

# Make sure Docker Desktop is running!

# Make sure you're logged into Azure CLI: az login

# Run the deployment script:

.\deploy-azure.ps1

# Follow the prompts to enter your Azure OpenAI credentials

### Option B: Manual Deployment

#### 3.1 Install Prerequisites

# Install Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli

# Install Docker Desktop: https://www.docker.com/products/docker-desktop

# Login to Azure:

az login

#### 3.2 Create Azure Resources

# Set variables

$RESOURCE_GROUP = "ai-agent-rg"
$LOCATION = "eastus"
$APP_NAME = "ai-agent-rag-backend"
$ACR_NAME = "aiagentacr123" # must be unique, lowercase, no dashes

# Create resource group

az group create --name $RESOURCE_GROUP --location $LOCATION

# Create container registry

az acr create --name $ACR_NAME --resource-group $RESOURCE_GROUP --sku Basic --admin-enabled true

#### 3.3 Build and Push Docker Image

# Login to your ACR

az acr login --name $ACR_NAME

# Build the image

docker build -t "$ACR_NAME.azurecr.io/${APP_NAME}:latest" .

# Push to ACR

docker push "$ACR_NAME.azurecr.io/${APP_NAME}:latest"

#### 3.4 Create App Service

# Create App Service Plan

az appservice plan create --name "${APP_NAME}-plan" --resource-group $RESOURCE_GROUP --is-linux --sku B1

# Create Web App

az webapp create --name $APP_NAME --resource-group $RESOURCE_GROUP --plan "${APP_NAME}-plan" --deployment-container-image-name "$ACR_NAME.azurecr.io/${APP_NAME}:latest"

# Configure container registry

$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv
az webapp config container set --name $APP_NAME --resource-group $RESOURCE_GROUP --docker-custom-image-name "$ACR_NAME.azurecr.io/${APP_NAME}:latest" --docker-registry-server-url "https://$ACR_NAME.azurecr.io" --docker-registry-server-user $ACR_NAME --docker-registry-server-password $ACR_PASSWORD

#### 3.5 Configure Environment Variables

az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings AZURE_OPENAI_API_KEY="your-key" AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/" AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4" AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME="text-embedding-ada-002" AZURE_OPENAI_API_VERSION="2024-02-15-preview" WEBSITES_PORT="8000"

#### 3.6 Get Your App URL

$APP_URL = az webapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "defaultHostName" -o tsv
Write-Host "Your app is live at: https://$APP_URL"

---

## ✅ VERIFICATION CHECKLIST

After deployment, verify:

[ ] App loads at https://your-app.azurewebsites.net
[ ] Health check works: https://your-app.azurewebsites.net/api/v1/health
[ ] API docs accessible: https://your-app.azurewebsites.net/docs
[ ] Chat works: Click a suggestion card and get a response
[ ] RAG works: Questions about documents show "RAG" badge and sources

---

## 🔍 TROUBLESHOOTING

### "Couldn't find relevant information"

- Azure OpenAI credentials are wrong or missing
- Check the .env file has correct values
- Restart the server after changing .env

### "Connection Error" in frontend

- Server is not running
- Run: uvicorn main:app --reload

### "Model not found" error

- Your deployment names in .env don't match Azure OpenAI Studio
- Go to Azure OpenAI Studio > Deployments and check exact names

### Docker build fails

- Make sure Docker Desktop is running
- Try: docker system prune (clears old data)

### Azure deployment fails

- Make sure Azure CLI is logged in: az login
- Check subscription: az account show

---

## 💰 COST ESTIMATE

### Development (minimal usage):

- Azure OpenAI: ~$5-10/month
- Azure App Service B1: ~$13/month
- Azure Container Registry: ~$5/month
- Total: ~$25/month

### Production (moderate usage):

- Azure OpenAI: ~$50-100/month
- Azure App Service B2: ~$55/month
- Total: ~$100-200/month

---

## 📞 NEED HELP?

1. Check Azure OpenAI docs: https://learn.microsoft.com/en-us/azure/ai-services/openai/
2. FastAPI docs: https://fastapi.tiangolo.com/
3. Azure App Service docs: https://learn.microsoft.com/en-us/azure/app-service/
