"""
Mock Azure OpenAI Service for Demo Mode.
Provides simulated responses without making actual API calls.
"""

import logging
import random
import hashlib
from typing import List, Optional

logger = logging.getLogger(__name__)


class MockChatCompletion:
    """Mock chat completion response."""
    def __init__(self, content: str):
        self.message = MockMessage(content)


class MockMessage:
    """Mock message object."""
    def __init__(self, content: str):
        self.content = content
        self.tool_calls = None


class MockChoice:
    """Mock choice object."""
    def __init__(self, message: MockMessage):
        self.message = message


class MockResponse:
    """Mock response object."""
    def __init__(self, content: str):
        self.choices = [MockChoice(MockMessage(content))]


class MockToolCall:
    """Mock tool call object."""
    def __init__(self, name: str, arguments: str):
        self.function = MockFunction(name, arguments)


class MockFunction:
    """Mock function object."""
    def __init__(self, name: str, arguments: str):
        self.name = name
        self.arguments = arguments


class MockToolMessage:
    """Mock message with tool calls."""
    def __init__(self, tool_calls=None):
        self.content = None
        self.tool_calls = tool_calls


class MockToolResponse:
    """Mock response with tool calls."""
    def __init__(self, tool_calls=None):
        self.choices = [MockChoice(MockToolMessage(tool_calls))]


# Predefined responses for demo
DEMO_RESPONSES = {
    "remote work": {
        "answer": """Based on our company policies, here's the remote work policy:

**Remote Work Guidelines:**
- Employees can work remotely up to **3 days per week**
- Core collaboration hours are **10 AM - 3 PM** in your local timezone
- You must have a stable internet connection and dedicated workspace
- Manager approval is required for remote work arrangements
- Remote work equipment (laptop, monitor) is provided by the company

**Requirements:**
1. Submit a remote work request through the HR portal
2. Complete the home office safety checklist
3. Attend mandatory in-office days (usually Tuesday and Thursday)

*Source: company_policies.txt*""",
        "sources": ["company_policies.txt"]
    },
    "pto": {
        "answer": """Here's the PTO (Paid Time Off) policy information:

**Annual PTO Allowance:**
- **Standard Employees**: 15 days per year
- **Senior Level (5+ years)**: 20 days per year
- **Management**: 25 days per year

**Additional Leave:**
- 🏥 Sick Leave: 10 days per year
- 👶 Parental Leave: 12 weeks paid
- 🎓 Education Leave: 5 days per year
- 🏠 Bereavement: 3-5 days depending on relation

**PTO Rollover:**
- Up to 5 unused PTO days can roll over to the next year
- Unused days beyond 5 are forfeited

*Source: hr_policies.txt*""",
        "sources": ["hr_policies.txt"]
    },
    "401k": {
        "answer": """Here's information about our 401(k) retirement benefits:

**401(k) Matching Policy:**
- Company matches **100% of the first 4%** of your salary contribution
- Additional **50% match on the next 2%** of contributions
- Maximum company match: **5% of your annual salary**

**Eligibility:**
- Full-time employees after 90 days of employment
- Part-time employees after 1 year (1,000+ hours)

**Vesting Schedule:**
- Year 1: 20%
- Year 2: 40%
- Year 3: 60%
- Year 4: 80%
- Year 5+: 100% vested

*Source: hr_policies.txt*""",
        "sources": ["hr_policies.txt"]
    },
    "cloudsync": {
        "answer": """Here are the key features of **CloudSync Pro**:

**Core Features:**
- ☁️ **Real-time Sync**: Automatic file synchronization across all devices
- 🔒 **End-to-end Encryption**: AES-256 encryption for all files
- 📁 **Smart Folders**: AI-powered automatic file organization
- 🔄 **Version History**: Keep up to 30 versions of each file
- 👥 **Team Collaboration**: Share files and folders with granular permissions

**Enterprise Features:**
- SSO Integration (SAML 2.0, OAuth 2.0)
- Admin Dashboard with analytics
- Compliance reports (SOC 2, HIPAA ready)
- API access for custom integrations

**Pricing:**
- Personal: $9.99/month
- Business: $19.99/user/month
- Enterprise: Custom pricing

*Source: product_documentation.txt*""",
        "sources": ["product_documentation.txt"]
    },
    "code review": {
        "answer": """Here are our code review requirements and guidelines:

**Code Review Standards:**

**Before Submitting:**
1. All code must pass automated tests
2. No linting errors allowed
3. Code coverage must be ≥80%
4. Documentation for public APIs required

**Review Process:**
- Minimum **2 approvals** required for merge
- At least 1 approval must be from a senior engineer
- Reviews should be completed within **24 business hours**
- Use conventional commit messages

**Best Practices:**
- Keep PRs small (< 400 lines of code)
- Include description of changes
- Add screenshots for UI changes
- Link related issues/tickets

**Tools:**
- GitHub for version control
- SonarQube for code quality
- Jest/PyTest for testing

*Source: technical_guidelines.txt*""",
        "sources": ["technical_guidelines.txt"]
    },
    "password": {
        "answer": """Here's how to reset your password:

**Self-Service Password Reset:**
1. Go to **https://sso.company.com/reset**
2. Enter your corporate email address
3. Click "Send Reset Link"
4. Check your email (also check spam folder)
5. Click the reset link (valid for 30 minutes)
6. Create a new password following the requirements

**Password Requirements:**
- Minimum 12 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character (!@#$%^&*)
- Cannot reuse last 10 passwords

**Need Help?**
Contact IT Help Desk: helpdesk@company.com or ext. 5555

*Source: company_faq.txt*""",
        "sources": ["company_faq.txt"]
    },
    "default": {
        "answer": """I found relevant information in our company documents. Here's what I can tell you:

This is a **demo response** showing how the AI Agent RAG system works. In production mode with Azure OpenAI:

1. 🔍 Your query would be analyzed by the AI
2. 📚 Relevant documents would be searched using FAISS vector similarity
3. 🤖 The LLM would generate a contextual response
4. 📌 Source documents would be cited

**Available Topics in Demo:**
- Remote work policy
- PTO/vacation days
- 401(k) matching
- CloudSync Pro features
- Code review standards
- Password reset

Try asking about any of these topics!

*Demo Mode Active - No Azure tokens used*""",
        "sources": ["demo_mode"]
    }
}

