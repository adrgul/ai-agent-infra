# KnowledgeRouter - AI Agent Demo

**Vállalati Tudásirányító & Workflow-Automata**

Multi-domain AI agent rendszer Python Django backenddel, LangGraph orchestrációval és modern Tailwind CSS frontenddel (ChatGPT-style UI).

## 🎯 Projekt Áttekintése

KnowledgeRouter egy vállalati belső tudásbázis rendszer, amely:

✅ **6 domain-re** szétválasztott tudásbázisokból keres (HR, IT, Finance, Legal, Marketing, General)  
✅ **Intent detection** segítségével felismeri, melyik domain-hez tartozik a kérdés  
✅ **RAG (Retrieval-Augmented Generation)** használ releváns dokumentumok megtalálásához  
✅ **Workflow-okat** futtat (HR szabadság igénylés, IT ticket, stb.)  
✅ **Citációkkal** ellátott válaszokat ad (dokumentum referenciák)  
✅ **Konverzáció előzményt** mentesít JSON-ban  
✅ **Docker-ben** futtatható

## 📋 Tech Stack

- **Backend**: Python 3.11+ | Django | LangGraph
- **LLM**: OpenAI GPT-4o Mini (gpt-4o-mini)
- **Vector DB**: Qdrant (self-hosted)
- **Frontend**: Tailwind CSS + Vanilla JavaScript (ChatGPT-style UI)
- **Deployment**: Docker Compose

## 🚀 Quick Start (Docker)

### 1. Klón és Setup

```bash
cd benketibor
cp .env.example .env
```

### 2. API Key Beállítása

```bash
# .env-ben add meg az OPENAI_API_KEY-t
nano .env
# Vagy set a Windows PowerShell-ben:
$env:OPENAI_API_KEY = "sk-your-key-here"
```

### 3. Docker Compose Indítása

```bash
docker-compose up --build
```

### 4. Hozzáférés

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001/api/
- **Qdrant Dashboard**: http://localhost:6334 (vector DB)

## 🎮 Próba Kérések

Nyisd meg a frontend-et és próbáld ezeket:

### HR Domain
```
"Szeretnék szabadságot igényelni október 3-4-re"
"Mi a szabadság politika?"
"Munkaadó támogatások?"
```

### IT Domain
```
"Nem működik a VPN"
"Hogyan telepítsem fel a VPN klienst?"
"Szoftver támogatás"
```

### Marketing Domain
```
"Hol van a brand guideline?"
"Legfrissebb marketing dokumentumok?"
```

## 📁 Projekt Struktúra

```
benketibor/
├── backend/                      # Django + LangGraph
│   ├── core/                    # Django settings & config
│   │   ├── settings.py          # App konfigurció
│   │   ├── urls.py              # URL routing
│   │   ├── wsgi.py / asgi.py    # WSGI/ASGI entry
│   │   └── __init__.py
│   ├── domain/                  # Business logic models
│   │   ├── models.py            # Pydantic data models
│   │   ├── interfaces.py        # Abstract base classes
│   │   └── __init__.py
│   ├── infrastructure/          # External integrations
│   │   ├── repositories.py      # File-based storage (users, sessions)
│   │   ├── rag_client.py        # Mock Qdrant client
│   │   └── __init__.py
│   ├── services/                # Business logic
│   │   ├── agent.py             # LangGraph agent (intent → retrieval → response)
│   │   ├── chat_service.py      # Chat orchestration
│   │   └── __init__.py
│   ├── api/                     # API endpoints
│   │   ├── views.py             # REST views (/api/query/, /api/sessions/)
│   │   ├── urls.py              # API URLs
│   │   ├── apps.py              # App initialization
│   │   └── __init__.py
│   ├── data/                    # Persistent storage (JSON)
│   │   ├── users/              # User profiles
│   │   ├── sessions/           # Conversation histories
│   │   └── files/              # Generated files
│   ├── manage.py                # Django CLI
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile               # Backend container

├── frontend/                    # Tailwind CSS + Vanilla JS
│   ├── templates/
│   │   └── index.html          # Chat UI (HTMX)
│   ├── static/css/
│   │   └── style.css           # Styles
│   ├── package.json            # Node dependencies
│   └── Dockerfile              # Frontend container

├── docker-compose.yml          # Multi-container orchestration
├── .env.example                # Environment template
├── README.md                   # This file
├── INSTALLATION.md             # Detailed setup guide
└── start-dev.sh               # Local dev script (bash)
```

