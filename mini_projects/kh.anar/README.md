# 1. Házi feladat

- Az OpenAI API-t behívtam. 
- Próbáltam olyan promp-t írni amit majd a későbbi házifeladat utasításokkal lehet bővíteni, így a végére összeáll a kiválasztott mini projekt.

# KnowledgeRouter Chat (Homework Iteration)

Minimal LangGraph-orchestrated chat foundation for the AI Internal Knowledge Router & Workflow Automation Agent.

## Stack
- Backend: FastAPI, LangGraph, LangChain OpenAI
- Frontend: React (Vite) + UIkit
- Deployment: Docker, docker-compose

## Setup
1) Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
2) From `mini_projects/kh.anar` run:
   ```bash
   docker-compose up --build
   ```
3) Open http://localhost:4000 and start chatting.

## Behavior
- Conversation and user profile stored as JSON under `data/`.
- `reset context` command clears session conversation history only.
- Debug sidebar shows request JSON, user/session IDs, query, RAG context, and final LLM prompt.
  The default model is set to `gpt-4o-mini` in `backend/app/core/config.py`; override with `OPENAI_MODEL` in your `.env` if needed.

## Development
- Backend dev server: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Frontend dev server (Vite): `npm install && npm run dev -- --host --port 3000`
