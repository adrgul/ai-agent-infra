# AI Agent Demo - LangGraph + FastAPI + React

A complete working example demonstrating an AI Agent workflow with a Python backend (FastAPI + LangGraph) and React frontend.
The recent changes made are: 
- **Radio API Tool**: Fetches current radio station information and playing tracks for various countries and genres
- **Book Tool**: Provides RAG (Retrieval-Augmented Generation) capabilities for querying literary content, currently featuring Ferenc Molnár's "Pál Utcai Fiúk"

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
- **7 integrated tools**:
  - 🌤️ Weather forecast (Open-Meteo)
  - 🗺️ Geocoding and reverse geocoding (OpenStreetMap Nominatim)
  - 📍 IP geolocation (ipapi.co)
  - 💱 Foreign exchange rates (ExchangeRate.host)
  - ₿ Cryptocurrency prices (CoinGecko)
  - 📝 File creation (local storage)
  - 🔍 Conversation history search
  - 📻 New feature: Radio API, where you can ask stats about radio stations all over the world
  - 📚 Book RAG: Query Ferenc Molnár's "Pál Utcai Fiúk" using FAISS vector database

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
│   └── tool_clients.py    # External API clients (weather, crypto, FX, etc.)
├── services/              # Service layer - Business logic
│   ├── agent.py           # LangGraph agent implementation
│   ├── tools.py           # Tool wrappers for agent
│   └── chat_service.py    # Chat workflow orchestration
└── main.py               # API layer - FastAPI endpoints
```

### LangGraph Workflow

The agent is implemented as a **LangGraph state graph**:

```
┌─────────────────┐
│  agent_decide   │  ← Entry: Analyzes request, decides action
└────────┬────────┘
         │
         ├─→ tool_weather ──┐
         ├─→ tool_geocode ──┤
         ├─→ tool_ip ───────┤
         ├─→ tool_fx ───────┼─→ agent_finalize ─→ END
         ├─→ tool_crypto ───┤
         ├─→ tool_file ─────┤
         ├─→ tool_radio ────┤
         ├─→ tool_book ─────┤
         ├─→ tool_search ───┘
         │
         └─→ agent_finalize ─→ END (if no tool needed)
```

**Nodes**:
- `agent_decide`: LLM reasoning - decides whether to call tools
- `tool_*`: Individual tool execution nodes
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
  "session_id": "session_456",
  "messages": [
    {
      "role": "user",
      "content": "What's the weather in Budapest?",
      "timestamp": "2025-12-08T10:15:00",
      "metadata": null
    },
    {
      "role": "system",
      "content": "Fetched weather forecast for location (47.4979, 19.0402)",
      "timestamp": "2025-12-08T10:15:01",
      "metadata": null
    },
    {
      "role": "assistant",
      "content": "A jelenlegi hőmérséklet Budapesten 12°C.",
      "timestamp": "2025-12-08T10:15:02",
      "metadata": null
    }
  ],
  "summary": null,
  "created_at": "2025-12-08T10:15:00",
  "updated_at": "2025-12-08T10:15:02"
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
  "message": "What's the weather in Budapest?",
  "session_id": "session_456"
}
```

**Response**:
```json
{
  "final_answer": "A jelenlegi hőmérséklet Budapesten 12°C.",
  "tools_used": [
    {
      "name": "weather",
      "arguments": {"city": "Budapest"},
      "success": true
    }
  ],
  "memory_snapshot": {
    "preferences": {
      "language": "hu",
      "default_city": "Budapest"
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

### `GET /api/history/search?q=weather`
Search conversation history.

## 💡 Example Interactions

### Weather Query
```
User: What will the weather be like tomorrow in Budapest?
Agent: [Calls geocode tool → weather tool]
Response: A holnap előrejelzett hőmérséklet Budapesten 8-14°C között lesz.
```

### Cryptocurrency Price
```
User: What's the current BTC price in EUR?
Agent: [Calls crypto_price tool]
Response: A Bitcoin (BTC) jelenlegi ára 42,350 EUR, 24 órás változás: +2.3%.
```

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

### History Search
```
User: Search our past conversations for 'weather'
Agent: [Calls search_history tool]
Response: I found 3 previous mentions of weather in our conversations...
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
- `FileUserRepository`: Only handles user profile persistence
- `WeatherTool`: Only handles weather API calls
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
  - `IWeatherClient`, `IFXRatesClient`, etc.: Specific tool operations
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

**Built with ❤️ for the AI Agent Programming Course**
