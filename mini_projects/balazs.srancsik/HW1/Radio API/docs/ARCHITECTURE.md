# AI Agent Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      User Browser                           │
│                    (React Frontend)                         │
│  ┌─────────────┐  ┌──────────┐  ┌─────────────────┐       │
│  │ ChatWindow  │  │ ChatInput│  │  DebugPanel     │       │
│  └─────────────┘  └──────────┘  └─────────────────┘       │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP/REST API
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Layer (main.py)                     │  │
│  │  ┌─────────┐  ┌─────────┐  ┌──────────┐           │  │
│  │  │ /chat   │  │/profile │  │ /history │  ...      │  │
│  │  └────┬────┘  └────┬────┘  └────┬─────┘           │  │
│  └───────┼────────────┼────────────┼──────────────────┘  │
│          │            │            │                      │
│  ┌───────▼────────────▼────────────▼──────────────────┐  │
│  │         Service Layer (services/)                   │  │
│  │  ┌──────────────┐                                   │  │
│  │  │ ChatService  │ ◄── Orchestrates workflow        │  │
│  │  └──────┬───────┘                                   │  │
│  │         │                                            │  │
│  │  ┌──────▼────────┐  ┌──────────────────┐          │  │
│  │  │   AIAgent     │  │     Tools        │          │  │
│  │  │  (LangGraph)  │◄─┤ - Weather        │          │  │
│  │  │               │  │ - Geocode        │          │  │
│  │  │  ┌─────────┐  │  │ - IP Geolocation │          │  │
│  │  │  │ Agent   │  │  │ - FX Rates       │          │  │
│  │  │  │ Decide  │  │  │ - Crypto Price   │          │  │
│  │  │  └────┬────┘  │  │ - File Creation  │          │  │
│  │  │       │       │  │ - History Search │          │  │
│  │  │  ┌────▼────┐  │  └──────────────────┘          │  │
│  │  │  │  Tool   │  │                                 │  │
│  │  │  │  Nodes  │  │                                 │  │
│  │  │  └────┬────┘  │                                 │  │
│  │  │       │       │                                 │  │
│  │  │  ┌────▼────┐  │                                 │  │
│  │  │  │ Agent   │  │                                 │  │
│  │  │  │Finalize │  │                                 │  │
│  │  │  └─────────┘  │                                 │  │
│  │  └───────────────┘                                 │  │
│  └────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │      Infrastructure Layer (infrastructure/)        │  │
│  │  ┌──────────────────┐  ┌─────────────────────┐   │  │
│  │  │   Repositories    │  │   Tool Clients      │   │  │
│  │  │ - FileUser       │  │ - OpenMeteo         │   │  │
│  │  │   Repository     │  │ - Nominatim         │   │  │
│  │  │ - FileConv       │  │ - IPAPI             │   │  │
│  │  │   Repository     │  │ - ExchangeRateHost  │   │  │
│  │  │                  │  │ - CoinGecko         │   │  │
│  │  └─────────┬────────┘  └──────────┬──────────┘   │  │
│  └────────────┼──────────────────────┼──────────────┘  │
│               │                      │                  │
│  ┌────────────▼──────────┐  ┌────────▼──────────────┐  │
│  │   Domain Layer        │  │   External APIs       │  │
│  │   (domain/)           │  │ - Open-Meteo          │  │
│  │ - Models              │  │ - OpenStreetMap       │  │
│  │ - Interfaces          │  │ - ipapi.co            │  │
│  │                       │  │ - ExchangeRate.host   │  │
│  └───────────────────────┘  │ - CoinGecko           │  │
│                             │ - OpenAI GPT-4        │  │
└─────────────────────────────┴───────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │   File System         │
            │  ┌─────────────────┐  │
            │  │ data/           │  │
            │  │  users/         │  │
            │  │  sessions/      │  │
            │  │  files/         │  │
            │  └─────────────────┘  │
            └───────────────────────┘
```

## LangGraph Agent Workflow

```
User Message
    │
    ▼
┌───────────────────┐
│  agent_decide     │ ◄── Analyze request + memory
│  (LLM Reasoning)  │     Decide: tool or answer?
└─────────┬─────────┘
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼
  Tool?      Answer
  Call       Directly
    │           │
    ▼           │
┌────────────┐  │
│  Tool      │  │
│  Execution │  │
│  Nodes     │  │
└─────┬──────┘  │
      │         │
      └────┬────┘
           │
           ▼
    ┌──────────────┐
    │agent_finalize│ ◄── Generate natural
    │   (LLM)      │     language response
    └──────┬───────┘
           │
           ▼
    Final Answer
```

## Data Flow for a Chat Request

```
1. User types message
   ↓
2. Frontend sends POST /api/chat
   ↓
