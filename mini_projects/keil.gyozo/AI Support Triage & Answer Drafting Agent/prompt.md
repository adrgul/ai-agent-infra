# AI Support Triage & Answer Drafting Agent - VS Code 2026 Development Prompt

## Project: SupportAI
**Customer Support Triage and Response Agent with Knowledge Base**

---

## 🎯 PROJECT MISSION

Build a production-ready Python AI agent that automatically:
- **Triages** customer support tickets (category, priority, team assignment)
- **Analyzes** sentiment and intent
- **Retrieves** relevant knowledge base articles using RAG
- **Generates** draft responses with proper citations
- **Validates** output against company policies

---

## 📊 BUSINESS IMPACT

| Objective | Implementation | Target Metric |
|-----------|---------------|---------------|
| Reduce support workload | Automated triage + draft responses | **-40%** manual triage time |
| Accelerate response time | Sub-second categorization + drafting | **85% → 95%** SLA compliance |
| Standardize communication | Policy-based responses with tone control | **-60%** customer complaints |
| Scale senior support capacity | AI handles simple, humans handle complex | **+50%** senior capacity |

---

## 🏗️ SYSTEM ARCHITECTURE

### Input
Customer message from any channel (ticket/email/chat)

### Processing Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│  TICKET INPUT                                               │
│  From: john.doe@example.com                                 │
│  Subject: Charged twice for subscription!                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  NODE 1: INTENT DETECTION (LLM)                             │
│  • Classify problem type: billing/technical/account/feature │
│  • Analyze sentiment: frustrated/neutral/satisfied          │
│  Output: {type: "billing", sentiment: "frustrated"}         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  NODE 2: TRIAGE CLASSIFICATION (LLM)                        │
│  • Determine category: "Billing - Invoice Issue"            │
│  • Assign priority: P1 (Critical) / P2 (Medium)             │
│  • Set SLA: 4h / 24h / 48h                                  │
│  • Route to team: Finance Team                              │
│  Output: {category, priority, sla_hours, team, confidence}  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  NODE 3: QUERY EXPANSION (LLM)                              │
│  • Generate semantic search queries                         │
│  • Expand abbreviations and technical terms                 │
│  • Create variations for better retrieval                   │
│  Output: ["duplicate charge refund", "invoice error fix"]   │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  NODE 4: VECTOR SEARCH (Embeddings + Database)              │
│  • Embed queries using text-embedding-3-large               │
│  • Search vector DB (Pinecone/Weaviate/Qdrant)              │
│  • Retrieve top-k=10 similar KB articles                    │
│  Output: [KB-1234, KB-5678, FAQ-910, ...]                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  NODE 5: RE-RANKING (Cross-encoder / LLM)                   │
│  • Score relevance of retrieved documents                   │
│  • Re-rank and select top-3 most relevant                   │
│  • Filter out low-quality matches                           │
│  Output: Top 3 citations with scores                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  NODE 6: DRAFT GENERATION (LLM + Templates)                 │
│  • Select response template based on category               │
│  • Generate personalized response body                      │
│  • Integrate citations: [KB-1234], [FAQ-910]                │
│  • Apply appropriate tone: empathetic/professional/friendly │
│  Output: Complete draft with greeting, body, closing        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  NODE 7: POLICY CHECK (Guardrails)                          │
│  • Validate no unauthorized promises (refunds, discounts)   │
│  • Check SLA mentions are accurate                          │
│  • Flag if escalation needed                                │
│  • Ensure compliance with company policies                  │
│  Output: {compliance: "passed", escalation_needed: false}   │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  NODE 8: JSON OUTPUT VALIDATION                             │
│  • Validate against Pydantic schema                         │
│  • Check citation format correctness                        │
│  • Ensure all required fields present                       │
│  Output: Structured JSON with triage + draft + citations    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 EXPECTED OUTPUT FORMAT

