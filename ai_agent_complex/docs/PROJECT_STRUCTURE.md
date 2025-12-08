# Project Structure

```
ai_agent_complex/
├── backend/                    # Python FastAPI backend
│   ├── domain/                # Core business entities
│   │   ├── __init__.py
│   │   ├── models.py         # Pydantic models
│   │   └── interfaces.py     # Abstract interfaces
│   ├── infrastructure/        # External implementations
│   │   ├── __init__.py
│   │   ├── repositories.py   # File-based storage
│   │   └── tool_clients.py   # API clients
│   ├── services/             # Business logic
│   │   ├── __init__.py
│   │   ├── agent.py          # LangGraph agent
│   │   ├── tools.py          # Tool wrappers
│   │   └── chat_service.py   # Chat orchestration
│   ├── data/                 # Data storage (gitignored)
│   │   ├── users/           # User profiles
│   │   ├── sessions/        # Conversation histories
│   │   └── files/           # User files
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile           # Backend container
│   └── .env.example         # Environment template
├── frontend/                 # React TypeScript frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   └── DebugPanel.tsx
│   │   ├── App.tsx          # Main component
│   │   ├── App.css          # Styles
│   │   ├── api.ts           # API client
│   │   ├── types.ts         # TypeScript types
│   │   ├── utils.ts         # Utilities
│   │   └── main.tsx         # Entry point
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── nginx.conf           # Nginx config for Docker
│   └── Dockerfile           # Frontend container
├── docker-compose.yml       # Multi-container orchestration
├── .env.example             # Environment template
├── .gitignore
├── README.md                # Main documentation
├── QUICKSTART.md            # Quick start guide
├── ARCHITECTURE.md          # Architecture details
└── start-dev.sh             # Local dev script

Total files: ~40
Lines of code: ~3,500+
```

## File Counts by Category

**Backend Python**: ~25 files
- Domain layer: 2 files (~200 lines)
- Infrastructure: 2 files (~400 lines)
- Services: 3 files (~600 lines)
- API: 1 file (~200 lines)
- Config: 3 files

**Frontend TypeScript**: ~15 files
- Components: 4 files (~400 lines)
- Core: 5 files (~500 lines)
- Config: 6 files

**Documentation**: 4 files (~800 lines)

**Infrastructure**: 6 files
- Docker: 4 files
- Config: 2 files

## Key Technologies

### Backend Stack
- Python 3.11+
- FastAPI (async web framework)
- LangGraph (agent orchestration)
- LangChain (LLM utilities)
- OpenAI GPT-4 (reasoning)
- Pydantic (validation)
- httpx (async HTTP)

### Frontend Stack
- React 18
- TypeScript
- Vite (build tool)
- Axios (HTTP client)

### Infrastructure
- Docker & Docker Compose
- Nginx (reverse proxy)
- JSON files (persistence)

## Architecture Layers

1. **Domain Layer**: Pure business logic, no dependencies
2. **Infrastructure Layer**: External systems (APIs, files)
3. **Service Layer**: Orchestration and workflows
4. **API Layer**: HTTP endpoints and middleware
5. **Frontend Layer**: User interface
