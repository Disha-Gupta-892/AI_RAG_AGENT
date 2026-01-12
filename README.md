# AI Agent RAG Backend

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)](https://fastapi.tiangolo.com/)
[![Azure OpenAI](https://img.shields.io/badge/Azure-OpenAI-blue.svg)](https://azure.microsoft.com/en-us/products/cognitive-services/openai-service)

An intelligent **AI Agent backend system** with **Retrieval-Augmented Generation (RAG)** capabilities, built with FastAPI and powered by Azure OpenAI.

---

## 📋 Table of Contents

- [Architecture Overview](#-architecture-overview)
- [Tech Stack](#-tech-stack)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Local Setup](#-local-setup)
- [Azure Deployment](#-azure-deployment)
- [API Reference](#-api-reference)
- [Design Decisions](#-design-decisions)
- [Limitations & Future Improvements](#-limitations--future-improvements)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT REQUEST                                │
│                         POST /api/v1/ask                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            FASTAPI SERVER                               │
│                         (Input Validation)                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           SESSION SERVICE                               │
│              (Get/Create Session, Load History)                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            AGENT SERVICE                                │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │           QUERY CLASSIFICATION (Tool Calling)                    │   │
│  │                                                                  │   │
│  │   Azure OpenAI analyzes query + decides:                        │   │
│  │   - Direct Answer (general knowledge)                           │   │
│  │   - Use RAG (document-specific questions)                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                          │                    │                         │
│              ┌───────────┴────────┐  ┌───────┴──────────┐              │
│              ▼                    │  ▼                  │              │
│  ┌─────────────────────┐         │  ┌─────────────────────────┐       │
│  │   DIRECT RESPONSE   │         │  │      RAG PIPELINE       │       │
│  │                     │         │  │                         │       │
│  │  LLM generates      │         │  │  1. Generate Query      │       │
│  │  answer directly    │         │  │     Embedding           │       │
│  │                     │         │  │  2. FAISS Vector Search │       │
│  └─────────────────────┘         │  │  3. Retrieve Top-K      │       │
│                                  │  │  4. Context Injection   │       │
│                                  │  │  5. LLM Generation      │       │
│                                  │  └─────────────────────────┘       │
│                                  │                                     │
└──────────────────────────────────┴─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          STRUCTURED RESPONSE                            │
│           { answer, sources, query_type, session_id }                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Query** → FastAPI validates and routes request
2. **Session Management** → Retrieves/creates session for conversation continuity
3. **Query Classification** → Agent uses Azure OpenAI with tool calling to decide approach
4. **Processing Path**:
   - **Direct**: LLM generates response from knowledge
   - **RAG**: Query embedding → FAISS search → Context injection → LLM response
5. **Response** → Structured JSON with answer, sources, and metadata

---

## 🛠️ Tech Stack

| Component             | Technology             | Purpose                       |
| --------------------- | ---------------------- | ----------------------------- |
| **Backend Framework** | FastAPI 0.109          | High-performance async API    |
| **LLM Provider**      | Azure OpenAI           | Chat completions & embeddings |
| **Vector Store**      | FAISS                  | Efficient similarity search   |
| **Embeddings**        | text-embedding-ada-002 | Document vectorization        |
| **Containerization**  | Docker                 | Deployment packaging          |
| **Cloud Platform**    | Azure (App Service)    | Production hosting            |

---

## ✨ Features

### Core Capabilities

- **🤖 Intelligent Query Routing**: Automatically determines optimal response strategy
- **📚 RAG Pipeline**: Retrieves relevant documents for context-aware answers
- **💬 Session Memory**: Maintains conversation history for contextual responses
- **🔧 Tool Calling**: Uses OpenAI function calling for smart decision-making
- **📊 Source Attribution**: Returns document sources with answers

### Technical Highlights

- **Async Architecture**: Non-blocking I/O for high concurrency
- **Type Safety**: Full Pydantic validation for requests/responses
- **Singleton Services**: Efficient resource management
- **Health Checks**: Production-ready monitoring endpoints
- **CORS Support**: Configurable cross-origin access

---

## 📁 Project Structure

```
ai-agent-rag-backend/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # API endpoint definitions
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py          # Configuration management
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Pydantic schemas
│   └── services/
│       ├── __init__.py
│       ├── agent_service.py   # Core AI agent logic
│       ├── azure_openai_service.py  # Azure OpenAI client
│       ├── rag_service.py     # RAG pipeline (FAISS)
│       └── session_service.py # Session management
├── documents/                  # Sample documents for RAG
│   ├── company_policies.txt
│   ├── company_faq.txt
│   ├── hr_policies.txt
│   ├── product_documentation.txt
│   └── technical_guidelines.txt
├── data/
│   └── faiss_index/           # Generated FAISS index
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container definition
├── docker-compose.yml         # Local development
├── .env.example               # Environment template
├── .gitignore
└── README.md
```

---

## 🚀 Local Setup

### Prerequisites

- Python 3.11+
- Azure OpenAI resource with deployments:
  - Chat model (e.g., `gpt-4` or `gpt-35-turbo`)
  - Embedding model (e.g., `text-embedding-ada-002`)

### Step 1: Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd ai-agent-rag-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Azure OpenAI credentials
# Required variables:
# - AZURE_OPENAI_API_KEY
# - AZURE_OPENAI_ENDPOINT
# - AZURE_OPENAI_DEPLOYMENT_NAME
# - AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME
```

### Step 3: Run the Application

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# OR production mode with Gunicorn
gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Step 4: Test the API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Ask a question (RAG)
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the remote work policy?"}'

# Ask a general question (Direct)
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the capital of France?"}'
```

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build and run manually
docker build -t ai-agent-rag .
docker run -p 8000:8000 --env-file .env ai-agent-rag
```

---

## ☁️ Azure Deployment

### Prerequisites

1. Azure subscription
2. Azure CLI installed and logged in
3. Azure OpenAI resource created with deployments

### Option 1: Azure App Service (Recommended)

#### Step 1: Create Azure Resources

```bash
# Set variables
RESOURCE_GROUP="ai-agent-rg"
LOCATION="eastus"
APP_NAME="ai-agent-rag-backend"
ACR_NAME="aiagentacr"

# Create Resource Group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure Container Registry
az acr create --name $ACR_NAME --resource-group $RESOURCE_GROUP --sku Basic --admin-enabled true
```

#### Step 2: Build and Push Docker Image

```bash
# Login to ACR
az acr login --name $ACR_NAME

# Build and push image
docker build -t $ACR_NAME.azurecr.io/$APP_NAME:latest .
docker push $ACR_NAME.azurecr.io/$APP_NAME:latest
```

#### Step 3: Create App Service

```bash
# Create App Service Plan
az appservice plan create \
  --name "${APP_NAME}-plan" \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku B1

# Create Web App
az webapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan "${APP_NAME}-plan" \
  --deployment-container-image-name "$ACR_NAME.azurecr.io/$APP_NAME:latest"

# Configure ACR credentials
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)
az webapp config container set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name "$ACR_NAME.azurecr.io/$APP_NAME:latest" \
  --docker-registry-server-url "https://$ACR_NAME.azurecr.io" \
  --docker-registry-server-user $ACR_NAME \
  --docker-registry-server-password $ACR_PASSWORD
```

#### Step 4: Configure Environment Variables

```bash
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    AZURE_OPENAI_API_KEY="your-api-key" \
    AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4" \
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME="text-embedding-ada-002" \
    AZURE_OPENAI_API_VERSION="2024-02-15-preview" \
    WEBSITES_PORT="8000"
```

#### Step 5: Access Your Application

```bash
# Get the URL
az webapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "defaultHostName" -o tsv

# Your app is now available at:
# https://{app-name}.azurewebsites.net
```

### Option 2: Azure Container Instances (Simpler)

```bash
# Create container instance
az container create \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --image $ACR_NAME.azurecr.io/$APP_NAME:latest \
  --registry-login-server $ACR_NAME.azurecr.io \
  --registry-username $ACR_NAME \
  --registry-password $ACR_PASSWORD \
  --dns-name-label $APP_NAME \
  --ports 8000 \
  --environment-variables \
    AZURE_OPENAI_API_KEY="your-key" \
    AZURE_OPENAI_ENDPOINT="your-endpoint" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4" \
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME="text-embedding-ada-002"

# Get the FQDN
az container show \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --query ipAddress.fqdn \
  --output tsv
```

---

## 📖 API Reference

### Base URL

- Local: `http://localhost:8000/api/v1`
- Production: `https://{your-app}.azurewebsites.net/api/v1`

### Endpoints

#### POST /ask

Main endpoint for querying the AI Agent.

**Request:**

```json
{
  "query": "What is the remote work policy?",
  "session_id": "optional-session-id"
}
```

**Response:**

```json
{
  "answer": "According to the company policy, employees can work remotely up to 3 days per week...",
  "sources": ["company_policies.txt"],
  "query_type": "rag",
  "session_id": "abc123-def456",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET /health

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### POST /reindex

Trigger document re-indexing.

**Response:**

```json
{
  "message": "Successfully indexed 25 document chunks"
}
```

#### DELETE /session/{session_id}

Clear session history.

**Response:**

```json
{
  "message": "Session abc123 cleared successfully"
}
```

---

## 🎯 Design Decisions

### 1. **Tool Calling for Query Classification**

Instead of simple keyword matching or rule-based classification, we use Azure OpenAI's function calling feature. This allows the model to intelligently decide when document retrieval is needed based on semantic understanding.

**Rationale**: More accurate classification, handles edge cases better, and is extensible for additional tools.

### 2. **FAISS for Vector Storage**

Chose FAISS over alternatives (Pinecone, Weaviate, ChromaDB) for several reasons:

- Zero external dependencies (runs locally)
- No API costs
- Fast similarity search
- Simple to deploy (file-based persistence)

**Trade-off**: Limited scalability compared to managed solutions, but suitable for the document volume in this use case.

### 3. **In-Memory Session Storage**

Used a simple dictionary-based session store instead of Redis or database.

**Rationale**:

- Simplifies deployment (no external dependencies)
- Sufficient for demonstration purposes
- Easy to replace with Redis for production scaling

### 4. **Singleton Service Pattern**

All services (Azure OpenAI, RAG, Session) use singleton pattern.

**Rationale**:

- Avoid re-initializing expensive resources
- Maintain single FAISS index in memory
- Consistent state across requests

### 5. **Chunking Strategy**

Used sentence-boundary-aware chunking with overlap.

**Rationale**:

- Preserves semantic coherence
- Overlap ensures context isn't lost at boundaries
- Configurable chunk size for tuning

---

## ⚠️ Limitations & Future Improvements

### Current Limitations

1. **Session Storage**: In-memory only; sessions lost on restart
2. **Document Types**: Only `.txt` files supported
3. **Scalability**: Single FAISS index limits horizontal scaling
4. **Authentication**: No built-in auth mechanism

### Recommended Improvements

| Area                 | Current        | Recommended                 |
| -------------------- | -------------- | --------------------------- |
| **Session Storage**  | In-memory dict | Redis or Azure Cache        |
| **Document Support** | Text only      | Add PDF, Word, HTML parsers |
| **Vector Store**     | Local FAISS    | Azure AI Search for scale   |
| **Auth**             | None           | Azure AD / API Keys         |
| **Monitoring**       | Basic logging  | Azure Application Insights  |
| **Rate Limiting**    | None           | Add middleware              |

### Production Checklist

- [ ] Add authentication/authorization
- [ ] Implement rate limiting
- [ ] Set up Azure Application Insights
- [ ] Configure Azure Key Vault for secrets
- [ ] Add request/response logging
- [ ] Implement circuit breaker for Azure OpenAI calls
- [ ] Set up CI/CD pipeline
- [ ] Add comprehensive unit/integration tests

---

## 📄 License

This project is provided as a demonstration for educational and evaluation purposes.

---

## 👤 Author

Built as an AI Engineer job assignment demonstration, showcasing:

- AI Agent development
- RAG system implementation
- Azure cloud deployment
- Production-ready Python development

---

_For questions or feedback, please open an issue in the repository._