```json
{
  "ticket_id": "TKT-2025-12-09-4567",
  "timestamp": "2025-12-09T14:32:00Z",
  
  "triage": {
    "category": "Billing - Invoice Issue",
    "subcategory": "Duplicate Charge",
    "priority": "P2",
    "sla_hours": 24,
    "suggested_team": "Finance Team",
    "sentiment": "frustrated",
    "confidence": 0.92
  },
  
  "answer_draft": {
    "greeting": "Dear John,",
    "body": "Thank you for reaching out regarding the duplicate charge on your invoice. I understand this can be frustrating. [KB-1234]\n\nBased on our records, duplicate charges are typically resolved within 3-5 business days through our automated refund process. [FAQ-910]\n\nTo expedite this, I recommend:\n1. Verifying the charge amount ($49.99)\n2. Confirming the transaction date (Dec 5)\n3. Replying with your transaction ID\n\nOur Finance Team will review and process the refund accordingly. [KB-5678]",
    "closing": "Best regards,\nSupport Team",
    "tone": "empathetic_professional"
  },
  
  "citations": [
    {
      "doc_id": "KB-1234",
      "chunk_id": "c-45",
      "title": "How to Handle Duplicate Charges",
      "score": 0.89,
      "url": "https://kb.company.com/billing/duplicate-charges"
    },
    {
      "doc_id": "FAQ-910",
      "chunk_id": "c-12",
      "title": "Refund Processing Timeframes",
      "score": 0.85,
      "url": "https://kb.company.com/faq/refunds"
    },
    {
      "doc_id": "KB-5678",
      "chunk_id": "c-78",
      "title": "Finance Team SLA Policy",
      "score": 0.81,
      "url": "https://kb.company.com/policies/sla"
    }
  ],
  
  "policy_check": {
    "refund_promise": false,
    "sla_mentioned": true,
    "escalation_needed": false,
    "compliance": "passed"
  }
}
```

---

## 🛠️ TECHNICAL STACK

### Core Dependencies
```
python >= 3.11
langchain >= 0.1.0
langgraph >= 0.0.30
openai >= 1.0.0
pydantic >= 2.0.0
python-dotenv >= 1.0.0
```

### Vector Database (Choose One)
```
pinecone-client >= 3.0.0
# OR
weaviate-client >= 4.0.0
# OR
qdrant-client >= 1.7.0
```

### LLM & Embeddings
- **LLM**: GPT-4-turbo OR Claude 3.5 Sonnet
- **Embeddings**: OpenAI `text-embedding-3-large` (3072 dimensions)
- **Re-ranker**: Cohere Rerank API OR LLM-based scoring

### Optional Integrations
```
# Email
imaplib (built-in)
smtplib (built-in)

# Ticketing systems
zenpy  # Zendesk
freshdesk-api

# Communications
slack-sdk
pymsteams  # MS Teams

# Project management
jira
```

---

## 📁 PROJECT STRUCTURE

```
support-ai/
│
├── src/
│   ├── __init__.py
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── intent_detector.py       # Node 1: Classify intent & sentiment
│   │   ├── triage_classifier.py     # Node 2: Category, priority, SLA
│   │   ├── query_expander.py        # Node 3: Generate search queries
│   │   ├── draft_generator.py       # Node 6: Create response draft
│   │   └── policy_checker.py        # Node 7: Validate compliance
│   │
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── vector_store.py          # Node 4: Vector DB interface
│   │   ├── embeddings.py            # Embedding generation
│   │   └── reranker.py              # Node 5: Document re-ranking
│   │
│   ├── workflow/
│   │   ├── __init__.py
│   │   ├── langgraph_flow.py        # Main LangGraph workflow
│   │   └── state.py                 # Workflow state definition
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── input_schema.py          # Ticket input validation
│   │   └── output_schema.py         # JSON output models (Pydantic)
│   │
│   ├── templates/
│   │   ├── __init__.py
│   │   ├── prompts.py               # LLM prompt templates
│   │   └── response_templates.py    # Response structure templates
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py            # Schema & policy validators
│   │   ├── logger.py                # Logging configuration
│   │   └── config.py                # Environment configuration
│   │
│   └── integrations/
│       ├── __init__.py
│       ├── email_connector.py       # Email ingestion
│       ├── zendesk_connector.py     # Zendesk API
│       └── slack_notifier.py        # Slack notifications
│
├── data/
│   ├── knowledge_base/
│   │   ├── raw/                     # Original KB articles
│   │   ├── processed/               # Chunked & embedded
│   │   └── embeddings/              # Vector index
│   │
│   └── examples/
│       └── sample_tickets.json      # Test data
│
├── tests/
│   ├── __init__.py
│   ├── test_agents/
│   ├── test_retrieval/
│   ├── test_workflow/
│   └── test_integration/
│
├── notebooks/
│   ├── 01_data_preparation.ipynb    # KB processing
│   ├── 02_embedding_generation.ipynb
│   └── 03_evaluation.ipynb          # Metrics & testing
│
├── .env.example                     # Environment variables template
├── .gitignore
├── requirements.txt
├── setup.py
├── README.md
└── main.py                          # Entry point
```

