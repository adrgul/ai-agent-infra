# AI Chat Phase 1 - INIT PROMPT

You are GitHub Copilot. Generate a COMPLETE working example application that demonstrates a multi-user chat system with OpenAI integration.

## Goal
Build a small but realistic demo app for an AI programming course that demonstrates:
- Multi-user chat functionality
- OpenAI API integration
- SQLite database persistence
- Clean architecture with separation of concerns
- Docker containerization
- React + TypeScript frontend

The application MUST:
- Use Docker for containerization (backend + frontend, runnable via docker-compose).
- Use OpenAI Chat Completions API with API key provided via environment variable OPENAI_API_KEY.
- Persist ALL chat messages and user data to SQLite database.
- Support multiple users with proper session management.
- Implement short-term memory (last 20 messages per session).
- Follow SOLID principles and clean architecture.

## High-level Requirements

Backend: Python (FastAPI) implementing a chat service with OpenAI integration.
Frontend: React + TypeScript, ChatGPT-like UI.
Chat capabilities:
- Multi-user support with 3 predefined test users
- Session-based conversations
- Message persistence to SQLite
- OpenAI integration for AI responses
- User identity context in system messages
- Error handling and logging

## Technologies & Architecture

### Backend
- Language: Python 3.11+
- Framework: FastAPI
- Database: SQLite with sqlite3
- LLM integration: OpenAI Chat Completions with API key from OPENAI_API_KEY env var
- Data models: Pydantic models for requests, responses, users, messages
- Logging: Python logging module
- Architecture & SOLID:
  - Structure into layers: api, services, database
  - Clear separation: routes (thin), services (business logic), database (persistence)
  - Dependency injection where appropriate
  - Single responsibility per module

### Frontend
- React 18 + TypeScript
- Build with Vite
- ChatGPT-like interface:
  - Scrollable chat history
  - User input at bottom
  - Message bubbles with different styling for user/assistant
- Components: UserDropdown, ChatWindow, MessageBubble, ChatInput
- State management: React hooks
- API client for backend communication

## Database Schema

SQLite database with 3 tables:

### Users Table
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    firstname TEXT NOT NULL,
    lastname TEXT NOT NULL,
    nickname TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    default_lang TEXT DEFAULT 'en',
    created_at DATETIME NOT NULL
);
```

**Predefined Test Users:**
1. Alice Johnson (alice_j) - Developer - ACTIVE - Hungarian (default_lang: 'hu')
2. Bob Smith (bob_s) - Manager - ACTIVE - English (default_lang: 'en')
3. Charlie Davis (charlie_d) - Analyst - INACTIVE - English (default_lang: 'en')

### Chat Sessions Table
```sql
CREATE TABLE chat_sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
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
    created_at DATETIME NOT NULL,
    FOREIGN KEY (session_id) REFERENCES chat_sessions (id),
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);
```

## Backend Details: Endpoints & Behavior

Create a FastAPI app with the following endpoints:

### 1) GET /api/users
- Returns list of all users
- Response: Array of user objects with all fields

### 2) GET /api/chat/{session_id}/messages
- Returns all messages for a specific session
- Response: Array of message objects ordered by created_at

### 3) POST /api/chat
Request body:
```json
{
  "user_id": 1,
  "session_id": "uuid-string",
  "message": "User's message text"
}
```

Behavior:
1. Validate user exists and is active
2. Create session if it doesn't exist
3. Load last 20 messages for context
4. Build system message with user identity
5. Call OpenAI Chat Completions API
6. Persist both user and assistant messages
7. Return assistant response

Response:
```json
{
  "answer": "Assistant's response text"
}
```

## Chat Flow Implementation

### Message Processing Pipeline
1. **User Validation**: Check user exists and is_active
2. **Session Management**: Create session if new
3. **Context Loading**: Load last 20 messages from database
4. **System Message**: Include user identity and context
5. **OpenAI Call**: Send full context to OpenAI
6. **Persistence**: Save both messages to database
7. **Response**: Return assistant answer

### System Message Format
```
You are a helpful AI assistant in a test-mode internal chat system.
You are currently chatting with {firstname} {lastname} (nickname: {nickname}, role: {role}, email: {email}, preferred language: {default_lang}).
{language_instruction} Provide helpful, concise responses. This is a test environment.
```

**Language Instructions:**
- If default_lang == 'hu': "Respond in Hungarian."
- If default_lang == 'en': "Respond in English."
- The LLM automatically adapts its responses based on the user's language preference

### OpenAI Integration
- Model: gpt-3.5-turbo
- Temperature: 0.7
- Max tokens: 500
- Include full message history in context

## Frontend Implementation

### Components Structure
```
App.tsx (main container)
├── HowTo.tsx (left sidebar with instructions)
├── UserDropdown.tsx (user selection)
├── ChatWindow.tsx (message list - center)
│   └── MessageBubble.tsx (individual messages)
├── ChatInput.tsx (message input - bottom)
└── DebugModal.tsx (overlay with user info & debug features)
```

### State Management
- users: User[] - loaded from API
- selectedUserId: number | null
- sessionId: string - generated per user, stored in localStorage
- messages: Message[] - current conversation
- isLoading: boolean - for API calls
- isDebugOpen: boolean - debug modal visibility

### Key Behaviors
- User selection creates new session and loads previous messages
- Messages persist across page refreshes via localStorage sessionId
- Auto-focus input after assistant response
- Loading states and error handling
- Disabled input for inactive users
- **Debug button** appears when user is selected
- **Language-aware responses** based on user's default_lang

### Debug Features
- **Debug Modal** accessible via 🐛 button (top-right)
- Displays:
  - User data from database (all fields including default_lang)
  - AI-generated summary of user knowledge
  - Last 10 message exchanges with timestamps
- **Delete Conversations** button:
  - Confirmation dialog
  - Deletes all messages and sessions for current user
  - Refreshes both debug modal and chat window

## Docker Setup

### Backend Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 80
CMD ["npx", "serve", "-s", "dist", "-l", "80"]
```

