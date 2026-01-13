# AI Agent RAG Backend - Test Suite

This document describes the test suite for the AI Agent RAG Backend.

## Test Coverage

### 1. API Endpoint Tests (`tests/test_api.py`)
Tests all FastAPI REST endpoints:

- **Health Check** (`TestHealthEndpoint`)
  - `test_health_check` - Verifies health endpoint returns healthy status
  - `test_health_check_content_type` - Checks JSON content type

- **Root Endpoint** (`TestRootEndpoint`)
  - `test_api_info` - Verifies API information endpoint

- **Ask Endpoint** (`TestAskEndpoint`)
  - `test_ask_with_valid_query` - Tests asking company policy questions
  - `test_ask_with_session_id_new` - Tests session creation with provided ID
  - `test_ask_maintains_conversation` - Verifies conversation continuity
  - `test_ask_with_empty_query` - Validates input validation
  - `test_ask_with_missing_query` - Tests missing parameter handling
  - `test_ask_with_general_knowledge_question` - Tests direct LLM responses
  - `test_ask_with_product_question` - Tests RAG for product queries

- **Reindex Endpoint** (`TestReindexEndpoint`)
  - `test_reindex_documents` - Tests document indexing

- **Session Endpoint** (`TestSessionEndpoint`)
  - `test_create_session` - Tests automatic session creation
  - `test_clear_session` - Tests session clearing
  - `test_clear_nonexistent_session` - Tests 404 handling

- **Frontend** (`TestFrontendEndpoints`)
  - `test_frontend_served` - Tests frontend serving

### 2. RAG Service Tests (`tests/test_rag_service.py`)
Tests document processing and retrieval:

- **DocumentChunk** (`TestDocumentChunk`)
  - `test_document_chunk_creation` - Tests chunk object creation
  - `test_document_chunk_repr` - Tests string representation

- **RAG Service** (`TestRAGService`)
  - `test_rag_service_initialization` - Verifies service setup
  - `test_get_rag_service_singleton` - Tests singleton pattern
  - `test_chunk_text_basic` - Tests basic text chunking
  - `test_chunk_text_short_text` - Tests short text handling
  - `test_search_empty_index` - Tests empty index behavior
  - `test_search_with_results` - Tests search functionality
  - `test_get_context_for_query` - Tests context retrieval

- **Integration** (`TestRAGServiceIntegration`)
  - `test_index_documents` - Tests full document indexing
  - `test_search_company_policy` - Tests policy document search
  - `test_search_with_top_k_parameter` - Tests result limiting

### 3. Session Service Tests (`tests/test_session_service.py`)
Tests conversation memory management:

- **SessionService** (`TestSessionService`)
  - `test_session_service_initialization` - Verifies service setup
  - `test_get_session_service_singleton` - Tests singleton pattern
  - `test_create_new_session` - Tests session creation
  - `test_get_existing_session` - Tests session retrieval
  - `test_get_or_create_session_with_existing_id` - Tests ID reuse
  - `test_add_message_to_session` - Tests message storage
  - `test_get_conversation_history` - Tests history retrieval
  - `test_get_history_nonexistent_session` - Tests empty history
  - `test_clear_session` - Tests session clearing
  - `test_clear_nonexistent_session` - Tests missing session handling
  - `test_add_message_to_nonexistent_session` - Tests error handling
  - `test_message_history_limit` - Tests history truncation

- **SessionData** (`TestSessionData`)
  - `test_session_data_creation` - Tests data model creation
  - `test_session_data_with_messages` - Tests messages in session

- **SessionMessage** (`TestSessionMessage`)
  - `test_session_message_creation` - Tests message model

## Running Tests

### Prerequisites
```bash
# Install test dependencies
pip install pytest httpx
```

### Run All Tests
```bash
# Run all tests with verbose output
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=term-missing
```

### Run Specific Test Files
```bash
# Run API tests only
python -m pytest tests/test_api.py -v

# Run RAG service tests
python -m pytest tests/test_rag_service.py -v

# Run session service tests
python -m pytest tests/test_session_service.py -v
```

### Run Specific Test Classes
```bash
# Run all health endpoint tests
python -m pytest tests/test_api.py::TestHealthEndpoint -v

# Run all RAG integration tests
python -m pytest tests/test_rag_service.py::TestRAGServiceIntegration -v
```

### Run Single Tests
```bash
# Run a specific test
python -m pytest tests/test_api.py::TestHealthEndpoint::test_health_check -v
```

## Test Configuration

Tests are configured via `pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
filterwarnings =
    ignore::DeprecationWarning
```

## Demo Mode

The test suite runs in **demo mode** by default, which:
- Uses mock Azure OpenAI responses
- Does not require Azure credentials
- Tests all functionality with simulated responses

This allows full test coverage without cloud dependencies.

## Test Fixtures

### `client`
Creates a FastAPI `TestClient` for HTTP testing.

### `setup_test_environment`
Resets all service singletons before each test to ensure test isolation.

## Continuous Integration

To run tests in CI/CD pipelines:
```bash
python -m pytest tests/ -v --tb=short --junit-xml=test-results.xml
```

Generate JUnit XML for CI integration.

## Best Practices

1. **Test Isolation**: Each test resets service singletons
2. **Deterministic Tests**: Mock services provide consistent responses
3. **Descriptive Names**: Test names describe the behavior being tested
4. **Edge Cases**: Tests cover error conditions and edge cases
5. **Integration Testing**: API tests verify end-to-end functionality

## Adding New Tests

1. Add test file to `tests/` directory
2. Follow naming convention: `test_*.py`
3. Import required modules
4. Create test classes with `Test*` prefix
5. Use pytest fixtures for setup/cleanup
6. Run tests to verify they pass

