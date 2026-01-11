# MeetingAI Backend Documentation

## Overview

The MeetingAI Backend is a **FastAPI** application designed to process meeting transcripts using advanced AI agents. It leverages **LangGraph** to orchestrate a workflow of specific agents that extract notes, identify tasks, and generate comprehensive summaries.

## Technology Stack

- **Framework**: FastAPI (Python 3.9+)
- **AI Orchestration**: LangGraph
- **LLM Integration**: LangChain + OpenAI (GPT-4o)
- **Data Validation**: Pydantic
- **Containerization**: Docker

## Architecture

The backend operates on a specialized graph workflow defined in `graph.py` and implemented in `nodes.py`.

### The Workflow

The processing pipeline follows a directed graph structure:

1.  **Input**: A raw text transcript is received via the API.
2.  **Processing Nodes** (Agents):
    *   **Note Taker**: Analyzes the transcript to extract key points and formal decisions.
    *   **Task Assigner**: Identifies actionable items, assigns owners, sets priorities, and determines due dates.
    *   **Summarizer**: Synthesizes the extracted notes and tasks into a high-level executive summary in Markdown format.
3.  **Output**: A structured JSON response containing the summary, actionable tasks, and structured notes.

### specific Agents

#### 1. Note Taker (`nodes.py`)
- **Role**: Expert meeting secretary.
- **Function**: Filters noise and chit-chat to extract factual information.
- **Output Model**: `MeetingNotes` (Key Points, Decisions).

#### 2. Task Assigner (`nodes.py`)
- **Role**: Project Manager.
- **Function**: Scans for commitments and assignments. Defaults unassigned tasks to "Unassigned".
- **Output Model**: List of `Task` objects (Title, Assignee, Priority, Due Date).

#### 3. Summarizer (`nodes.py`)
- **Role**: Professional Technical Writer.
- **Function**: Generates a final report based *strictly* on the outputs of the Note Taker and Task Assigner (not the raw transcript), ensuring consistency.

## API Reference

### Base URL
`http://localhost:8000` (Default)

### Endpoints

#### `GET /`
**Description**: Health check endpoint to verify the API is running.
- **Response**: `{"message": "MeetingAI API is running"}`

#### `POST /process`
**Description**: Uploads a meeting transcript for processing.
- **Request**: `multipart/form-data`
    - `file`: The transcript text file (`.txt`).
- **Response** (JSON):
    ```json
    {
      "summary": "# Executive Summary...",
      "notes": [
        "Key Point: Discussed Q4 goals",
        "Decision: Budget increased by 10%"
      ],
      "tasks": [
        {
          "title": "Update roadmap",
          "assignee": "Alice",
          "priority": "High",
          "due_date": "2023-11-01"
        }
      ]
    }
    ```

## Setup & Development

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- OpenAI API Key

### Local Installation

1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Set up environment variables:
    Create a `.env` file in the project root:
    ```env
    OPENAI_API_KEY=your_key_here
    ```
4.  Run the server:
    ```bash
    fastapi dev main.py
    ```

### Docker Usage

The backend is configured to run effortlessly via Docker Compose from the root directory:

```bash
docker-compose up --build backend
```