# General knowledge responses (no RAG needed)
GENERAL_RESPONSES = [
    "That's an interesting question! As your AI assistant, I'm happy to help. ",
    "Great question! Here's what I know: ",
    "I'd be glad to help with that. ",
]


class MockAzureOpenAIService:
    """
    Mock service for demo mode that simulates Azure OpenAI responses.
    """
    
    def __init__(self):
        """Initialize the mock service."""
        self.chat_deployment = "demo-gpt-4"
        self.embedding_deployment = "demo-embedding"
        self.client = self  # Self-reference for compatibility
        logger.info("Mock Azure OpenAI Service initialized (DEMO MODE)")

    def _should_use_rag(self, query: str) -> bool:
        """Determine if query should use RAG based on keywords."""
        rag_keywords = [
            "policy", "policies", "remote", "work", "pto", "vacation", 
            "leave", "401k", "retirement", "benefits", "cloudsync", 
            "product", "code review", "password", "reset", "hr", 
            "company", "documentation", "technical", "guidelines"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in rag_keywords)

    def _get_demo_response(self, query: str) -> dict:
        """Get appropriate demo response based on query."""
        query_lower = query.lower()
        
        if "remote" in query_lower or "work from home" in query_lower:
            return DEMO_RESPONSES["remote work"]
        elif "pto" in query_lower or "vacation" in query_lower or "time off" in query_lower or "days" in query_lower:
            return DEMO_RESPONSES["pto"]
        elif "401k" in query_lower or "retirement" in query_lower or "matching" in query_lower:
            return DEMO_RESPONSES["401k"]
        elif "cloudsync" in query_lower or "product" in query_lower or "feature" in query_lower:
            return DEMO_RESPONSES["cloudsync"]
        elif "code review" in query_lower or "review" in query_lower or "pr" in query_lower:
            return DEMO_RESPONSES["code review"]
        elif "password" in query_lower or "reset" in query_lower:
            return DEMO_RESPONSES["password"]
        else:
            return DEMO_RESPONSES["default"]

    def get_chat_completion(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate a mock chat completion.
        """
        # Get the last user message
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        # Check if this is a RAG response (system prompt contains context)
        system_prompt = messages[0].get("content", "") if messages else ""
        if "RETRIEVED CONTEXT" in system_prompt:
            response = self._get_demo_response(user_message)
            return response["answer"]
        
        # General response
        prefix = random.choice(GENERAL_RESPONSES)
        return f"{prefix}This is a demo response. In production, I would use Azure OpenAI to provide a detailed answer to: '{user_message[:50]}...'"

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate mock embeddings (deterministic based on text hash).
        """
        embeddings = []
        for text in texts:
            # Create deterministic embedding based on text hash
            hash_obj = hashlib.md5(text.encode())
            hash_bytes = hash_obj.digest()
            # Create 1536-dimensional embedding (same as ada-002)
            embedding = []
            for i in range(1536):
                byte_idx = i % 16
                embedding.append((hash_bytes[byte_idx] + i) / 255.0 - 0.5)
            embeddings.append(embedding)
        return embeddings

    def get_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return self.get_embeddings([text])[0]

    class ChatCompletions:
        """Mock chat completions class."""
        def __init__(self, parent):
            self.parent = parent
        
        def create(self, model, messages, tools=None, tool_choice=None, temperature=0.7, max_tokens=1000):
            """Mock create method for chat completions with tool support."""
            user_message = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break
            
            # Check if we should use RAG
            if tools and self.parent._should_use_rag(user_message):
                # Return a tool call
                import json
                tool_call = MockToolCall(
                    "search_documents",
                    json.dumps({"query": user_message})
                )
                return MockToolResponse([tool_call])
            
            # Return direct response
            content = self.parent.get_chat_completion(messages, temperature, max_tokens)
            return MockResponse(content)

    @property
    def chat(self):
        """Return mock chat object."""
        class ChatMock:
            def __init__(self, parent):
                self.completions = MockAzureOpenAIService.ChatCompletions(parent)
        return ChatMock(self)


# Singleton instance
_mock_service: Optional[MockAzureOpenAIService] = None


def get_mock_openai_service() -> MockAzureOpenAIService:
    """Get or create the mock OpenAI service singleton."""
    global _mock_service
    if _mock_service is None:
        _mock_service = MockAzureOpenAIService()
    return _mock_service
