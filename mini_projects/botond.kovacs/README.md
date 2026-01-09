
# AI Agent Demo - LangGraph + FastAPI + React

A complete working example demonstrating an AI Agent workflow with a Python backend (FastAPI + LangGraph) and React frontend.

- **Regulation Tool**: Provides RAG (Retrieval-Augmented Generation) capabilities for querying regulatory content, currently featuring the 2008. évi LX. Gáztörvény
- **GasExportTool**: Lets you query exported gas quantities (kWh) for a given point and date range using Transparency.host API

## 🎯 Overview

This application demonstrates the **Agent Workflow Cycle**:

```
Prompt → Decision → Tool → Observation → Memory → Response
```

**Workflow**: `Agent → Tool → Agent → User`

The agent uses **LangGraph** for orchestration, **OpenAI** for LLM capabilities, and provides a **ChatGPT-like interface** for interaction.

## ✨ Key Features


### Agent Capabilities
- **LangGraph-based orchestration**: Graph of nodes for agent reasoning and tool execution
- **Regulation RAG**: Query the 2008. évi LX. Gáztörvény using FAISS vector database
- **Gas Export Tool**: Query exported gas quantities for specific points and date ranges
- **Memory management**: Maintains user preferences, conversation history, and workflow state
- **Multi-language support**: Responds in user's preferred language (Hungarian/English)

### Persistence
- ✅ **All conversation messages** persisted to JSON files
- ✅ **User profiles** stored separately (never deleted)
- ✅ **Reset context** command: Clears conversation but preserves profile
- ✅ **File-based storage**: Simple, transparent, and easy to inspect

### Architecture
- 🏗️ **SOLID principles** applied throughout
- 📦 **Clean architecture**: Domain → Services → Infrastructure → API layers
- 🔌 **Dependency Inversion**: Abstract interfaces for all external dependencies
- 🎯 **Single Responsibility**: Each class/module has one clear purpose
- 🔓 **Open/Closed**: Easy to extend with new tools without modifying existing code

## 🏛️ Architecture


### Backend Structure

```
backend/
├── domain/                 # Domain layer - Core business entities
│   ├── models.py          # Data models (Message, UserProfile, Memory, etc.)
│   └── interfaces.py      # Abstract interfaces (IUserRepository, IToolClient, etc.)
├── infrastructure/        # Infrastructure layer - External implementations
│   ├── repositories.py    # File-based persistence (user profiles, conversations)
│   └── tool_clients.py    # Tool API clients (RegulationRAGClient, GasExportClient)
├── services/              # Service layer - Business logic
│   ├── agent.py           # LangGraph agent implementation
│   ├── tools.py           # Tool wrappers (RegulationTool, GasExportTool)
│   └── chat_service.py    # Chat workflow orchestration
└── main.py               # API layer - FastAPI endpoints
```


## 🛠️ Tool Implementations

### RegulationTool
Provides RAG (Retrieval-Augmented Generation) Q&A for the 2008. évi LX. Gáztörvény. Allows users to ask questions about the regulation, get relevant passages, and receive answers with sources.

**Main actions:**
- `query`: Ask a question about the regulation
- `info`: Get metadata about the regulation

**Parameters:**
- `action`: 'query' or 'info'
- `question`: The user's question (for 'query')
- `top_k`: Number of relevant passages to retrieve (default: 5)

**Example output:**
```
📚 **Answer from 'gaztorveny':**

A Magyar Energetikai és Közmű-szabályozási Hivatal (MEKH) felhatalmazásai a 2008. évi XL. törvény alapján ...

**Sources:**
[Page 146]: ...
[Page 145]: ...
```

---

### GasExportTool
Allows querying exported gas quantity (kWh) for a given point and date range using the Transparency.host API.

**Purpose:**
- Get daily and total exported gas quantities for a specific cross-border point and period.

