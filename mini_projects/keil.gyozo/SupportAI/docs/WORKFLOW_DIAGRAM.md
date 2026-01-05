# SupportAI - Visual Workflow Diagram

## Complete Ticket Processing Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          INCOMING TICKET                                 │
│                                                                          │
│  {                                                                       │
│    "ticket_id": "TKT-001",                                              │
│    "raw_message": "I was charged twice for my subscription",           │
│    "customer_name": "John Doe",                                         │
│    "customer_email": "john@example.com"                                 │
│  }                                                                       │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                     NODE 1: detect_intent                                │
│                                                                          │
│  Input:  raw_message, customer_name                                     │
│  LLM:    GPT-4 (temp=0)                                                 │
│  Output: problem_type, sentiment                                        │
│                                                                          │
│  ┌────────────────────────────────────────────────────────┐            │
│  │ Analyze message → Classify problem → Detect emotion    │            │
│  │                                                         │            │
│  │ Result:                                                 │            │
│  │   problem_type: "billing"                               │            │
│  │   sentiment: "frustrated"                               │            │
│  └────────────────────────────────────────────────────────┘            │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                   NODE 2: triage_classify                                │
│                                                                          │
│  Input:  problem_type, sentiment, raw_message                           │
│  LLM:    GPT-4 (temp=0)                                                 │
│  Output: category, priority, sla_hours, suggested_team                  │
│                                                                          │
│  ┌────────────────────────────────────────────────────────┐            │
│  │ Apply priority rules → Boost if frustrated             │            │
│  │                                                         │            │
│  │ Result:                                                 │            │
│  │   category: "Billing"                                   │            │
│  │   subcategory: "Duplicate Charge"                       │            │
│  │   priority: "P2"                                        │            │
│  │   sla_hours: 24                                         │            │
│  │   suggested_team: "Finance Team"                        │            │
│  │   confidence: 0.92                                      │            │
│  └────────────────────────────────────────────────────────┘            │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                   NODE 3: expand_queries                                 │
│                                                                          │
│  Input:  raw_message, category                                          │
│  LLM:    GPT-4 (temp=0.3) - slightly creative                           │
│  Output: search_queries (2-5 variations)                                │
│                                                                          │
│  ┌────────────────────────────────────────────────────────┐            │
│  │ Rephrase → Add keywords → Create variations            │            │
│  │                                                         │            │
│  │ Queries:                                                │            │
│  │   1. "duplicate subscription charge resolution"        │            │
│  │   2. "how to handle double billing"                    │            │
│  │   3. "refund process for duplicate payment"            │            │
│  │   4. "subscription billing error troubleshooting"      │            │
│  └────────────────────────────────────────────────────────┘            │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                     NODE 4: search_rag                                   │
│                                                                          │
│  Input:  search_queries, category                                       │
│  Process: For each query → Embed → Search Qdrant → Deduplicate          │
│  Output: retrieved_docs (top-10)                                        │
│                                                                          │
│  ┌────────────────────────────────────────────────────────┐            │
│  │ Query 1 → [0.1, 0.3, ..., 0.5] → Qdrant → 10 docs     │            │
│  │ Query 2 → [0.2, 0.1, ..., 0.4] → Qdrant → 10 docs     │            │
│  │ Query 3 → [0.3, 0.2, ..., 0.6] → Qdrant → 10 docs     │            │
│  │ Query 4 → [0.1, 0.4, ..., 0.3] → Qdrant → 10 docs     │            │
│  │                                                         │            │
│  │ Deduplicate by chunk_id → Keep highest scores          │            │
│  │                                                         │            │
│  │ Retrieved:                                              │            │
│  │   1. KB-1001 "Duplicate Charges" (score: 0.89)         │            │
│  │   2. FAQ-2001 "Refund Timeframes" (score: 0.85)        │            │
│  │   3. KB-3001 "Cancellation Policy" (score: 0.78)       │            │
│  │   ... (up to 10 documents)                             │            │
│  └────────────────────────────────────────────────────────┘            │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    NODE 5: rerank_docs                                   │
│                                                                          │
│  Input:  retrieved_docs, raw_message                                    │
│  LLM:    GPT-4 (temp=0) - per document                                  │
│  Output: reranked_docs (top-3)                                          │
│                                                                          │
│  ┌────────────────────────────────────────────────────────┐            │
│  │ For each doc: LLM scores relevance 0-1                 │            │
│  │                                                         │            │
│  │ Doc 1: vector=0.89, llm=0.95 → final=0.92             │            │
│  │ Doc 2: vector=0.85, llm=0.88 → final=0.87             │            │
│  │ Doc 3: vector=0.78, llm=0.92 → final=0.85             │            │
│  │                                                         │            │
│  │ Sort by final score → Return top 3                     │            │
│  │                                                         │            │
│  │ Reranked:                                               │            │
│  │   1. KB-1001 "Duplicate Charges" (final: 0.92)         │            │
│  │   2. FAQ-2001 "Refund Timeframes" (final: 0.87)        │            │
│  │   3. KB-3001 "Cancellation Policy" (final: 0.85)       │            │
│  └────────────────────────────────────────────────────────┘            │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    NODE 6: draft_answer                                  │
│                                                                          │
│  Input:  reranked_docs, customer_name, sentiment                        │
│  LLM:    GPT-4 (temp=0.3) - natural language                            │
│  Output: answer_draft, citations                                        │
│                                                                          │
│  ┌────────────────────────────────────────────────────────┐            │
│  │ Context from top 3 docs → Generate response            │            │
│  │ Adjust tone based on sentiment                         │            │
│  │ Add inline citations [DOC-ID]                          │            │
│  │                                                         │            │
│  │ Draft:                                                  │            │
│  │   greeting: "Hi John,"                                 │            │
│  │   body: "I understand your concern about being         │            │
│  │          charged twice. Duplicate charges are          │            │
│  │          typically resolved within 3-5 business        │            │
│  │          days [KB-1001]. We'll investigate and         │            │
│  │          process a refund to your original payment     │            │
│  │          method [FAQ-2001]..."                         │            │
│  │   closing: "Best regards,\nSupport Team"               │            │
│  │   tone: "empathetic_professional"                      │            │
│  │                                                         │            │
│  │ Citations: [KB-1001, FAQ-2001]                         │            │
│  └────────────────────────────────────────────────────────┘            │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                   NODE 7: check_policy                                   │
│                  ⚠️ NODE NAME ≠ STATE FIELD NAME                        │
│                                                                          │
│  Input:  answer_draft                                                   │
│  LLM:    GPT-4 (temp=0)                                                 │
│  Output: policy_check                                                   │
│                                                                          │
│  ┌────────────────────────────────────────────────────────┐            │
│  │ Scan for:                                               │            │
│  │   ❌ Unauthorized refund promises                       │            │
│  │   ❌ Specific SLA commitments                           │            │
│  │   ❌ Policy exceptions                                  │            │
│  │   ✅ P1 tickets need escalation                         │            │
│  │                                                         │            │
│  │ Result:                                                 │            │
│  │   refund_promise: false                                 │            │
│  │   sla_mentioned: true                                   │            │
│  │   escalation_needed: false                              │            │
│  │   compliance: "passed"                                  │            │
│  │   issues: []                                            │            │
│  └────────────────────────────────────────────────────────┘            │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                   NODE 8: validate_output                                │
│                                                                          │
│  Input:  Complete state from all nodes                                  │
│  Process: Build Pydantic models → Validate → Add metadata               │
│  Output: Structured JSON (TicketOutput)                                 │
│                                                                          │
│  ┌────────────────────────────────────────────────────────┐            │
│  │ Collect all fields → Pydantic validation               │            │
│  │                                                         │            │
│  │ Final Output:                                           │            │
│  │ {                                                       │            │
│  │   "ticket_id": "TKT-001",                               │            │
│  │   "timestamp": "2025-01-23T10:30:00+00:00",             │            │
│  │   "triage": {                                           │            │
│  │     "category": "Billing",                              │            │
│  │     "priority": "P2",                                   │            │
│  │     "sla_hours": 24,                                    │            │
│  │     ...                                                 │            │
│  │   },                                                    │            │
│  │   "answer_draft": { ... },                             │            │
│  │   "citations": [ ... ],                                │            │
│  │   "policy_check": { ... }                              │            │
│  │ }                                                       │            │
│  └────────────────────────────────────────────────────────┘            │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                          API RESPONSE                                    │
│                                                                          │
│  HTTP 200 OK                                                            │
│  {                                                                       │
│    "success": true,                                                     │
│    "ticket_id": "TKT-001",                                              │
│    "result": { ... complete output ... }                               │
│  }                                                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

