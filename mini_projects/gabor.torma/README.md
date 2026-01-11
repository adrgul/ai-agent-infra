# MeetingAI

**MeetingAI** is an intelligent system designed to automate the post-meeting workflow. It analyzes raw meeting transcripts using generative AI agents to produce structured, actionable outputs, separating note-taking from task management and summarization.

## ✨ Features

- **🤖 Multi-Agent AI Workflow**: Leverages LangGraph to orchestrate specialized agents (Note Taker, Task Assigner, Summarizer) for comprehensive meeting analysis.
- **📄 Multi-Format Support**: Seamlessly processes text files (`.txt`, `.md`), Word documents (`.docx`), and Subtitle files (`.srt`).
- **📝 Structured Outputs**: distinct separation of concerns—automated **Executive Summaries**, **Actionable Tasks** (w/ priority & owner), and **Key Usage Notes**.
- **🔍 RAG & Semantic Search**: Built-in Retrieval-Augmented Generation (ChromaDB) allows you to search across your past meetings semantically.
- **🛡️ Prevent Idempotency**: Uses SHA-256 hashing to detect duplicate uploads, preventing redundant processing to save costs and maintain data integrity.
- **🎨 Modern UI**: Clean, responsive React frontend with drag-and-drop file upload and Markdown rendering.
- **🐳 Docker Native**: Fully containerized environment for consistent deployment.

## 📚 Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **AI Orchestration**: LangGraph
- **LLM Integration**: LangChain + OpenAI (GPT-4o)
- **Database**: ChromaDB (Vector Store)
- **Data Validation**: Pydantic
- **Containerization**: Docker

### Frontend
- **Framework**: React 19
- **Build Tool**: Vite 5
- **Styling**: Vanilla CSS / Standard Vite styles
- **Icons**: Lucide React
- **Markdown**: React Markdown

## ⚙️ Technical Requirements

To run this project, you will need:
- **Docker & Docker Compose**
- **OpenAI API Key** (Required for the AI functionality)

## 🐳 Docker (Recommended)

The entire system is containerized and orchestrated using `docker-compose`. This ensures all services start with the correct configuration and networking.

1. **Configure Environment**
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   Then edit the `.env` file to add your actual OpenAI API Key:
   ```bash
   OPENAI_API_KEY=sk-your-api-key-here
   ```

2. **Run the System**
   Execute the following command in the project root:
   ```bash
   docker-compose up --build
   ```

3. **Access the Application**
   - **Frontend**: http://localhost:3000
   - **Backend API**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs

## 🚀 Usage

1. Open the frontend application in your browser.
2. **Upload a Transcript**: Drag and drop a `.txt` file containing your meeting transcript into the upload area.
   *   Supported formats: `.txt`, `.md`, `.docx`, `.srt`.
3. **Processing**: The system will process the file through the AI agents (Note Taker, Task Assigner, Summarizer).
4. **View Results**: Once complete, you will see:
   - **Executive Summary**: A high-level overview of the meeting.
   - **Tasks**: Actionable items with assignees and priorities.
   - **Notes**: Key decisions and points discussed.

## 🧪 Testing

### Mock Data
The project includes a `mock_data` directory containing sample meeting transcripts. You can use these files to test the system's capabilities without needing real meeting data.

### Backend Scripts
The `backend/scripts` directory contains utility scripts for testing specific components. 
Ensure the backend server is running (e.g., via Docker) before running the API tests.

- `test_api.py`: Tests the core API endpoints including transcript processing.
- `test_rag.py`: Tests the RAG (Retrieval-Augmented Generation) logic directly (bypassing API).
- `test_search.py`: Tests the semantic search and meeting listing endpoints.
- `generate_docx.py`: Utility for generating sample docx files.

To run a script (from the `backend` directory):
```bash
# Test API endpoints
python -m scripts.test_api

# Test Search Capability
python -m scripts.test_search

# Test RAG logic
python -m scripts.test_rag
```
