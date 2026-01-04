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
- ✅ **Időpontot foglal** calendar-ban API-n keresztül
- ✅ **Email-t küld** a megfelelő személynek a szükséges kéréssel, információval

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