## State Evolution Through Workflow

```
START
│
├─ ticket_id: "TKT-001"
├─ raw_message: "I was charged twice..."
├─ customer_name: "John Doe"
└─ customer_email: "john@example.com"

↓ detect_intent

├─ problem_type: "billing"
└─ sentiment: "frustrated"

↓ triage_classify

├─ category: "Billing"
├─ subcategory: "Duplicate Charge"
├─ priority: "P2"
├─ sla_hours: 24
├─ suggested_team: "Finance Team"
└─ triage_confidence: 0.92

↓ expand_queries

└─ search_queries: ["duplicate charge...", "double billing...", ...]

↓ search_rag

└─ retrieved_docs: [KB-1001, FAQ-2001, KB-3001, ...] (10 docs)

↓ rerank_docs

└─ reranked_docs: [KB-1001, FAQ-2001, KB-3001] (3 docs)

↓ draft_answer

├─ answer_draft: {greeting, body, closing, tone}
└─ citations: [KB-1001, FAQ-2001]

↓ check_policy

└─ policy_check: {compliance: "passed", ...}

↓ validate_output

└─ output: {complete TicketOutput JSON}

END
```

## Service Dependencies

```
┌────────────────────────────────────────────────────┐
│              LangGraph Workflow                    │
└───────┬──────────────────┬─────────────────┬───────┘
        │                  │                 │
        ↓                  ↓                 ↓
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   OpenAI     │   │   Qdrant     │   │    Redis     │
│   API        │   │   Vector DB  │   │   Cache      │
│              │   │              │   │              │
│  - GPT-4     │   │  - Search    │   │  - Embeddings│
│  - Embeddings│   │  - Upsert    │   │  - Results   │
└──────────────┘   └──────────────┘   └──────────────┘
```

