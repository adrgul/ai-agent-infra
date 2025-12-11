Hozz létre egy TELJES működő példaalkalmazást, amely bemutat egy AI Agent munkafolyamatot Python Django backenddel és modern Tailwind CSS frontenddel (ChatGPT-style UI).

Cél:
AI Internal Knowledge Router & Workflow Automation Agent
Projekt név: KnowledgeRouter
Alcím: Vállalati Belső Tudásirányító + Workflow-Automata Agent

Az alkalmazásnak KÖTELEZŐ:
- Dockert kell használnia a konténerizációhoz (backend + frontend, futtatható Docker-compose-on keresztül).
- LangGraph-ot kell használnia az ágens vezényléséhez (csomópontok gráfja az ágenshez, eszközökhöz stb.).
- OpenAI-t kell használnia LLM backendként (Chat Completions / függvényhívás vagy hasonló), az OPENAI_API_KEY környezeti változón keresztül biztosított API-kulccsal.
- MINDEN beszélgetési előzményt (összes üzenetet) JSON fájlokban kell tárolni a fájlrendszerben.
- Egy külön felhasználói profilt kell tárolni JSON-ban a fájlrendszeren.
- Lehetővé kell tenni a beszélgetési előzmények törlését egy speciális "reset context" felhasználói üzenettel. - Soha ne törölje a felhasználói profilt; csak létrehozható/betölthető és frissíthető, de nem törölhető.
- SOLID elvek és a lehető legnagyobb mértékben tiszta architektúra szerint kell megvalósítani egy kis példában (a problémák szétválasztása, egyértelmű absztrakciók, függőségek inverziója stb.).

---------------------------------------------------------------------------------
Magas szintű követelmények
-------------------------------------------------------------------------------------------

Háttér: Python (Django), amely egy AI ügynököt valósít meg LangGraph-pal.
Frontend: Tailwind CSS + Vanilla JavaScript, ChatGPT-szerű felhasználói felület (dark mode, gradient header, modern buttons).

Ügynök képességei:
- Felhasználói prompt + memória fogadása (csevegési előzmények összefoglalása és felhasználói profil + munkafolyamat állapota).
- Döntés arról, hogy meghívja-e az eszközöket (időjárás, geokódolás, FX, kripto, fájl létrehozása, JSON keresés).
- LangGraph eszközcsomópontok meghívása külső API-khoz és belső segédprogramokhoz.
- Memória frissítése (beszélgetés, beállítások, munkafolyamat állapota).
- Végső választ ad vissza a felhasználónak.

Projekt felépítés:
Hasonlóan a workspacen belül található ai_agent_complex és ai_agent_intro projektekhez

Megőrzés:
- Minden beszélgetési üzenetet (felhasználó + asszisztens + eszköz/rendszer üzenetek) JSON fájlokban kell tárolni a lemezen.
- Egy külön felhasználói profil JSON fájlját kell tárolni a lemezen.
- Egy speciális "kontextus visszaállítása" üzenetnek (kis- és nagybetűket nem megkülönböztető) törölnie kell az adott munkamenet/felhasználó beszélgetési előzményeit, de NEM törölheti a felhasználói profilt.

---------------------------------------------------------------------------------
Technológiák és architektúra
---------------------------------------------------------------------------------------------

Háttér:
- Nyelv: Python 3.11+
- Keretrendszer: Django + FastAPI 
- Ügynökkoordináció: LangGraph (Python könyvtár)
- A LangGraph segítségével definiálhat egy gráfot a következőkkel:
- Ügynökcsomópont(ok): LLM érvelés és döntéshozatal.
- Eszközcsomópont(ok): külső API hívások, fájllétrehozás, előzménykeresés.
- HTTP kliens: httpx (aszinkron).
- LLM integráció: OpenAI Chat Completions (vagy azzal egyenértékű) függvényhívással / JSON kimenettel.
- Használja az OPENAI_API_KEY környezeti változót.
- Adatmodellek: Pydantic modellek kérésekhez, válaszokhoz, memóriához, üzenetekhez, felhasználói profilokhoz.
- Naplózás: Python naplózó modul strukturált naplókhoz.
- ARCHITEKTÚRA ÉS SOLID:
- A backend strukturálása rétegekbe / modulokba (pl. API, szolgáltatások, domain, infrastruktúra).
- Világos interfészek / absztrakciók meghatározása:
- API lekérések  (pl. Google Drive)
- fájlalapú adattárak (beszélgetési előzmények, felhasználói profil).
- Függőségi inverzió használata, ahol lehetséges (absztrakciókra támaszkodjon, ne konkrét implementációkra).
- A vezérlők (API útvonalak) legyenek vékonyak, a logikát szolgáltatásosztályokra delegálja.
- Biztosítson egyetlen felelősséget osztályonként vagy modulonként, ahol ez praktikus.

