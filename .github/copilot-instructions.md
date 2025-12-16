<!-- Copilot instructions for AI coding agents working in this repository -->
# Quick Orientation for AI Coding Agents

This repository is an example AI Agent demo with a Python FastAPI backend and React + TypeScript frontend. Use these notes to be immediately productive and avoid guessing project-specific rules.

- **Architecture (high level)**: layered FastAPI backend (see `backend/`):
  - `domain/` — Pydantic models & interfaces (pure business logic).
  - `infrastructure/` — concrete implementations (file repositories, HTTP tool clients).
  - `services/` — orchestration: `agent.py` (LangGraph), `tools.py`, `chat_service.py`.
  - `main.py` — application entry, lifespan initializes repos, tools and agent.

- **Where to look for authoritative behavior**:
  - Agent decision format & rules: `backend/services/agent.py` (the LLM MUST return JSON-only decisions; examples present in `_agent_decide_node`).
  - Tool contracts / return shape: `backend/services/tools.py` (each `execute(...)` returns a dict with `success`, `data`, and `system_message`).
  - App wiring & runtime checks: `backend/main.py` (OpenAI API key requirement, lifecycle setup).
  - Docs for architecture & quickstart: `docs/ARCHITECTURE.md`, `docs/QUICKSTART.md`, `docs/INIT_PROMPT.md`.

- **Important runtime commands** (what humans use):
  - Recommended (Docker): `docker-compose up --build` (root or service folder with `docker-compose.yml`).
  - Local dev script: `./start-dev.sh` (bash). If working on Windows, run it from WSL / Git Bash or use Docker Compose.
  - Required env: `OPENAI_API_KEY` (backend refuses to start without it).

- **Persistence & data layout**:
  - Conversation histories: `data/sessions/` (JSON files; append every message).
  - User profiles: `data/users/` (JSON; never delete programmatically; can be updated).
  - Files saved by agents: `data/files/{user_id}/`.
  - Code expects these folders to exist (see `start-dev.sh` creating them).

- **Agent / LangGraph conventions you must preserve**:
  - Decision JSON: the LLM output consumed by `agent_decide` must be strictly JSON. The agent code strips code fences and parses JSON (see `_agent_decide_node`).
  - `action` field: MUST be one of `"call_tool"` or `"final_answer"`.
  - When `action == "call_tool"`, include `tool_name` and `arguments`.
  - Never call the same tool with identical arguments twice for one turn — the agent enforces this rule.
  - A tool call appends a `SystemMessage` describing the observation; tools return `system_message` for this purpose.
  - File creation tool requires `user_id` in arguments (agent injects it for `create_file`).

- **Tool behavior & names** (use exact keys):
  - `weather`, `geocode`, `ip_geolocation`, `fx_rates`, `crypto_price`, `create_file`, `search_history`.
  - Each `Tool.execute` is `async` and returns `{ "success": bool, "data": ..., "system_message": str }` or an error variant.

- **Special flows to respect**:
  - `reset context` (case-insensitive): detected early in `ChatService.process_message()` and must clear the session history file but preserve the user profile. If you change behavior, update docs and `main.py` wiring.
  - Memory model: `memory` includes `chat_history` (last N messages), `preferences` (from user profile), `workflow_state` (for multi-step flows). See `docs/ARCHITECTURE.md` and `services/agent.py` for examples.

- **Testing & extension rules**:
  - To add a new tool: implement `I*Client` in `infrastructure/tool_clients.py`, add a Tool wrapper in `services/tools.py`, register it in `main.py` and in `AIAgent.__init__()` (preserve tool key names).
  - Keep controllers thin — business logic belongs in `services/`.

- **Small examples to copy/paste**:
  - Decision JSON example (from `agent.py`):
    ```json
    {"action":"call_tool","tool_name":"weather","arguments":{"city":"Budapest"},"reasoning":"get weather forecast"}
    ```
  - Final answer example:
    ```json
    {"action":"final_answer","reasoning":"all tasks completed"}
    ```

- **When changing code**:
  - If you change the LLM decision format, update `services/agent.py` and the docs in `docs/INIT_PROMPT.md` (these are authoritative).
  - If you add dependencies, update `backend/requirements.txt` (and Dockerfile) or `ai_agent_intro/backend/pyproject.toml` where applicable.

If anything here is unclear or you want me to expand a specific section (examples, more file snippets, or a brief checklist for PR reviewers), tell me which part to expand. 