### docker-compose.yml
```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

## Code Quality Requirements

### Backend
- **Separation of Concerns**: API routes, business logic, data access
- **Error Handling**: Proper exception handling and logging
- **Validation**: Pydantic models for all inputs/outputs
- **Logging**: Structured logging for debugging
- **Database**: Proper connection management with context managers

### Frontend
- **TypeScript**: Full type safety
- **React Best Practices**: Hooks, functional components
- **Accessibility**: Proper ARIA labels and keyboard navigation
- **Performance**: Efficient re-renders, no memory leaks
- **Styling**: Clean CSS with responsive design

## Testing Scenarios

### Happy Path
1. Select active user (Alice)
2. Send message: "Hello"
3. Receive AI response
4. Send another message: "What's my name?"
5. AI responds with user context

### Edge Cases
1. Select inactive user (Charlie) - input disabled
2. Send empty message - no API call
3. OpenAI API failure - error message displayed
4. Database connection issues - proper error handling

### Memory Testing
1. Send multiple messages in one session
2. Check that context includes previous messages
3. Verify messages persist in database
4. Test session isolation between users

## Documentation Requirements

Include comprehensive README.md with:
- Project overview and goals
- Tech stack details
- Database schema documentation (including default_lang field)
- API endpoint specifications (including /api/debug endpoints)
- Frontend component descriptions (including DebugModal and HowTo)
- Docker setup instructions
- Development setup (local running)
- Testing instructions (including debug features)
- Language support documentation
- Troubleshooting guide

Include HOW_TO.md with:
- Practical testing guide for instructors
- User testing scenarios
- Language switching demonstrations
- Debug features usage
- Memory testing procedures
- Step-by-step program operation

## Implementation Notes

### Database Initialization
- Create tables on startup if they don't exist
- Seed with 3 test users on first run
- Use proper foreign key relationships

### Session Management
- UUID-based session IDs
- One session per user selection
- Persistent across page refreshes via localStorage

### OpenAI Integration
- Proper error handling for API failures
- Rate limiting considerations (though not implemented)
- Cost tracking (optional)

### Security Considerations
- API key via environment variables
- Input validation and sanitization
- CORS configuration for frontend

Now, based on ALL of the above requirements, generate:
- Backend Python code (FastAPI, OpenAI integration, SQLite persistence)
- Frontend React + TypeScript code (chat UI with components)
- Dockerfiles and docker-compose.yml
- Comprehensive README.md

Use clear, modern, well-structured code with detailed comments explaining:
- Database operations and schema
- API endpoint implementations
- Chat flow and message processing
- Component architecture and state management
- Docker containerization setup</content>
<parameter name="filePath">c:\Users\laszl\work\ai_course_playground\ai_chat_phase1\INIT_PROMPT.md