---

## 🚀 IMPLEMENTATION GUIDE FOR VS CODE 2026 AI AGENT

### PHASE 1: Environment Setup

**Step 1.1**: Create project structure
```python
# Ask VS Code AI Agent:
"Create a Python project with the folder structure shown above. 
Initialize __init__.py files in all packages."
```

**Step 1.2**: Setup virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Step 1.3**: Install dependencies
```python
# Ask VS Code AI Agent:
"Generate a requirements.txt file with all dependencies listed in the 
Technical Stack section. Include version pinning for production use."
```

**Step 1.4**: Configure environment variables
```python
# Ask VS Code AI Agent:
"Create a .env.example file with the following API keys:
- OPENAI_API_KEY
- PINECONE_API_KEY (or WEAVIATE_URL, or QDRANT_URL)
- COHERE_API_KEY (for re-ranking)
- Optional: ZENDESK_EMAIL, ZENDESK_TOKEN, SLACK_WEBHOOK_URL"
```

---

### PHASE 2: Data Layer - Schemas & State

**Step 2.1**: Define Pydantic schemas
```python
# Prompt for VS Code AI Agent:
"""
Create src/schemas/output_schema.py with Pydantic v2 models:

1. TriageOutput model with fields:
   - category (str)
   - subcategory (str)
   - priority (Literal["P1", "P2", "P3"])
   - sla_hours (int)
   - suggested_team (str)
   - sentiment (Literal["frustrated", "neutral", "satisfied"])
   - confidence (float between 0-1)

2. AnswerDraft model with fields:
   - greeting (str)
   - body (str)
   - closing (str)
   - tone (str)

3. Citation model with fields:
   - doc_id (str)
   - chunk_id (str)
   - title (str)
   - score (float)
   - url (HttpUrl)

4. PolicyCheck model with fields:
   - refund_promise (bool)
   - sla_mentioned (bool)
   - escalation_needed (bool)
   - compliance (Literal["passed", "failed"])

5. SupportAgentOutput model (main) combining all above:
   - ticket_id (str)
   - timestamp (datetime)
   - triage (TriageOutput)
   - answer_draft (AnswerDraft)
   - citations (List[Citation])
   - policy_check (PolicyCheck)

Add proper validation, examples, and docstrings.
"""
```

**Step 2.2**: Define workflow state
```python
# Prompt for VS Code AI Agent:
"""
Create src/workflow/state.py with a TypedDict for LangGraph state:

WorkflowState should include:
- ticket_id (str)
- original_message (str)
- customer_email (str | None)
- intent (dict | None)
- triage (dict | None)
- search_queries (list[str] | None)
- retrieved_docs (list[dict] | None)
- reranked_docs (list[dict] | None)
- draft (dict | None)
- policy_check (dict | None)
- final_output (dict | None)
- errors (list[str])

Use proper type hints and add docstrings.
"""
```

---

### PHASE 3: Core Agent Nodes

**Step 3.1**: Intent Detection Node
```python
# Prompt for VS Code AI Agent:
"""
Create src/agents/intent_detector.py with a function:

def detect_intent(state: WorkflowState) -> WorkflowState:
    '''
    Analyzes customer message to detect:
    1. Problem type: billing, technical, account, feature_request
    2. Sentiment: frustrated, neutral, satisfied
    
    Uses LLM with structured output (JSON mode).
    Returns updated state with intent dict.
    '''

Use OpenAI GPT-4 with JSON mode.
Include prompt template with few-shot examples.
Add error handling and logging.
Return confidence score.
"""
```

