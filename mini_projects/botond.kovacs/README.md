# AI Agent Workflow Demo

This project demonstrates an AI Agent workflow with a Python backend (FastAPI) and a React frontend. The application showcases the agent cycle:

- **Prompt → Decision → Tool → Observation → Memory**

## Features

- **Backend**:
  - FastAPI with LangGraph for agent orchestration.
  - OpenAI integration for LLM reasoning.
  - Tools for gas exported quantity and JSON history search.
  - Persistent user profiles and conversation history.
  - "Reset context" functionality.

- **Frontend**:
  - ChatGPT-like interface built with React + TypeScript.
  - Displays chat history and allows user input.

- **Dockerized**:
  - Backend and frontend are containerized and runnable via `docker-compose`.

## Setup

### Prerequisites

- Docker and Docker Compose installed.
- OpenAI API key.

### Running the Application

1. Clone the repository.
2. Create a `.env` file in the `backend` directory with your OpenAI API key:

   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. Build and run the application:

   ```bash
   docker-compose up --build
   ```

4. Access the frontend at `http://localhost:3000`.

## Backend Endpoints

- `POST /api/chat`: Handles user messages and agent responses.
- `GET /api/session/{session_id}`: Retrieves conversation history.
- `GET /api/profile/{user_id}`: Retrieves user profile.
- `PUT /api/profile/{user_id}`: Updates user profile.

## Frontend

- Chat interface for interacting with the agent.
- Displays chat history and responses.

## Project Structure

- **Backend**:
  - `services/`: Business logic (user profiles, conversation history, LangGraph workflow).
  - `tools/`: Tool implementations (gas exported quantity, JSON history search).
  - `main.py`: FastAPI app entry point.

- **Frontend**:
  - `src/`: React components and styles.
  - `vite.config.ts`: Vite configuration.

## Example Prompts

- "How much was the exported gas quantity to Ukraine in the last 12 months?"
- "From now on, answer in English."
- "Reset context."
- "Search our past conversations for 'gas quantity'."

## SOLID Principles

- **Single Responsibility**: Each module handles a specific concern (e.g., user profiles, tools).
- **Open/Closed**: Tools can be extended without modifying existing code.
- **Liskov Substitution**: Interfaces allow interchangeable implementations.
- **Interface Segregation**: Clear separation of concerns in services and tools.
- **Dependency Inversion**: High-level modules depend on abstractions, not concrete implementations.

## License

MIT