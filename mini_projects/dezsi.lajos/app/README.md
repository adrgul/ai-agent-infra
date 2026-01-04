# MedicalSupportAI (Pharma CRM Triage Agent)

A specialized AI agent for medical/pharmaceutical support triage, capable of categorizing tickets (Tier 1-3) and drafting policy-compliant responses using Google's AI stack.

## Architecture

- **Backend**: Python (FastAPI), LangGraph, Google Gemini, Qdrant.
- **Frontend**: React (Vite), TailwindCSS.
- **Protocol**: REST API.

## Prerequisites

- Docker & Docker Compose (optional)
- Node.js 18+
- Python 3.11+
- Google Cloud API Key (AI Studio or Vertex AI)

## Setup & Running

### 🐳 The Quick Way: Docker Compose (Recommended)

Run the entire application (frontend + backend) with a single command:

1. **Configure API Key**: 
   Ensure `backend/.env` exists and contains your `GOOGLE_API_KEY`.
   ```bash
   # From the app directory
   cp backend/.env.example backend/.env
   # Edit backend/.env and add your key
   ```

2. **Run with Compose**:
   ```bash
   docker-compose up --build
   ```
   - **Frontend**: `http://localhost:80` (or `http://localhost`)
   - **Backend API**: `http://localhost:8000`

---

### 🛠️ Manual Setup (Development)

#### 1. Backend Setup
1. Navigate to `backend`:
   ```bash
   cd backend
   ```
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure Environment:
   Copy `.env.example` to `.env` and add your key.
5. Run Server:
   ```bash
   uvicorn main:app --reload
   ```

#### 2. Frontend Setup
1. Navigate to `frontend`:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run Development Server:
   ```bash
   npm run dev
   ```
   App runs at `http://localhost:5173`.

### 3. Usage

1. Open the application URL.
2. Click the **"Seed Knowledge Base"** button (database icon) to load sample medical policies.
3. Type a medical support query (e.g., "I cannot login to the CLM app").
4. Observe the agent's response and the **Debug Panel** with triage decisions.