**Step 3.2**: Triage Classification Node
```python
# Prompt for VS Code AI Agent:
"""
Create src/agents/triage_classifier.py with a function:

def classify_triage(state: WorkflowState) -> WorkflowState:
    '''
    Classifies ticket based on intent:
    - Category (e.g., "Billing - Invoice Issue")
    - Subcategory (e.g., "Duplicate Charge")
    - Priority: P1 (4h), P2 (24h), P3 (48h)
    - Suggested team routing
    
    Uses LLM with structured output.
    '''

Priority rules:
- P1: Account locked, payment failures, security issues
- P2: Billing issues, feature bugs, urgent requests
- P3: General questions, feature requests, documentation

Use function calling or JSON mode for structured output.
Add validation against known categories.
"""
```

**Step 3.3**: Query Expansion Node
```python
# Prompt for VS Code AI Agent:
"""
Create src/agents/query_expander.py with a function:

def expand_queries(state: WorkflowState) -> WorkflowState:
    '''
    Generates 3-5 semantic search queries from the ticket:
    - Expand abbreviations (e.g., "txn" → "transaction")
    - Add synonyms (e.g., "charge" → "billing", "payment")
    - Create specific + general variations
    
    Example input: "Charged twice for subscription"
    Example output: [
        "duplicate subscription charge",
        "double billing issue",
        "refund duplicate payment",
        "invoice error multiple charges"
    ]
    '''

Use LLM to generate queries.
Limit to 3-5 diverse queries.
No queries longer than 10 words.
"""
```

**Step 3.4**: Draft Generator Node
```python
# Prompt for VS Code AI Agent:
"""
Create src/agents/draft_generator.py with a function:

def generate_draft(state: WorkflowState) -> WorkflowState:
    '''
    Generates personalized response draft:
    - Greeting with customer name (if available)
    - Empathetic opening acknowledging issue
    - Solution steps from KB articles
    - Citations in format [KB-1234]
    - Professional closing
    
    Tone adaptation:
    - frustrated → empathetic, apologetic
    - neutral → professional, helpful
    - satisfied → friendly, encouraging
    '''

Use retrieved documents from state['reranked_docs'].
Generate response in sections: greeting, body, closing.
Integrate citations naturally in body.
Validate citations reference actual retrieved docs.
"""
```

**Step 3.5**: Policy Checker Node
```python
# Prompt for VS Code AI Agent:
"""
Create src/agents/policy_checker.py with a function:

def check_policies(state: WorkflowState) -> WorkflowState:
    '''
    Validates draft response against company policies:
    
    1. Refund promises: 
       - BLOCK: "We'll refund you immediately"
       - ALLOW: "Our Finance team will review your refund request"
    
    2. SLA promises:
       - BLOCK: "Fixed within 24 hours guaranteed"
       - ALLOW: "Typically resolved within 24-48 hours"
    
    3. Escalation triggers:
       - Legal threats → escalate
       - Account closure threats → escalate
       - Multiple unresolved tickets → escalate
    
    Returns policy_check dict with violations and flags.
    '''

Use LLM or rule-based validation.
Log all policy violations.
Set escalation_needed flag when appropriate.
"""
```

---

### PHASE 4: Retrieval System

**Step 4.1**: Vector Store Setup
```python
# Prompt for VS Code AI Agent:
"""
Create src/retrieval/vector_store.py with a VectorStore class:

class VectorStore:
    '''
    Manages vector database operations for KB articles.
    Supports Pinecone, Weaviate, or Qdrant.
    '''
    
    def __init__(self, provider: str = "pinecone"):
        # Initialize connection based on provider
        
    def add_documents(self, documents: List[Document]):
        # Chunk documents, generate embeddings, store vectors
        
    def search(self, query: str, top_k: int = 10) -> List[Document]:
        # Embed query, perform similarity search
        
    def delete_by_id(self, doc_id: str):
        # Remove document from index

Use text-embedding-3-large for embeddings (3072 dim).
Chunk documents: 500-1000 tokens with 100 token overlap.
Store metadata: doc_id, chunk_id, title, url, category.
"""
```