3. ChatService.process_message()
   ├── Check for "reset context" command
   │   ├── Yes → Clear history, keep profile → Return
   │   └── No → Continue
   ├── Load user profile (create if new)
   ├── Load conversation history (create if new)
   ├── Build memory context
   ├── Add user message to history (persist)
   └── Call AIAgent.run()
       │
       ├── Initialize LangGraph state
       └── Execute graph workflow
           │
           ├── agent_decide node
           │   ├── Build LLM prompt with context
           │   ├── Get decision from OpenAI
           │   └── Set next action (tool or final)
           │
           ├── tool_* node (if tool needed)
           │   ├── Execute tool (API call)
           │   ├── Record tool call
           │   ├── Add system message
           │   └── Update state
           │
           └── agent_finalize node
               ├── Build final prompt
               ├── Get response from OpenAI
               └── Add assistant message
   ↓
4. ChatService persists all messages
   ├── System messages (tool logs)
   └── Assistant message
   ↓
5. Check for profile updates
   ├── Detect language change
   ├── Detect city preference
   └── Update profile if needed
   ↓
6. Build ChatResponse
   ├── final_answer
   ├── tools_used
   ├── memory_snapshot
   └── logs
   ↓
7. Return to frontend
   ↓
8. Frontend displays message
   └── Update UI with tools & memory
```

## SOLID Principles Implementation

### Single Responsibility Principle (SRP)

```
FileUserRepository
└── Responsibility: Persist user profiles to/from JSON files

WeatherTool
└── Responsibility: Fetch weather data via external API

ChatService
└── Responsibility: Orchestrate chat workflow
```

### Open/Closed Principle (OCP)

```
Adding new tool:
1. Create new client implementing IToolClient
2. Create new tool wrapper
3. Register in AIAgent.__init__()
4. Graph automatically adds node
   → No modification to existing code!
```

### Liskov Substitution Principle (LSP)

```
All tool clients implement IToolClient
└── Can be swapped without breaking agent
    ├── Real implementations (production)
    └── Mock implementations (testing)
```

### Interface Segregation Principle (ISP)

```
IUserRepository
├── get_profile()
├── save_profile()
└── update_profile()

IConversationRepository
├── get_history()
├── save_history()
├── add_message()
├── clear_history()
└── search_messages()

Separate interfaces for different concerns!
```

### Dependency Inversion Principle (DIP)

```
High-level: ChatService
    │
    ├── Depends on IUserRepository (abstraction)
    │   └── Implemented by FileUserRepository (concrete)
    │
    └── Depends on AIAgent (abstraction)
        └── Depends on IToolClient (abstraction)
            └── Implemented by specific clients (concrete)

Direction of dependencies: High → Abstraction ← Low
```

## Memory and Persistence Model

```
User Profile (Never Deleted)
┌──────────────────────────┐
│ user_id                  │
│ language: "hu"           │
│ default_city: "Budapest" │
│ created_at               │
│ updated_at               │
│ preferences: {}          │
└──────────────────────────┘
         │
         │ 1:N
         ▼
Conversation Sessions (Can Reset)
┌──────────────────────────┐
│ session_id               │
│ messages: [              │
│   {role, content, ts},   │
│   {role, content, ts},   │
│   ...                    │
│ ]                        │
│ summary                  │
│ created_at               │
│ updated_at               │
└──────────────────────────┘
         │
         │ Feeds into
         ▼
Agent Memory Context
┌──────────────────────────┐
│ chat_history: [last 20]  │
│ preferences: {           │
│   language,              │
│   default_city,          │
│   ...                    │
│ }                        │
│ workflow_state: {        │
│   flow, step, data       │
│ }                        │
└──────────────────────────┘
```

## Tool Integration Pattern

```
External API
    │
    ▼
┌─────────────────┐
│  Tool Client    │ ◄── Infrastructure Layer
│  (IToolClient)  │     Handles API communication
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Tool Wrapper  │ ◄── Service Layer
│   (e.g.         │     Formats for agent
│    WeatherTool) │     Adds system messages
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LangGraph Node │ ◄── Agent executes
│  (tool_weather) │     Records in history
└─────────────────┘
```

## State Management

```
Frontend State
├── messages: ChatMessage[]
├── isLoading: boolean
├── lastToolsUsed: ToolUsed[]
├── memorySnapshot: MemorySnapshot
└── userId, sessionId (localStorage)

Backend State (per request)
├── AgentState (LangGraph)
│   ├── messages: BaseMessage[]
│   ├── memory: Memory
│   ├── tools_called: ToolCall[]
│   └── next_action: string
└── Persisted State (JSON files)
    ├── User profiles
    └── Conversation histories
```

## Reset Context Flow

```
User sends "reset context"
    │
    ▼
ChatService detects special command
    │
    ├── Load user profile (ensure exists)
    │
    ├── Clear conversation history file
    │   └── Create new ConversationHistory
    │       with empty messages list
    │
    ├── Keep user profile intact
    │   └── NO changes to profile
    │
    └── Return confirmation message
        └── In user's preferred language
```

This architecture ensures:
- ✅ Clean separation of concerns
- ✅ Easy testing and mocking
- ✅ Simple extension with new tools
- ✅ Transparent data persistence
- ✅ SOLID principles throughout