**Parameters:**
- `pointLabel` (string, required): Name of the export point (e.g. 'VIP Bereg')
- `from` or `periodFrom` (string, required): Start date (YYYY-MM-DD)
- `to` or `periodTo` (string, required): End date (YYYY-MM-DD)

**How it works:**
- Calls the Transparency.host API for the given point and date range
- Returns daily values and the total for the period

**Example output:**
```
⛽ **Gas Exported Quantity for 'VIP Bereg':**

Period: 2025-12-01 to 2025-12-07
Total: 12,345,678 kWh

**Details:**
- Date: 2025-12-01 | Value: 1,234,567 kWh | Indicator: Export | Operator: FGSZ | Status: Confirmed
- Date: 2025-12-02 | Value: 1,234,567 kWh | Indicator: Export | Operator: FGSZ | Status: Confirmed
...
```

**Error handling:**
- If required parameters are missing, returns an error message
- If the API call fails, returns the error

---

### LangGraph Workflow

The agent is implemented as a **LangGraph state graph**:

```
┌─────────────────┐
│  agent_decide   │  ← Entry: Analyzes request, decides action
└────────┬────────┘
         │
         ├─→ tool_regulation ─────┤
         │
         └─→ agent_finalize ─→ END (if no tool needed)
```

**Nodes**:
- `agent_decide`: LLM reasoning - decides whether to call tools
- `tool_regulation`: Regulation tool execution node
- `agent_finalize`: Generates final natural language response

### Persistence Model

#### User Profile (`data/users/{user_id}.json`)
```json
{
  "user_id": "user_123",
  "language": "hu",
  "default_city": "Budapest",
  "created_at": "2025-12-08T10:00:00",
  "updated_at": "2025-12-08T10:30:00",
  "preferences": {}
}
```

**Behavior**:
- ✅ Created automatically on first interaction
- ✅ Updated when preferences change
- ❌ **Never deleted** - persists across all sessions