## 🔧 API Végpontok

### POST `/api/query/`

Feldolgozz egy felhasználói kérdést az agent-en keresztül.

**Request:**
```json
{
  "user_id": "emp_001",
  "session_id": "session_abc123",
  "query": "Szeretnék szabadságot igényelni október 3-4-re",
  "organisation": "ACME Corp"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "domain": "hr",
    "answer": "Szabadságkérelmed rögzítésre került október 3-4 között. A policy szerint minimum 2 héttel előre kell jelezni. [HR-POL-001]",
    "citations": [
      {
        "doc_id": "HR-POL-001",
        "title": "Vacation Policy",
        "score": 0.94,
        "url": null
      }
    ],
    "workflow": {
      "action": "hr_request_draft",
      "type": "vacation_request",
      "status": "draft"
    }
  }
}
```

### GET `/api/sessions/{session_id}/`

Lekérd egy session beszélgetési előzményét.

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "session_abc123",
    "messages": [
      {
        "role": "user",
        "content": "Szeretnék szabadságot igényelni...",
        "timestamp": "2025-10-03T14:30:00"
      },
      {
        "role": "assistant",
        "content": "Szabadságkérelmed rögzítésre került...",
        "timestamp": "2025-10-03T14:30:05"
      }
    ]
  }
}
```

### POST `/api/reset-context/`

Töröld a session beszélgetési előzményét (de a user profil megmarad).

**Request:**
```json
{
  "session_id": "session_abc123"
}
```

## 🌐 Environment Változók

Szükséges `.env` fájl:

```bash
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,backend

# OpenAI API
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4o-mini

# Vector DB (Qdrant)
QDANT_HOST=localhost
QDANT_PORT=6334

# Database
DATABASE_URL=sqlite:///db.sqlite3
```

## 📝 Tipikus Workflow

```
User Query
    ↓
[Intent Detection] → Classify domain (HR/IT/Finance/etc)
    ↓
[Retrieval] → Search Qdrant for relevant documents
    ↓
[Generation] → LLM generates answer with citations
    ↓
[Workflow] → Execute domain-specific action (if needed)
    ↓
Response + Citations + Workflow Result
    ↓
[Persistence] → Save to JSON (conversation history)
```

## 🔐 Biztonság & Compliance

✅ **Citations**: Minden válasz tartalmazza a forrás dokumentum ID-ját  
✅ **Audit Log**: Teljes conversation history mentése  
✅ **Reset Context**: Special command a beszélgetési előzmények törlésére  
✅ **User Profiles**: Soha nem törlődnek, csak frissíthetők  

## 🛠️ Fejlesztés

### Local Dev (BASH/WSL)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # vagy venv\Scripts\activate (Windows)
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."
python manage.py runserver 0.0.0.0:8000

# Frontend (új terminal)
cd frontend
npx http-server . -p 3000
```

### Docker Dev

```bash
docker-compose up --build
# Changes are auto-reloaded (gunicorn --reload)
```

## 📚 Kapcsolódó Dokumentumok

- [Installation Guide](INSTALLATION.md)
- [LangGraph Usage (Repo)](../ai_agent_complex/docs/LANGGRAPH_USAGE_HU.md)
- [Agent Loop (Repo)](../ai_agent_complex/docs/AGENT_LOOP_HU.md)
- [Architecture (Repo)](../ai_agent_complex/docs/ARCHITECTURE.md)

## 🤝 Roadmap

- [ ] Qdrant vector store real integration (mock → real)
- [ ] Domain-specific workflows (HR approval, Jira ticket creation)
- [ ] Multi-turn conversation with context tracking
- [ ] Google Drive API integration
- [ ] Slack integration
- [ ] Frontend React version (optional)
- [ ] Monitoring & logging (Prometheus + Grafana)

## 📞 Support

Ha kérdésed van, nyisd meg az issue-t vagy nézd meg a `docs/` mappát.

---

**Happy Knowledge Routing! 🚀**