**Step 4.2**: Re-ranker Implementation
```python
# Prompt for VS Code AI Agent:
"""
Create src/retrieval/reranker.py with a Reranker class:

class Reranker:
    '''
    Re-ranks retrieved documents for relevance.
    Supports Cohere Rerank API or LLM-based scoring.
    '''
    
    def __init__(self, method: str = "cohere"):
        # Initialize Cohere client or LLM
        
    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 3
    ) -> List[Document]:
        '''
        Re-ranks documents and returns top_k most relevant.
        Adds relevance_score to each document.
        '''

For Cohere: use cohere.rerank endpoint.
For LLM: score each doc 0-10, select top_k.
Filter out scores below 0.7 threshold.
"""
```

---

### PHASE 5: LangGraph Workflow

**Step 5.1**: Build workflow graph
```python
# Prompt for VS Code AI Agent:
"""
Create src/workflow/langgraph_flow.py with the complete workflow:

from langgraph.graph import StateGraph, END
from src.workflow.state import WorkflowState

def create_support_workflow() -> StateGraph:
    '''
    Creates LangGraph workflow connecting all nodes:
    
    1. intent_detection
    2. triage_classification
    3. query_expansion
    4. vector_search
    5. reranking
    6. draft_generation
    7. policy_check
    8. output_validation
    '''
    
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("detect_intent", detect_intent)
    workflow.add_node("classify_triage", classify_triage)
    workflow.add_node("expand_queries", expand_queries)
    workflow.add_node("vector_search", vector_search_node)
    workflow.add_node("rerank", rerank_node)
    workflow.add_node("generate_draft", generate_draft)
    workflow.add_node("check_policy", check_policies)
    workflow.add_node("validate_output", validate_output_node)
    
    # Add edges
    workflow.set_entry_point("detect_intent")
    workflow.add_edge("detect_intent", "classify_triage")
    workflow.add_edge("classify_triage", "expand_queries")
    workflow.add_edge("expand_queries", "vector_search")
    workflow.add_edge("vector_search", "rerank")
    workflow.add_edge("rerank", "generate_draft")
    workflow.add_edge("generate_draft", "check_policy")
    
    # Conditional edge: if policy fails, flag for human review
    workflow.add_conditional_edges(
        "check_policy",
        should_escalate,
        {
            True: END,  # Escalate to human
            False: "validate_output"
        }
    )
    
    workflow.add_edge("validate_output", END)
    
    return workflow.compile()

Include error handling at each node.
Add logging for debugging.
Implement should_escalate function.
"""
```

**Step 5.2**: Create main entry point
```python
# Prompt for VS Code AI Agent:
"""
Create main.py as the application entry point:

import asyncio
from src.workflow.langgraph_flow import create_support_workflow
from src.schemas.output_schema import SupportAgentOutput

async def process_ticket(
    ticket_id: str,
    message: str,
    customer_email: str | None = None
) -> SupportAgentOutput:
    '''
    Process a single support ticket through the workflow.
    '''
    workflow = create_support_workflow()
    
    initial_state = {
        "ticket_id": ticket_id,
        "original_message": message,
        "customer_email": customer_email,
        "errors": []
    }
    
    result = await workflow.ainvoke(initial_state)
    
    # Convert to Pydantic model
    output = SupportAgentOutput(**result["final_output"])
    
    return output

if __name__ == "__main__":
    # Example usage
    ticket = '''
    From: john.doe@example.com
    Subject: Charged twice for December subscription!
    
    Hi, I just noticed I was charged $49.99 TWICE on December 5th 
    for my subscription. This is ridiculous! I want a refund immediately. 
    My transaction ID is TXN-12345678.
    '''
    
    result = asyncio.run(process_ticket(
        ticket_id="TKT-2025-12-09-4567",
        message=ticket,
        customer_email="john.doe@example.com"
    ))
    
    print(result.model_dump_json(indent=2))
"""
```

---

### PHASE 6: Testing & Evaluation

**Step 6.1**: Unit tests
```python
# Prompt for VS Code AI Agent:
"""
Create tests/test_agents/test_intent_detector.py with pytest tests:

Test cases:
1. Billing issue detection
2. Technical problem detection
3. Sentiment analysis (frustrated/neutral/satisfied)
4. Edge case: multiple issues in one message
5. Edge case: vague/unclear message

Use pytest fixtures for mock LLM responses.
Test error handling for API failures.
"""
```