#### Conversation History (`data/sessions/{session_id}.json`)
```json
{
  "session_id": "session_1767436277743_e72yl3tzd",
  "messages": [
    {
      "role": "user",
      "content": "Mire van felhatalmazása a MEKH-nek (Hivatal) és mely pontok szerint?",
      "timestamp": "2026-01-03T15:58:57.179776",
      "metadata": null
    },
    {
      "role": "system",
      "content": "📚 **Answer from 'gaztorveny':**\n\nA Magyar Energetikai és Közmű-szabályozási Hivatal (MEKH) felhatalmazásai a 2008. évi XL. törvény - a földgázellátásról szóló törvény alapján széleskörűek és részletesen meghatározottak. Ezek közé tartoznak a földgázpiac szabályozásával, felügyeletével és a piaci szereplők tevékenységének ellenőrzésével kapcsolatos feladatok. A törvény alapján a MEKH felhatalmazást kap többek között:\n\n1. A földgázellátás keretszabályainak, árszabályozási ciklusainak meghatározására, a csatlakozási díjak és a külön díjak fizetésére kötelezettek körének, valamint az alkalmazásuk feltételeinek meghatározására.\n\n2. A földgázrendszerre történő csatlakozás részletes szabályainak, beleértve a műszaki-gazdasági feltételeket és azok közzétételét, valamint a földgázelosztó és földgázszállító csatlakozással kapcsolatos együttműködés szabályait.\n\n3. A szállítási rendszerüzemeltetési díjból származó árbevétel szállítási rendszerüzemeltetők közötti megosztására vonatkozó kiegyenlítő fizetések számítási módszerének és részletes szabályainak meghatározására.\n\n4. A rendszeregyensúlyozásra vonatkozó módszertan és részletszabályok, beleértve a rendszerüzemeltetői adatszolgáltatásokat és egyensúlytartási szolgáltatásokat.\n\n5. A rendszer-összekötési pontokra vonatkozó szabályok alkalmazását harmadik országok felől való betáplálási és kiadási pontokra.\n\n6. Az adatszolgáltatásra kötelezettek által szolgáltatandó adatok körének, az adatszolgáltatás teljesítésének módjára és esedékességére vonatkozó követelmények meghatározására.\n\n7. A válsághelyzeti monitoringrendszer működésének részletszabályainak, valamint a védett felhasználók és a szolidaritási alapon védett felhasználók földgáz felhasználásának meghatározására.\n\n8. Az energetikai szabályozási tesztkörnyezet által támogatott célok, a kérelem benyújtására jogosultak körének és a kérelem elbírálásával kapcsolatos szabályok meghatározására.\n\nEzen felül a MEKH felhatalmazást kap a műszaki-biztonsági szempontból jelentős munkakörök betöltéséhez szükséges szakmai képesítés és gyakorlat, valamint a továbbképzésekkel kapcsolatos szabályok meghatározására, a gázszerelők és gázkészülék-javítók tevékenységének részletes feltételeire, a műszaki biztonsági követelményekre, valamint a gázfogyasztó készülékek forgalomba hozatalára és üzembe helyezésére vonatkozó szabályokra.\n\n**Sources:**\n[Page 146]: 2008. évi XL. törvény - a földgázellátásról \nHatály: 2025.VIII.1. -   Jogtár \n  147/165 oldal \nkeret...\n[Page 145]: 2008. évi XL. törvény - a földgázellátásról \nHatály: 2025.VIII.1. -   Jogtár \n  146/165 oldal \nHivat...\n[Page 136]: 2008. évi XL. törvény - a földgázellátásról \nHatály: 2025.VIII.1. -   Jogtár \n  137/165 oldal \n(4) A...",
      "timestamp": "2026-01-03T15:59:42.883731",
      "metadata": null
    },
    {
      "role": "assistant",
      "content": "A Magyar Energetikai és Közmű-szabályozási Hivatal (MEKH) számos fontos és részletesen meghatározott feladattal rendelkezik a földgázellátás szabályozása terén, a 2008. évi XL. törvény alapján. Ezek a feladatok magukban foglalják a piac szabályozását, felügyeletét és a piaci szereplők ellenőrzését. A MEKH felhatalmazásai között szerepelnek például a földgázellátás keretszabályainak meghatározása, a csatlakozási díjak szabályozása, a rendszerüzemeltetési díjak megosztása, adatszolgáltatási követelmények meghatározása és a válsághelyzeti intézkedések szabályozása. Emellett a MEKH felel a műszaki biztonsági előírások, a gázszerelők és javítók tevékenységének szabályozása, valamint a gázfogyasztó készülékek forgalomba hozatalára és üzembe helyezésére vonatkozó előírások megállapításáért is. Ezek a felhatalmazások biztosítják a földgázpiac zökkenőmentes és biztonságos működését.",
      "timestamp": "2026-01-03T15:59:42.890939",
      "metadata": null
    }
  ],
  "summary": null,
  "created_at": "2026-01-03T15:58:57.176536",
  "updated_at": "2026-01-03T15:59:42.903534"
}
```

**Behavior**:
- ✅ All messages (user, assistant, system, tool) are persisted
- ✅ Can be cleared with "reset context" command
- ✅ User profile remains intact after reset

### Frontend Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatWindow.tsx      # Scrollable message list
│   │   ├── MessageBubble.tsx   # Individual message display
│   │   ├── ChatInput.tsx       # User input field
│   │   └── DebugPanel.tsx      # Tools & memory viewer
│   ├── App.tsx                 # Main application
│   ├── api.ts                  # Backend API client
│   ├── types.ts                # TypeScript interfaces
│   └── utils.ts                # Utility functions
├── index.html
├── vite.config.ts
└── package.json
```

## 🚀 Getting Started

### Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose** (for containerized deployment)
- **OpenAI API Key**

### Option 1: Docker (Recommended)

1. **Clone and navigate**:
   ```bash
   cd ai_agent_complex
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Option 2: Local Development

#### Backend

1. **Navigate to backend**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variable**:
   ```bash
   export OPENAI_API_KEY='your_api_key_here'
   # On Windows: set OPENAI_API_KEY=your_api_key_here
   ```

