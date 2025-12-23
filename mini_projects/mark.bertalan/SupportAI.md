**Projekt név:** SupportAI  
**Alcím:** Ügyfélszolgálati Triage és Válaszoló Agent Tudásbázissal

### Koncepció

Egy AI agent, amely:
- ✅ **Kategorizál** (triage): melyik osztály, kategória, sürgősség
- ✅ **Prioritást ad** (SLA javaslat: P1/P2, 4h/24h)
- ✅ **Választ generál** citációkkal FAQ/KB cikkekből (RAG)
- ✅ **Strukturált JSON output** validációval

### Üzleti Célok

| Cél | Megvalósítás | Mért Eredmény |
|-----|--------------|---------------|
| **Csökkenteni az ügyfélszolgálat terhelését** | Kevesebb kézi triage, draft válaszok | -40% manual triage idő |
| **Gyorsítani a válaszidőt** | Másodperces kategorizálás + draft | SLA compliance: 85% → 95% |
| **Egységesíteni a kommunikációt** | Policy-based válaszok, hangnem ellenőrzés | -60% customer complaint |
| **Tehermentesíteni senior supportosokat** | Egyszerű kérdések AI-hoz, komplex emberhez | +50% senior capacity |

### A Termék Működése

**Input:** Bejövő üzenet (ticket/email/chat)

**Workflow:**

```
1. Intent Detection
   ├─ Probléma típus: billing / technical / account / feature request
   └─ Sentiment: frustrated / neutral / satisfied

2. Triage Classification
   ├─ Kategória: "Billing - Invoice issue"
   ├─ Prioritás: P2 (Medium)
   ├─ SLA: 24 hours
   └─ Javasolt osztály: Finance Team

3. RAG Knowledge Retrieval
   ├─ Query expansion
   ├─ Vector search (top-k = 10)
   ├─ Re-ranking (top-3)
   └─ Retrieved documents: [KB-1234, KB-5678, FAQ-910]

4. Answer Draft Generation
   ├─ Template selection (based on category)
   ├─ Citációk beépítése
   ├─ Policy check (SLA, promises, refund limits)
   └─ Draft: "Dear customer, regarding your invoice issue... [KB-1234]"

5. Validation & Output
   ├─ JSON schema validation
   ├─ Citation format check
   └─ Output: Triage + Draft + Citations
```

### Output Példa

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

### LangGraph Workflow

```
┌─────────────────┐
│  Ticket Input   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Intent Detection│  (LLM - category + sentiment)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Triage Node     │  (LLM - priority + SLA)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Query Expansion │  (LLM - search queries)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Vector Search   │  (Embeddings + Retrieval)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Re-ranking    │  (Cross-encoder / LLM)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Draft Generator │  (LLM + Template)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Policy Check   │  (Guardrails)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  JSON Output    │  (Structured + Citations)
└─────────────────┘
```

### Technikai Stack

**Backend:**
- Python 3.11+
- LangChain + LangGraph
- Vector DB: Pinecone / Weaviate / Qdrant
- Embeddings: OpenAI text-embedding-3-large
- LLM: GPT-4 / Claude 3.5 Sonnet
- Re-ranker: Cohere Rerank / LLM-based

**Frontend (opcionális):**
- React dashboard (triage review)
- Real-time draft preview
- Citation highlight

**Integrations:**
- Email (IMAP/SMTP)
- Zendesk / Freshdesk API
- Slack / Teams webhook
- Jira Service Desk

### Mérési Metrikák

| Metrika | Baseline | Target | Mérés |
|---------|----------|--------|-------|
| **Triage Accuracy** | Manual (100%) | 90%+ | Classification F1-score |
| **Draft Acceptance Rate** | N/A | 70%+ | % of drafts sent as-is or with minor edits |
| **Response Time** | 2-4 hours | < 10 minutes | Time to first draft |
| **SLA Compliance** | 85% | 95%+ | % tickets resolved within SLA |
| **Citation Precision** | N/A | 95%+ | % citations relevant to answer |

---