**Step 6.2**: Integration tests
```python
# Prompt for VS Code AI Agent:
"""
Create tests/test_integration/test_end_to_end.py:

Test complete workflow with sample tickets:
1. Billing - duplicate charge (frustrated customer)
2. Technical - login issue (neutral customer)
3. Account - upgrade request (satisfied customer)
4. Feature request (neutral customer)

Assert:
- Correct category classification
- Appropriate priority assignment
- Valid citations in response
- Policy compliance passed
- JSON schema validation passed

Use real sample tickets from data/examples/sample_tickets.json.
"""
```

**Step 6.3**: Evaluation metrics
```python
# Prompt for VS Code AI Agent:
"""
Create src/utils/metrics.py with evaluation functions:

def calculate_triage_accuracy(
    predictions: List[dict],
    ground_truth: List[dict]
) -> dict:
    '''
    Calculate classification metrics:
    - Accuracy
    - Precision, Recall, F1 per category
    - Confusion matrix
    '''

def calculate_citation_precision(
    generated_citations: List[str],
    relevant_docs: List[str]
) -> float:
    '''
    Calculate what % of citations are relevant.
    '''

def measure_response_time(start_time: float, end_time: float) -> float:
    '''
    Track average time to generate draft.
    Target: < 10 seconds.
    '''

Use scikit-learn for classification metrics.
"""
```

---

### PHASE 7: Production Readiness

**Step 7.1**: Logging & monitoring
```python
# Prompt for VS Code AI Agent:
"""
Create src/utils/logger.py with structured logging:

- Log all workflow steps with timing
- Log LLM token usage
- Log policy violations
- Log errors with full context
- Export logs to JSON for analysis

Use Python's logging module with custom formatters.
Include log rotation for production.
"""
```

**Step 7.2**: API wrapper (optional)
```python
# Prompt for VS Code AI Agent:
"""
Create api/server.py with FastAPI endpoints:

POST /api/v1/triage
- Input: ticket data
- Output: SupportAgentOutput JSON

GET /api/v1/health
- Health check endpoint

POST /api/v1/feedback
- Accept human feedback on draft quality

Include rate limiting, authentication, CORS.
Add OpenAPI documentation.
"""
```

---

## 📊 SUCCESS METRICS

Track these KPIs after deployment:

| Metric | Baseline | Target | Measurement Method |
|--------|----------|--------|-------------------|
| **Triage Accuracy** | 100% (manual) | 90%+ | Classification F1-score on test set |
| **Draft Acceptance Rate** | N/A | 70%+ | % of drafts sent with no/minor edits |
| **Response Time** | 2-4 hours | < 10 minutes | Time from ticket arrival to draft |
| **SLA Compliance** | 85% | 95%+ | % tickets resolved within SLA |
| **Citation Precision** | N/A | 95%+ | % relevant citations (human eval) |
| **Escalation Rate** | N/A | < 15% | % tickets requiring human intervention |
| **Customer Satisfaction** | Baseline CSAT | +10% | Post-resolution survey scores |

---

## 🧪 SAMPLE TEST CASE

```python
# Input ticket
ticket = {
    "id": "TKT-2025-12-09-4567",
    "from": "john.doe@example.com",
    "subject": "Charged twice for December subscription!",
    "body": """
    Hi, I just noticed I was charged $49.99 TWICE on December 5th 
    for my subscription. This is ridiculous! I want a refund immediately. 
    My transaction ID is TXN-12345678.
    """,
    "timestamp": "2025-12-09T14:32:00Z"
}

# Expected output
expected = {
    "triage": {
        "category": "Billing - Invoice Issue",
        "subcategory": "Duplicate Charge",
        "priority": "P2",
        "sla_hours": 24,
        "suggested_team": "Finance Team",
        "sentiment": "frustrated",
        "confidence": 0.85+
    },
    "answer_draft": {
        "tone": "empathetic_professional",
        "body_contains": [
            "duplicate charge",
            "understand this can be frustrating",
            "3-5 business days",
            "Finance Team"
        ],
        "citations_count": 2-4
    },
    "policy_check": {
        "refund_promise": False,  # Should NOT promise immediate refund
        "sla_mentioned": True,
        "escalation_needed": False,
        "compliance": "passe