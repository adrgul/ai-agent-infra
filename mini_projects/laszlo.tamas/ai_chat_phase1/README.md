# AI Chat - Phase 1

A complete, working multi-user chat application with OpenAI API integration. This is Phase 1 of a larger AI system, focusing on foundational chat functionality with external API calls.

## Project Overview

This application demonstrates:
- ✅ External API integration (OpenAI Chat Completions)
- ✅ Multi-user support (3 test users)
- ✅ Short-term conversation history in SQLite
- ✅ Clean, testable architecture
- ✅ Docker containerization

**Note:** This is Phase 1 ONLY. No LangGraph, no tools, no RAG, no vector database.

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- OpenAI Chat Completions API
- SQLite

### Frontend
- React 18
- TypeScript
- Vite

### Infrastructure
- Docker
- Docker Compose

## Prerequisites

- Docker and Docker Compose installed
- OpenAI API key

## Quick Start

1. **Clone the repository and navigate to the project directory:**
   ```bash
   cd ai_chat_phase1
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

3. **Start the application:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Database Schema

### Users Table
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    firstname TEXT NOT NULL,
    lastname TEXT NOT NULL,
    nickname TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT NOT NULL,
    is_active BOOLEAN NOT NULL,
    default_lang TEXT DEFAULT 'en',
    created_at DATETIME NOT NULL
);
```

**Predefined Test Users:**
1. Alice Johnson (alice_j) - Developer - ACTIVE - **Language: Hungarian (hu)**
2. Bob Smith (bob_s) - Manager - ACTIVE - **Language: English (en)**
3. Charlie Davis (charlie_d) - Analyst - INACTIVE - Language: English (en)

### Chat Sessions Table
```sql
CREATE TABLE chat_sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL
);
```

### Chat Messages Table (Event Log)
```sql
CREATE TABLE chat_messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL
);
```

## API Endpoints

### GET /api/users
Retrieve all users for the dropdown.