5. **Run the server**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Frontend

1. **Navigate to frontend**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Run development server**:
   ```bash
   npm run dev
   ```

4. **Access**: http://localhost:3000

## 📚 API Endpoints

### `POST /api/chat`
Process chat message or reset context.

**Request**:
```json
{
  "user_id": "user_123",
  "message": "Mire van felhatalmazása a MEKH-nek (Hivatal) és mely pontok szerint?",
  "session_id": "session_1767436277743_e72yl3tzd"
}
```

**Response**:
```json
{
  "final_answer": "A Magyar Energetikai és Közmű-szabályozási Hivatal (MEKH) számos fontos és részletesen meghatározott feladattal rendelkezik a földgázellátás szabályozása terén, a 2008. évi XL. törvény alapján. Ezek a feladatok magukban foglalják a piac szabályozását, felügyeletét és a piaci szereplők ellenőrzését. A MEKH felhatalmazásai között szerepelnek például a földgázellátás keretszabályainak meghatározása, a csatlakozási díjak szabályozása, a rendszerüzemeltetési díjak megosztása, adatszolgáltatási követelmények meghatározása és a válsághelyzeti intézkedések szabályozása. Emellett a MEKH felel a műszaki biztonsági előírások, a gázszerelők és javítók tevékenységének szabályozása, valamint a gázfogyasztó készülékek forgalomba hozatalára és üzembe helyezésére vonatkozó előírások megállapításáért is. Ezek a felhatalmazások biztosítják a földgázpiac zökkenőmentes és biztonságos működését.",
  "tools_used": [
    {
      "name": "regulation",
      "arguments": {
        "action": "query",
        "question": "Mire van felhatalmazása a MEKH-nek (Hivatal) és mely pontok szerint?",
        "top_k": 5
      },
      "success": true,
      "result": {
        "answer": "A Magyar Energetikai és Közmű-szabályozási Hivatal (MEKH) felhatalmazásai a 2008. évi XL. törvény - a földgázellátásról szóló törvény alapján széleskörűek és részletesen meghatározottak. Ezek közé tartoznak a földgázpiac szabályozásával, felügyeletével és a piaci szereplők tevékenységének ellenőrzésével kapcsolatos feladatok. A törvény alapján a MEKH felhatalmazást kap többek között: ...",
        "sources": [
          {"page": 146, "content_preview": "2008. évi XL. törvény - a földgázellátásról ..."},
          {"page": 145, "content_preview": "2008. évi XL. törvény - a földgázellátásról ..."},
          {"page": 136, "content_preview": "2008. évi XL. törvény - a földgázellátásról ..."}
        ],
        "regulation_title": "gaztorveny"
      }
    }
  ],
  "memory_snapshot": {
    "preferences": {
      "language": "hu"
    },
    "workflow_state": {
      "flow": null,
      "step": 0,
      "total_steps": 0
    },
    "message_count": 3
  },
  "logs": ["Tools called: 1"]
}
```

### `GET /api/session/{session_id}`
Get conversation history.

### `GET /api/profile/{user_id}`
Get user profile.

### `PUT /api/profile/{user_id}`
Update user profile.

**Request**:
```json
{
  "language": "en",
  "default_city": "Szeged"
}
```


### `GET /api/history/search?q=MEKH`
Search conversation history for regulation tool queries.

**Example Response:**
```json
{
  "results": [
    {
      "session_id": "session_1767436277743_e72yl3tzd",
      "message": {
        "role": "user",
        "content": "Mire van felhatalmazása a MEKH-nek (Hivatal) és mely pontok szerint?",
        "timestamp": "2026-01-03T15:58:57.179776"
      },
      "answer": {
        "role": "assistant",
        "content": "A Magyar Energetikai és Közmű-szabályozási Hivatal (MEKH) számos fontos és részletesen meghatározott feladattal rendelkezik a földgázellátás szabályozása terén, a 2008. évi XL. törvény alapján. ..."
      },
      "sources": [
        {"page": 146, "content_preview": "2008. évi XL. törvény - a földgázellátásról ..."},
        {"page": 145, "content_preview": "2008. évi XL. törvény - a földgázellátásról ..."}
      ]
    }
  ],
  "total": 1
}
```

