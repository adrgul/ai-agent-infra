# AI Agent Projekt Ötletek - Magyar Dokumentáció

Ez a dokumentum három komplex AI agent projekt ötletet mutat be, amelyek LangGraph-alapú megvalósításra alkalmasak.

---

## Tartalomjegyzék
1. [AI Meeting Assistant](#1-ai-meeting-assistant)
2. [AI Support Triage & Answer Drafting Agent](#2-ai-support-triage--answer-drafting-agent)
3. [AI Internal Knowledge Router & Workflow Automation Agent](#3-ai-internal-knowledge-router--workflow-automation-agent)
4. [Technikai Összehasonlítás](#technikai-összehasonlítás)
5. [Implementációs Útmutató](#implementációs-útmutató)

---

## 1. AI Meeting Assistant

**Projekt név:** MeetingAI  
**Alcím:** Jegyző + Feladatkiosztó + Összegző Agent

### Koncepció

Egy AI agent, ami meeting jegyzetből vagy transcript-ből automatikusan:
- ✅ **Összefoglalót készít** (executive summary)
- ✅ **Akciópontokat gyűjt ki** (to-do lista tulajdonosokkal)
- ✅ **Elmenti** JSON formátumban vagy Jira API-n keresztül

### Előnyök

| Szempont | Részletek |
|----------|-----------|
| **Egyszerű indulás** | Sima TXT vagy transcript feldolgozása, nincs szükség külső API-kra |
| **LangGraph példák** | Document input → LLM summarization → JSON output |
| **Bővíthetőség** | Memóriával (korábbi meetingek), feladatrögzítéssel, Slack/Teams integrációval |
| **Üzleti érték** | Időmegtakarítás, egységes dokumentáció, követhetőség |

### Végeredmény Output-ok

**1. Meeting Summary (Összefoglaló)**
```json
{
  "meeting_id": "MTG-2025-12-09-001",
  "title": "Q4 Sprint Planning",
  "date": "2025-12-09",
  "participants": ["János", "Péter", "Maria"],
  "summary": "A csapat megvitatta a Q4 sprintek prioritásait. Megállapodtak a login feature véglegesítésében és a teljesítmény-optimalizálásban.",
  "key_decisions": [
    "Login feature lesz a P1 prioritás",
    "Performance audit Q4 végéig"
  ],
  "next_steps": [
    "UI mockup review - János - Dec 12",
    "Backend API setup - Péter - Dec 15"
  ]
}
```

**2. Task List (Feladatlista)**
```json
{
  "tasks": [
    {
      "task_id": "TASK-001",
      "title": "UI mockup review készítése",
      "assignee": "János",
      "due_date": "2025-12-12",
      "priority": "P1",
      "status": "to-do",
      "meeting_reference": "MTG-2025-12-09-001"
    },
    {
      "task_id": "TASK-002",
      "title": "Backend API setup - login endpoint",
      "assignee": "Péter",
      "due_date": "2025-12-15",
      "priority": "P1",
      "status": "to-do",
      "meeting_reference": "MTG-2025-12-09-001"
    }
  ]
}
```

**3. Jira Integration (Opcionális)**
- Automatikus ticket létrehozás Jira API-n keresztül
- Assignee beállítása
- Priority és due date szinkronizálás

### LangGraph Workflow

```
┌─────────────────┐
│  Document Input │  (TXT/Transcript)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Parse & Split │  (Chunking)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Summarize Node │  (LLM - executive summary)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Extract Actions │  (LLM - to-do extraction)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Structure JSON │  (Validation + Schema)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Save Output   │  (JSON file / Jira API)
└─────────────────┘
```

### Technikai Stack

**Backend:**
- Python 3.11+
- LangChain + LangGraph
- OpenAI GPT-4 / Claude
- Jira Python SDK (opcionális)
- Pydantic (JSON schema validation)

**Input formátumok:**
- Plain TXT
- Markdown
- SRT (subtitle format)
- DOCX

**Output formátumok:**
- JSON
- Markdown report
- Jira tickets (API)
- Slack/Teams message (webhook)

### Bővítési Lehetőségek

1. **Memory Integration**
   - Korábbi meetingek context-je
   - Résztvevők profiljai
   - Projekt history

2. **Slack/Teams Bot**
   - Meeting után automatikus összefoglaló post
   - Task assignee-k értesítése
   - Follow-up reminder 24h előtt

3. **Voice Transcript Integration**
   - Google Meet / Zoom transcript import
   - Speaker diarization (ki mit mondott)
   - Sentiment analysis

---

## 2. AI Support Triage & Answer Drafting Agent

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

## 3. AI Internal Knowledge Router & Workflow Automation Agent

**Projekt név:** KnowledgeRouter  
**Alcím:** Vállalati Belső Tudásirányító + Workflow-Automata Agent

### Koncepció

Egy agent, amely képes:
1. ✅ **Felismerni a kérés típusát** (FAQ, HR, IT, pénzügy, jog, marketing)
2. ✅ **Kiválasztani a megfelelő tudásbázist** (multi-vector store routing)
3. ✅ **Kikeresni releváns információt** RAG-gal
4. ✅ **Végrehajtani workflow lépést** (Jira ticket, Slack üzenet, approval, file generation)
5. ✅ **Strukturált választ adni** citációkkal

### Vállalati Probléma

**Fájdalom pontok:**
- 📁 10+ tudásbázis van szétszórva (Confluence, PDF-ek, HR fájlok, GitHub wiki, Google Docs)
- 🔀 20+ workflow típus (IT ticket, HR request, szabadság, eszközigénylés, szerződés)
- ❓ Senki nem tudja, „mi hol van"
- ⏱️ Órák mennek el információkeresésre

**Megoldás:** Agent, amely tudja, „hova kell nyúlni"

### Technikai Architektúra

**Multi-Vector Store:**
```python
vector_stores = {
    "hr": PineconeVectorStore(namespace="hr_kb"),
    "it": PineconeVectorStore(namespace="it_kb"),
    "finance": PineconeVectorStore(namespace="finance_kb"),
    "legal": PineconeVectorStore(namespace="legal_kb"),
    "marketing": PineconeVectorStore(namespace="marketing_kb"),
    "general": PineconeVectorStore(namespace="general_kb")
}
```

**Routing Logic:**
```python
async def route_domain(query: str) -> str:
    """LLM-based intent classification."""
    prompt = f"""
    Classify the following query into one domain:
    - hr (human resources, vacation, benefits, hiring)
    - it (tech support, VPN, access, software)
    - finance (invoices, expenses, budgets)
    - legal (contracts, compliance, policies)
    - marketing (brand, campaigns, content)
    - general (other)
    
    Query: {query}
    
    Return ONLY the domain name.
    """
    
    response = await llm.ainvoke(prompt)
    return response.content.strip().lower()
```

### Workflow Node-ok

**1. HR Workflow Node**
```python
async def hr_workflow_node(state: AgentState) -> AgentState:
    """HR-specifikus workflow végrehajtás."""
    
    if "szabadság" in state["query"].lower():
        # Generate HR request JSON
        hr_request = {
            "type": "vacation_request",
            "employee_id": state["user_id"],
            "start_date": extract_date(state["query"], "start"),
            "end_date": extract_date(state["query"], "end"),
            "status": "pending_approval"
        }
        
        # Save to file
        filename = f"hr_request_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_json(hr_request, filename)
        
        state["workflow_output"] = {
            "action": "hr_request_created",
            "file": filename,
            "next_step": "Manager approval required"
        }
    
    return state
```

**2. IT Workflow Node**
```python
async def it_workflow_node(state: AgentState) -> AgentState:
    """IT-specifikus workflow végrehajtás."""
    
    if "nem működik" in state["query"].lower():
        # Create Jira ticket draft
        ticket = {
            "project": "ITSUPPORT",
            "issue_type": "Bug",
            "summary": extract_issue_summary(state["query"]),
            "description": state["query"],
            "priority": determine_priority(state["query"]),
            "assignee": "it-team"
        }
        
        state["workflow_output"] = {
            "action": "it_ticket_draft",
            "ticket": ticket,
            "next_step": "Review and submit to Jira"
        }
    
    return state
```

### LangGraph Multi-Branch Workflow

```
┌─────────────────┐
│   User Query    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Intent Detection│  (LLM - domain routing)
└────────┬────────┘
         │
    ┌────┴────┐
    │ Router  │
    └────┬────┘
         │
         ├─────────┬─────────┬─────────┬─────────┬─────────┐
         │         │         │         │         │         │
         ▼         ▼         ▼         ▼         ▼         ▼
     ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
     │  HR   │ │  IT   │ │Finance│ │ Legal │ │Market │ │General│
     │ RAG   │ │ RAG   │ │ RAG   │ │ RAG   │ │ RAG   │ │ RAG   │
     └───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘
         │         │         │         │         │         │
         ├─────────┴─────────┴─────────┴─────────┴─────────┤
         │                                                   │
         ▼                                                   ▼
     ┌───────────┐                                   ┌───────────┐
     │ Workflow  │                                   │   Draft   │
     │ Execution │                                   │  Answer   │
     └─────┬─────┘                                   └─────┬─────┘
           │                                               │
           └───────────────────┬───────────────────────────┘
                               │
                               ▼
                        ┌─────────────┐
                        │ Final Output│
                        └─────────────┘
```

### Demo Példák

**1. HR Szabadság Igénylés**

**Input:**
```
"Szeretnék szabadságot igényelni október 3–4-re."
```

**Workflow:**
```
1. Intent Detection → "hr" domain
2. HR Vector Store → vacation policy documents
3. RAG Retrieval → "Szabadságkérés minimum 2 héttel előre"
4. HR Workflow Node → Generate hr_request_2025-10-03.json
5. Output:
   {
     "domain": "hr",
     "answer": "Szabadságkérelmed rögzítésre került október 3-4 időszakra. 
                A policy szerint minimum 2 héttel előre kell jelezni. [HR-POL-001]
                Kérlek, add meg a vezetőd jóváhagyását.",
     "citations": [
       {"doc_id": "HR-POL-001", "title": "Vacation Policy", "score": 0.94}
     ],
     "workflow": {
       "action": "hr_request_created",
       "file": "hr_request_2025-10-03.json",
       "status": "pending_approval"
     }
   }
```

**2. Marketing Brand Guideline**

**Input:**
```
"Hol van a legfrissebb marketing brand guideline?"
```

**Workflow:**
```
1. Intent Detection → "marketing" domain
2. Marketing Vector Store → brand docs
3. RAG Retrieval → "Brand Guidelines v3.2 - Dec 2025"
4. Output:
   {
     "domain": "marketing",
     "answer": "A legfrissebb brand guideline a v3.2 verzió, 
                amely 2025 decemberében lett frissítve. [BRAND-v3.2]
                Link: https://drive.google.com/marketing/brand-v3.2.pdf",
     "citations": [
       {"doc_id": "BRAND-v3.2", "title": "Brand Guidelines v3.2", "score": 0.97, 
        "url": "https://drive.google.com/marketing/brand-v3.2.pdf"}
     ],
     "workflow": null
   }
```

**3. IT VPN Issue**

**Input:**
```
"Nem működik a VPN"
```

**Workflow:**
```
1. Intent Detection → "it" domain
2. IT Vector Store → VPN troubleshooting docs
3. RAG Retrieval → top-3 VPN solutions
4. IT Workflow Node → Create Jira ticket draft
5. Output:
   {
     "domain": "it",
     "answer": "VPN kapcsolódási problémák gyakori okai: [IT-KB-234]
                1. Ellenőrizd, hogy az IT VPN kliens fut-e
                2. Próbáld újraindítani a VPN szolgáltatást
                3. Ellenőrizd a hálózati kapcsolatot
                
                Ha ezek nem segítenek, IT ticket került létrehozásra. [IT-TKT-DRAFT]",
     "citations": [
       {"doc_id": "IT-KB-234", "title": "VPN Troubleshooting Guide", "score": 0.91},
       {"doc_id": "IT-KB-189", "title": "VPN Client Installation", "score": 0.87}
     ],
     "workflow": {
       "action": "it_ticket_draft",
       "ticket": {
         "project": "ITSUPPORT",
         "summary": "VPN connection failure",
         "priority": "P2",
         "description": "User reports VPN not working"
       },
       "next_step": "Submit to Jira or contact IT support"
     }
   }
```

### Technikai Stack

**Backend:**
- Python 3.11+
- LangChain + LangGraph
- Multi-Vector Store: Pinecone (namespaces) vagy Weaviate (tenants)
- Embeddings: OpenAI text-embedding-3-large
- LLM: GPT-4o / Claude 3.5 Sonnet
- Workflow Tools: Jira SDK, Slack SDK, Google Drive API

**Domain Coverage:**
```python
domains = {
    "hr": ["vacation", "benefits", "hiring", "payroll", "onboarding"],
    "it": ["vpn", "access", "software", "hardware", "network"],
    "finance": ["invoice", "expense", "budget", "payment", "tax"],
    "legal": ["contract", "compliance", "policy", "gdpr", "ip"],
    "marketing": ["brand", "campaign", "content", "social", "analytics"],
    "general": ["other", "faq", "general-info"]
}
```

### AI Skills Demonstrated

| Skill | Implementáció |
|-------|---------------|
| **RAG (multi-dataset)** | 6 külön vector store, domain-specifikus embeddings |
| **LangGraph (multi-branch)** | Conditional routing 6 domain-re |
| **Memory** | Context tracking user sessionök között |
| **Tool calling** | Jira API, Slack API, file generation |
| **Reasoning** | Intent classification + domain routing |
| **JSON output** | Structured response + citations |
| **Policy check** | Guardrails (approval needed, SLA, compliance) |
| **Prompt engineering** | Domain-specific prompts + few-shot examples |

### Compliance & Security

**AI Act Compliance:**
- ✅ **Citációk:** Minden válasz tartalmazza a forrás dokumentum ID-ját
- ✅ **Traceability:** Logging minden döntésről (domain routing, retrieval scores)
- ✅ **Human-in-the-loop:** Workflow approval-ok emberi jóváhagyással
- ✅ **Audit log:** Teljes conversation history mentése

**Security:**
- 🔒 **Role-based access:** User csak a saját domain-jéhez fér hozzá
- 🔒 **Data encryption:** Vector store titkosítva
- 🔒 **PII masking:** Érzékeny adatok (személyes info) maszkolása

---

## Technikai Összehasonlítás

| Szempont | Meeting Assistant | Support Triage | Knowledge Router |
|----------|-------------------|----------------|------------------|
| **Komplexitás** | ⭐⭐ (Közepes) | ⭐⭐⭐ (Magas) | ⭐⭐⭐⭐ (Nagyon magas) |
| **RAG szükséges?** | ❌ Nem | ✅ Igen (1 KB) | ✅ Igen (multi-KB) |
| **Vector DB** | ❌ Nincs | ✅ 1 namespace | ✅ 6+ namespace |
| **LangGraph node-ok** | 5-6 | 7-8 | 10+ |
| **Workflow integration** | Jira API | Zendesk/Email | Jira + Slack + Drive |
| **Output típusok** | JSON + Markdown | JSON + Citations | JSON + Citations + Files |
| **Mérhetőség** | Summary quality | Triage accuracy + Draft acceptance | Intent routing + RAG precision |
| **Üzleti érték** | Időmegtakarítás | SLA javítás | Tudásmenedzsment + Automation |
| **Demo egyszerűsége** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Production readiness** | 2-3 hét | 4-6 hét | 8-12 hét |

---

## Implementációs Útmutató

### Közös Technikai Stack (mind a 3 projektre)

```python
# requirements.txt
langchain>=0.1.0
langgraph>=0.0.20
langchain-openai>=0.0.5
pydantic>=2.5.0
fastapi>=0.108.0
uvicorn>=0.25.0

# Vector DB (válaszd ki egyet)
pinecone-client>=3.0.0      # Managed cloud
weaviate-client>=4.4.0      # Self-hosted vagy cloud
qdrant-client>=1.7.0        # Self-hosted

# Integrations (opcionális)
jira>=3.5.0
slack-sdk>=3.26.0
google-api-python-client>=2.110.0
```

### LangGraph Alapstruktúra (közös)

```python
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict

class ProjectState(TypedDict, total=False):
    """Alapstruktúra - bővítsd projektenként."""
    input: str
    domain: str
    retrieved_docs: list
    output: dict
    citations: list

def build_workflow() -> StateGraph:
    workflow = StateGraph(ProjectState)
    
    # Közös node-ok
    workflow.add_node("intent_detection", intent_detection_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("generation", generation_node)
    workflow.add_node("validation", validation_node)
    
    # Entry
    workflow.set_entry_point("intent_detection")
    
    # Edges
    workflow.add_edge("intent_detection", "retrieval")
    workflow.add_edge("retrieval", "generation")
    workflow.add_edge("generation", "validation")
    workflow.add_edge("validation", END)
    
    return workflow.compile()
```

### Projekt-specifikus Bővítések

**Meeting Assistant:**
```python
# Extra node-ok
workflow.add_node("parse_transcript", parse_transcript_node)
workflow.add_node("extract_actions", extract_actions_node)
workflow.add_node("generate_summary", generate_summary_node)
```

**Support Triage:**
```python
# Extra node-ok
workflow.add_node("triage_classify", triage_classify_node)
workflow.add_node("rag_search", rag_search_node)
workflow.add_node("rerank", rerank_node)
workflow.add_node("draft_answer", draft_answer_node)
workflow.add_node("policy_check", policy_check_node)
```

**Knowledge Router:**
```python
# Extra node-ok
workflow.add_node("domain_router", domain_router_node)
workflow.add_node("hr_rag", hr_rag_node)
workflow.add_node("it_rag", it_rag_node)
# ... további domain RAG node-ok
workflow.add_node("workflow_executor", workflow_executor_node)

# Conditional routing
workflow.add_conditional_edges(
    "domain_router",
    route_to_domain,
    {
        "hr": "hr_rag",
        "it": "it_rag",
        "finance": "finance_rag",
        # ...
    }
)
```

### Deployment

**Docker Compose:**
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
    volumes:
      - ./data:/app/data
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
```

**Production Considerations:**
- Load balancing (több backend instance)
- Redis cache (embedding cache)
- Monitoring (Prometheus + Grafana)
- Logging (ELK stack)

---

## Összefoglalás

### Melyik projektet válaszd?

| Ha ezt akarod... | Válaszd ezt |
|------------------|-------------|
| **Gyors win, demo-barát** | Meeting Assistant |
| **Mérhető ROI, üzleti érték** | Support Triage |
| **Komplex, sok AI skill** | Knowledge Router |
| **LangGraph tanulás** | Support Triage |
| **RAG practice** | Support Triage vagy Knowledge Router |
| **Multi-agent system** | Knowledge Router |

### Következő Lépések

1. **Válassz egy projektet** a fenti kritériumok alapján
2. **Készíts POC-t** (Proof of Concept) LangGraph-ban
3. **Tesztelj kis dataset-en** (10-20 példa)
4. **Mérj metrikákat** (accuracy, response time)
5. **Iterálj** prompt engineering-en és retrieval-en
6. **Bővítsd** production feature-ökkel

### Kapcsolódó Dokumentumok

- **LangGraph használat:** `docs/LANGGRAPH_USAGE_HU.md`
- **Agent loop:** `docs/AGENT_LOOP_HU.md`
- **Prompt engineering:** `docs/PROMPTS.md`
- **Architektúra:** `docs/ARCHITECTURE.md`

---

**Verzió:** 1.0  
**Utolsó frissítés:** 2025-12-09  
**Szerző:** AI Agent Documentation Team