Frontend:
- HTMX
- ChatGPT-szerű felület:
- Görgethető csevegési előzmények középen.
- Felhasználói bevitel alul.
- Az új válaszok a bemenet felett jelennek meg, hasonlóan a ChatGPT-hez.
- Opcionális hibakeresés / oldalpanel:
- Megjeleníti, hogy mely eszközöket hívták meg.
- Memória pillanatképének megjelenítése (beállítások, munkafolyamat állapota).
- Minimális naplók megjelenítése.

-------------------------------------------------------------------------------------
Felhasználói és munkamenet-modell, fájltárolási követelmények
-----------------------------------------------------------------------------------------------

Döntsen el egy egyértelmű modellt a következőkhöz:
1) Felhasználói profil
2) Beszélgetési előzmények (felhasználónként/munkamenetenként)
3) Memória objektum

Felhasználói profil:
- JSON fájlként tárolva a lemezen, pl. data/users/{user_id}.json
- Tartalmaz (minimum):
- user_id: karakterlánc
- organisation: szervezet, ahova tartozik
- esetleg egyéb beállítások (jövőbeli kiterjesztés)
- Viselkedés:
- Első kérésre, ha a profil nem létezik, hozza létre az alapértelmezett értékekkel. - Későbbi kérések esetén töltse be és engedélyezze a frissítéseket.
- A felhasználói profilt TILOS munkafolyamattal törölni; csak frissíteni.
- Biztosítson mechanizmust a beállítások frissítésére a következőkön keresztül:
- API végpont(ok) (pl. PUT /api/profile), és/vagy
- Az ügynök megérti a felhasználói utasításokat, például a „Mostantól angolul válaszoljon.”

Beszélgetési előzmények:
- JSON fájlokként tárolva a lemezen, pl. data/sessions/


---------------------------------------------------------------------------------
Koncepció
-------------------------------------------------------------------------------------------
Egy agent, amely képes:

✅ Felismerni a kérés típusát (FAQ, HR, IT, pénzügy, jog, marketing)
✅ Kiválasztani a megfelelő tudásbázist (multi-vector store routing)
✅ Kikeresni releváns információt RAG-gal
✅ Végrehajtani workflow lépést (Jira ticket, Slack üzenet, approval, file generation)
✅ Strukturált választ adni dokumentum referencia hivatkozásokkal (citációkkal)

Vállalati Probléma
Fájdalom pontok:

📁 10+ tudásbázis van szétszórva (Confluence, PDF-ek, HR fájlok, GitHub wiki, Google Docs)
🔀 20+ workflow típus (IT ticket, HR request, szabadság, eszközigénylés, szerződés)
❓ Senki nem tudja, „mi hol van"
⏱️ Órák mennek el információkeresésre
Megoldás: Agent, amely tudja, „hova kell nyúlni"

Technikai Architektúra
Multi-Vector Store:

vector_stores = {
    "hr": PineconeVectorStore(namespace="hr_kb"),
    "it": PineconeVectorStore(namespace="it_kb"),
    "finance": PineconeVectorStore(namespace="finance_kb"),
    "legal": PineconeVectorStore(namespace="legal_kb"),
    "marketing": PineconeVectorStore(namespace="marketing_kb"),
    "general": PineconeVectorStore(namespace="general_kb")
}

Routing logikák:

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

Workflow Node-ok
1. HR Workflow Node

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
2. IT Workflow Node

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
LangGraph Multi-Branch Workflow
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
Demo Példák
1. HR Szabadság Igénylés

Input:

"Szeretnék szabadságot igényelni október 3–4-re."
Workflow:

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
2. Marketing Brand Guideline

Input:

"Hol van a legfrissebb marketing brand guideline?"
Workflow:

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
3. IT VPN Issue

Input:

"Nem működik a VPN"
Workflow:

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
----------------------------------------
Technikai Stack
----------------------------------------
Backend:

Python 3.11+
Django
LangChain + LangGraph
Multi-Vector Store: Pinecone (namespaces) vagy Weaviate (tenants)
Embeddings: OpenAI text-embedding-3-large
LLM: GPT-4.1-mini / Claude 3.5 Sonnet
Workflow Tools: Jira SDK, Slack SDK, Google Drive API
Domain Coverage:

domains = {
    "hr": ["vacation", "benefits", "hiring", "payroll", "onboarding"],
    "it": ["vpn", "access", "software", "hardware", "network"],
    "finance": ["invoice", "expense", "budget", "payment", "tax"],
    "legal": ["contract", "compliance", "policy", "gdpr", "ip"],
    "marketing": ["brand", "campaign", "content", "social", "analytics"],
    "general": ["other", "faq", "general-info"]
}
AI rendszer képességek:
Skill	Implementáció
RAG (multi-dataset)	6 külön vector store, domain-specifikus embeddings
LangGraph (multi-branch)	Conditional routing 6 domain-re
Memory	Context tracking user sessionök között
Tool calling	Jira API, Slack API, file generation
Reasoning	Intent classification + domain routing
JSON output	Structured response + citations
Policy check	Guardrails (approval needed, SLA, compliance)
Prompt engineering	Domain-specific prompts + few-shot examples
Compliance & Security

AI Act Compliance:

✅ Citációk: Minden válasz tartalmazza a forrás dokumentum ID-ját
✅ Traceability: Logging minden döntésről (domain routing, retrieval scores)
✅ Human-in-the-loop: Workflow approval-ok emberi jóváhagyással
✅ Audit log: Teljes conversation history mentése

Security:

🔒 Role-based access: User csak a saját domain-jéhez fér hozzá (organisation)
🔒 Data encryption: Vector store titkosítva
🔒 PII masking: Érzékeny adatok (személyes info) maszkolása

----------------------------------------------------------------------------
Implementációs útmutató
---------------------------------------------------------------------------

Technikai Stack
# requirements.txt
langchain>=0.1.0
langgraph>=0.0.20
langchain-openai>=0.0.5
pydantic>=2.5.0
django
djangorest
qudrant
redis
uvicorn>=0.25.0

# Vector DB 
qdrant-client>=1.7.0        # Self-hosted

# Integrations (opcionális)
jira>=3.5.0
slack-sdk>=3.26.0
google-api-python-client>=2.110.0
LangGraph Alapstruktúra (közös)
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

---------------------------
Projekt-specifikus bővítések
---------------------------

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
----------------
Deployment
---------------
Docker Compose:

version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8001:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
    volumes:
      - ./data:/app/data

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
Production Considerations:

Load balancing (több backend instance)
Redis cache (embedding cache)
Monitoring (Prometheus + Grafana)
Logging (ELK stack)

Felépítés struktúra:
benketibor/
├── backend/               # Python Django + LangGraph
│   ├── domain/            # Models & interfaces
│   ├── infrastructure/    # Repositories & API clients
│   ├── services/          # Agent & business logic
│   └── main.py            # Django application - illetve a Django részét ha tovább bontanád, tedd
├── frontend/              # HTMX + Vanilla JS
│   ├── src/
│   │   ├── components/    # app components
│   │   └── App	           # Main app
│   └── Dockerfile
├── docker-compose.yml     # Container orchestration
├── README.md              # Main documentation
└── start-dev.sh           # Development script

Frontendet templatekkel tedd app alá belátásod szerint.

-----------------------------
Kapcsolódó dokumentumok
----------------------------
LangGraph használat: https://github.com/Global-rd/ai-agents-hu/blob/main/ai_agent_complex/docs/LANGGRAPH_USAGE_HU.md
LanGraph nodes példák: https://github.com/Global-rd/ai-agents-hu/blob/main/ai_agent_complex/docs/LANGGRAPH_NODES_HU.md
Agent loop: https://github.com/Global-rd/ai-agents-hu/blob/main/ai_agent_complex/docs/AGENT_LOOP_HU.md
Prompt engineering: https://github.com/Global-rd/ai-agents-hu/blob/main/ai_agent_complex/docs/PROMPTS.md
Architektúra: https://github.com/Global-rd/ai-agents-hu/blob/main/ai_agent_complex/docs/ARCHITECTURE.md
Architektúra diagram: benketibor/docs/knowledge_router.svg

---------------------------------------------------------------------------------
Feladatok
-------------------------------------------------------------------------------------------

1. Feladat: Hozz létre a benketibor mappa alá egy projekt keretet a docs/INIT_PROMPT.md-ben leírtak alapján, hozz létre a projekthez a Readme-t (tartalmazza az app indítási és egyéb hasznos parancsokat) és Installation Guide-ot hozzá. Docker alapokon. Kell egy .env example, requirements.txt a dockernek. Kell egy példa API hívás a felsoroltak bármelyikébe. Kell tehát a django app keret és az alap struktúra, kell egy példa API hívás (rád bízom, melyik először), innen építkezünk tovább. Ha ellentmondás van az init prompt-ban, jelezd mielőbb. benketibor mappa fölé nem nyúlhatsz, csak alá dolgozhatsz.