## 💡 Example Interactions


### Language Preference Update
```
User: From now on, answer in English
Agent: [Updates user profile]
Response: Understood! I will respond in English from now on.
```

### Reset Context
```
User: reset context
Agent: [Clears conversation history, keeps profile]
Response: Context has been reset. We are starting a new conversation, but your preferences are preserved.
```


## 🎨 Special Features

### Reset Context Command
When a user sends `"reset context"` (case-insensitive):
1. ✅ Conversation history is **cleared**
2. ✅ User profile is **preserved**
3. ✅ New session starts fresh
4. ✅ Preferences (language, city) remain intact

**Implementation**: Detected in `ChatService.process_message()` before agent invocation.

### User Profile Management
- **Never deleted**: Only created/loaded and updated
- **Automatic updates**: Agent detects preference changes in conversation
- **Manual updates**: Via `PUT /api/profile/{user_id}` endpoint
- **Persistent across sessions**: Stored in `data/users/{user_id}.json`

### Memory Context
The agent receives:
- **Recent messages**: Last 20 messages for context
- **User preferences**: Language, default city, custom preferences
- **Workflow state**: Multi-step process tracking (extensible)

## 🏗️ SOLID Principles Applied

### Single Responsibility Principle (SRP)
- Each class/module has **one clear purpose**
- `ChatService`: Only orchestrates chat workflow

### Open/Closed Principle (OCP)
- **Easy to add new tools** without modifying existing code
- New tool: Implement `IToolClient`, create wrapper in `tools.py`, register in `agent.py`
- **No changes needed** to agent core logic or graph structure

### Liskov Substitution Principle (LSP)
- All tool clients implement `IToolClient` interface
- Can be swapped without breaking agent functionality
- Mock implementations for testing

### Interface Segregation Principle (ISP)
- **Specific interfaces** for different concerns:
  - `IUserRepository`: User profile operations
  - `IConversationRepository`: Conversation operations
  - `IRegulationRAGClient`: Specific tool operations
- Clients only depend on methods they use

### Dependency Inversion Principle (DIP)
- High-level modules (`ChatService`, `AIAgent`) depend on **abstractions** (`IUserRepository`, `IToolClient`)
- Low-level modules (repositories, API clients) implement abstractions
- **Easy to swap implementations** (file storage → database, real APIs → mocks)

## 🛠️ Technologies

### Backend
- **FastAPI**: Modern async web framework
- **LangGraph**: Agent orchestration and workflow
- **LangChain**: LLM integration utilities
- **OpenAI**: GPT-4 for reasoning and responses
- **Pydantic**: Data validation and settings
- **httpx**: Async HTTP client for tools

### Frontend
- **React 18**: UI library
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool
- **Axios**: HTTP client
- **CSS**: Custom ChatGPT-like styling

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Static file serving and reverse proxy
- **JSON files**: Simple, transparent persistence

## 📂 Data Storage

All data is stored in JSON files for transparency and easy inspection:

```
data/
├── users/           # User profiles (never deleted)
│   └── user_123.json
├── sessions/        # Conversation histories (can be reset)
│   └── session_456.json
└── files/           # User-created files
    └── user_123/
        └── note.txt
```

## 🧪 Development

### Backend Tests
```bash
cd backend
pytest  # (Add tests in tests/ directory)
```

### Frontend Tests
```bash
cd frontend
npm test  # (Add tests with Vitest/Jest)
```

### Type Checking
```bash
cd frontend
npm run type-check
```

## 🔒 Environment Variables

### Required
- `OPENAI_API_KEY`: Your OpenAI API key