## Error Handling Flow

```
Node Execution
      │
      ↓
  ┌───────┐
  │ Try:  │
  │ Execute│────→ Success ──→ Return state update
  └───────┘
      │
  Exception
      │
      ↓
  ┌───────┐
  │ Catch:│
  │ Log   │────→ Return fallback values + errors field
  └───────┘
      │
      ↓
  Continue workflow (graceful degradation)
```

## Metrics Collection Points

```
Request Start
     │
     ├─→ Counter: tickets_received
     │
  Workflow Start
     │
     ├─→ Timer: ticket_processing_START
     │
  Each Node
     │
     ├─→ Counter: node_{name}_executions
     ├─→ Timer: node_{name}_duration
     │
  Workflow End
     │
     ├─→ Timer: ticket_processing_END
     ├─→ Counter: tickets_processed
     ├─→ Counter: priority_{P1|P2|P3}
     ├─→ Counter: category_{category}
     ├─→ Counter: compliance_{status}
     │
Response Sent
```

## Priority Decision Tree

```
                    Problem Type + Sentiment
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
    Billing            Technical            Account
        │                   │                   │
        ↓                   ↓                   ↓
  ┌──────────┐       ┌──────────┐       ┌──────────┐
  │Frustrated│       │ Outage?  │       │Can't     │
  │   ?      │       │          │       │login?    │
  └──────────┘       └──────────┘       └──────────┘
   Yes │ No           Yes │ No           Yes │ No
       ↓                  ↓                  ↓
      P2                 P1                 P2
      24h                4h                 24h
       │                  │                  │
       ↓                  ↓                  ↓
  Finance Team      Engineering      Account Mgmt
```

## Citation Flow

```
Retrieved Docs (10)
      │
      ├─ KB-1001: "Duplicate charges..." (0.89)
      ├─ FAQ-2001: "Refund timeframes..." (0.85)
      ├─ KB-3001: "Cancellation..." (0.78)
      └─ ...
      │
      ↓ Re-ranking (LLM scoring)
      │
Reranked Docs (3)
      │
      ├─ KB-1001 (final: 0.92)
      ├─ FAQ-2001 (final: 0.87)
      └─ KB-3001 (final: 0.85)
      │
      ↓ Draft Answer (LLM generation)
      │
Response Body
      │
      "...within 3-5 days [KB-1001]..."
      "...refund process [FAQ-2001]..."
      │
      ↓ Extract Citations
      │
Citations Array
      │
      ├─ {doc_id: "KB-1001", score: 0.92, url: "..."}
      └─ {doc_id: "FAQ-2001", score: 0.87, url: "..."}
```

## Complete Data Flow (JSON)

```json
INPUT → {
  "ticket_id": "TKT-001",
  "raw_message": "I was charged twice",
  "customer_name": "John Doe",
  "customer_email": "john@example.com"
}

OUTPUT → {
  "ticket_id": "TKT-001",
  "timestamp": "2025-01-23T10:30:00+00:00",
  "triage": {
    "category": "Billing",
    "subcategory": "Duplicate Charge",
    "priority": "P2",
    "sla_hours": 24,
    "suggested_team": "Finance Team",
    "sentiment": "frustrated",
    "confidence": 0.92
  },
  "answer_draft": {
    "greeting": "Hi John,",
    "body": "I understand your concern... [KB-1001]...",
    "closing": "Best regards,\\nSupport Team",
    "tone": "empathetic_professional"
  },
  "citations": [
    {
      "doc_id": "KB-1001",
      "chunk_id": "KB-1001-c-1",
      "title": "How to Handle Duplicate Charges",
      "score": 0.92,
      "url": "https://kb.company.com/billing/duplicate-charges"
    }
  ],
  "policy_check": {
    "refund_promise": false,
    "sla_mentioned": true,
    "escalation_needed": false,
    "compliance": "passed",
    "issues": []
  }
}
```

This diagram shows the complete flow from input to output, including all state transformations, service interactions, and decision points.