**Response:**
```json
[
  {
    "user_id": 1,
    "firstname": "Alice",
    "lastname": "Johnson",
    "nickname": "alice_j",
    "email": "alice@example.com",
    "role": "developer",
    "is_active": true,
    "default_lang": "hu",
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### GET /api/debug/{user_id}
Get debug information for a user (user data, AI summary, last 10 message exchanges).

**Response:**
```json
{
  "user_data": {
    "user_id": 1,
    "firstname": "Alice",
    "lastname": "Johnson",
    "nickname": "alice_j",
    "email": "alice@example.com",
    "role": "developer",
    "is_active": true,
    "default_lang": "hu",
    "created_at": "2024-01-01T00:00:00"
  },
  "ai_summary": "Alice is a developer who...",
  "last_exchanges": [
    {
      "timestamp": "2024-01-01T10:00:00",
      "user_message": "Hello",
      "assistant_message": "Hi Alice!"
    }
  ]
- **Language preference** per user (default_lang: hu/en)

### Chat Functionality
- Real-time message sending
- Chat history persistence
- Short-term memory (last 20 messages)
- System messages include user identity **and language preference**
- **Language-aware responses** (Hungarian for Alice, English for Bob)
- Error handling for API failures

### Debug Features
- **🐛 Debug button** (top-right corner, visible when user selected)
- **Debug modal** with three sections:
  - 📊 **User data**: All database fields including language preference
  - 🤖 **AI Summary**: LLM-generated summary of what it knows about the user
  - 💬 **Last 10 message exchanges**: Timestamped conversation history
- **🗑️ Delete conversation history**: Button to clear all messages for current user
  - Confirmation dialog before deletion
  - Clears both database and UI
  - Non-reversible action

### UI Components
- **HowTo Panel**: Left sidebar with usage instructions (loaded from HOW_TO.md)
- **UserDropdown**: Select active user
- **ChatWindow**: Scrollable message area (center)
- **MessageBubble**: Individual message display
- **ChatInput**: Fixed input bar at bottom
- **DebugModal**: Overlay with user info and conversation management
### POST /api/chat
Send a chat message and receive an AI response.

**Request:**
```json
{
  "user_id": 1,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Hello, how are you?"
}
```

**Response:**
```json
{
  "answer": "Hello Alice! I'm doing well, thank you for asking. How can I assist you today?"
}
```

## Application Features

### User Management
- 3 predefined test users
- User selection via dropdown
- Inactive users are disabled but visible
- User switching creates a new session

### Chat Functionality
- Real-time message sending
- Chat history persistence
- Short-term memory (last 20 messages)
- System messages include user identity
- Error handling for API failures

### UI Components
- **UserDropdown**: Select active user
- **ChatWindow**: Scrollable message area
- **MessageBubble**: Individual message display
- **ChatInput**: Fixed input bar at bottom

## Architecture

### Backend Structure
```
backend/
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Backend container config
├── database/
│   ├── db.py              # Database operations
│   └── models.py          # Pydantic models
├── services/
│   └── chat_service.py    # Business logic
└── api/
    ├── ├── ChatInput.tsx
│       ├── DebugModal.tsx    # Debug information overlay
│       └── HowTo.tsx         # Left sidebar help panel  # API endpoints
    └── schemas.py         # Request/Response models
```

### Frontend Structure
```
frontend/
├── src/
│   ├── App.tsx            # Main application
│   ├── api.ts             # API client
│   ├── types.ts           # TypeScript types
│   └── components/
│       ├── UserDropdown.tsx
│       ├── ChatWindow.tsx
│       ├── MessageBubble.tsx
│       └── ChatInput.tsx
├── index.html
├── package.json
├── vite.config.ts
└── Dockerfile
```

## Chat Flow

1. User selects an active user from dropdown
2. New session UUID is generated (or restored from localStorage)
3. Previous messages are loaded if session exists
4. User types a message and clicks Send
5. Backend validates user and loads context
6. System message includes user identity **and language preference**
7. Last 20 messages are loaded for context
8. OpenAI API is called with full context (includes language instruction)
9. Both user and assistant messages are persisted
10. Assistant response is displayed in UI **in the user's preferred language**

## Short-Term Memory (Phase 1)

Memory in Phase 1 means **ONLY**:
- Last N messages (default: 20) for current session
- No summarization
- No vector storage
- No long-term memory

## Error Handling

- User validation (exists and is_active)
- OpenAI API failures return user-friendly messages
- All errors are logged on the backend
- Frontend displays error messages in chat

## Development

### Running Backend Locally
```bash
cd backend
pip install -r requirements.txt
export OPENAI_API_KEY=your_key_here
uvicorn main:app --reload
```

### Running Frontend Locally
```bash
cd frontend
npm install
npm run dev
```

### Accessing Logs
```bash
# View backend logs
docker-compose logs -f backend

# View frontend logs
docker-compose logs -f frontend
```

### Stopping the Application
```bash
docker-compose down
```

### Rebuilding After Changes
```bash
docker-compose up --build
```

## Code Quality

- ✅ Thin FastAPI routes
- ✅ Separation of concerns (API / Service / Persistence)
- ✅ Pydantic models for validation
- ✅ Python logging (INFO level)
- ✅ TypeScript for type safety
- ✅ No dead code or TODOs

## Security Notes

- API key is read from environment variable
- NEVER hard-coded in source code
- CORS enabled for frontend origin
- Authentication is OUT OF SCOPE for Phase 1

## Testing the Application

### Basic Chat Flow
1. Open http://localhost:3000
2. Select "Alice Johnson" from dropdown
3. Send a message in Hungarian: "Szia!"
4. Observe AI response **in Hungarian**
5. Switch to "Bob Smith"
6. Send message in English: "Hello!"
7. Observe AI response **in English**
8. Try selecting "Charlie Davis" (inactive user - should be disabled)

### Debug Features
1. Select an active user (Alice or Bob)
2. Have a short conversation (3-5 messages)
3. Click the **🐛 Debug** button (top-right)
4. Observe three sections:
   - User data (check default_lang field)
   - AI-generated summary
   - Last 10 message exchanges
5. Click **🗑️ Előzmények törlése** button
6. Confirm deletion
7. Verify messages disappear from both Debug modal and chat window

### Session Persistence
1. Chat with Alice
2. Refresh the page (F5)
3. Select Alice again
4. Previous messages should load

### Language Switching
1. Chat with Alice in Hungarian
2. Switch to Bob
3. Chat in English
4. Switch back to Alice
5. Notice conversation history is preserved per user
8. Notice chat input is disabled

## Troubleshooting

### Backend won't start
- Check if OPENAI_API_KEY is set in `.env`
- Verify Docker is running
- Check port 8000 is not in use

### Frontend can't connect to backend
- Ensure backend is running
- Check backend health: http://localhost:8000/health
- Verify CORS settings in backend

### OpenAI API errors
- Verify API key is valid
- Check your OpenAI account has credits
- Review backend logs for detailed error messages

## What's NOT Included (Future Phases)

- ❌ LangGraph
- ❌ Agent tools
- ❌ RAG (Retrieval Augmented Generation)
- ❌ Vector database
- ❌ Long-term memory
- ❌ Authentication
- ❌ User registration

## License

This is an educational project for demonstration purposes.

## Support

For issues or questions, check the application logs:
```bash
docker-compose logs
```