### Optional
- Backend runs on port `8000` by default
- Frontend runs on port `3000` by default
- Adjust in `docker-compose.yml` or locally

## 🚧 Extending the Application

### Adding a New Tool

1. **Create client** in `infrastructure/tool_clients.py`:
   ```python
   class MyAPIClient(IToolClient):
       async def execute(self, **kwargs) -> Dict[str, Any]:
           # Implementation
   ```

2. **Create tool wrapper** in `services/tools.py`:
   ```python
   class MyTool:
       def __init__(self, client: MyAPIClient):
           self.client = client
           self.name = "my_tool"
           self.description = "..."
       
       async def execute(self, **kwargs) -> Dict[str, Any]:
           # Wrapper logic
   ```

3. **Register in agent** (`services/agent.py`):
   ```python
   self.tools["my_tool"] = my_tool_instance
   ```

4. **Add to graph** (automatic via node creation in `_build_graph`)

### Adding a New Workflow Step

Modify `WorkflowState` in `domain/models.py` and update `ChatService` logic to track multi-step processes.

## 📝 License

This is a demo application for educational purposes.

## 🤝 Contributing

This is a teaching example. Feel free to fork and extend for your own learning!

---

**Built with ❤️ for the Regulation team**

## Tesztesetek

**Kérdés:** Listázd, hogy mely paragrafusok foglalkoznak az egyetemes szolgáltatóval!

**Várt válasz:**

Az egyetemes szolgáltatóval kapcsolatos legfontosabb paragrafusok a 2008. évi XL. törvényben a következők:

- **106/A. §** Az egyetemes szolgáltatást nyújtó szolgáltatók által kínált külön díjas szolgáltatások meghatározása.
- **107. §** Az egyetemes szolgáltatás árazásának elvei.
- **107/A. §** Árak nyilvánosságra hozatala és tájékoztatás a felmondási jogról.
- **34. §** Szerződéskötési kötelezettség az egyetemes szolgáltatóra nézve.
- **35. §** Az egyetemes szolgáltatási szerződés tartalma.
- **56. §** Ügyfélszolgálat működtetése.
- **115/B. §** Az egyetemes szolgáltatók közötti átadó-átvevő folyamat szabályozása.

Ezek a részek részletesen tárgyalják az egyetemes szolgáltató kötelezettségeit, az árazási elveket, az ügyfél tájékoztatását, valamint az ügyfélszolgálati követelményeket. Ha további részletekre vagy pontosításokra van szükséged e témában, nyugodtan kérdezz tovább!

**Kérdés:** A Hivatal a földgázellátással, a földgázellátás biztonságának és a földgázpiac hatékony működésének felügyeletével, továbbá az egyenlő bánásmód követelményének érvényesítésével, és a hatásos verseny elősegítésével kapcsolatos feladatai körében mely paragrafus és pontok szerint feladatai ellátásához az engedélyes társaságtól, a regisztrációköteles tevékenységet végzőtől, a mintaprojektet végző társaságtól, valamint a hazai termelésű földgázt termelőtől eseti és rendszeres információkat kérni?

**Várt válasz:**

A Magyar Energetikai és Közmű-szabályozási Hivatal (MEKH) jogosult eseti és rendszeres információkat kérni az engedéllyel rendelkező társaságoktól, a tevékenységüket regisztrálni kötelezett szervezetektől, a kísérleti projekteket végrehajtó társaságoktól és a belföldön termelt földgáz termelőitől. Ezt a felhatalmazást a 2008. évi földgázellátási törvény (2008. évi XL. törvény) részletezi, konkrétan a 130/165. oldalon található s) és sc) bekezdésében. Ez a rendelkezés lehetővé teszi a MEKH számára, hogy ellássa a földgázellátás felügyeletével, a földgázellátás biztonságának biztosításával, a földgázpiac hatékony működésének biztosításával, az egyenlő bánásmód követelményének érvényesítésével és a hatékony verseny elősegítésével kapcsolatos feladatait.
