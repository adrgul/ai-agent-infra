# City Briefing Agent - Startup Guide

## Prerequisites
- Python 3.9+ (backend)
- Node.js 18+ (frontend)
- OpenAI API key
- macOS/Linux/Windows

## Quick Start (Bash Script)

### 1. Set OpenAI API Key
```bash
# Add to .env file in project root
echo "OPENAI_API_KEY=sk-..." >> .env
```

### 2. Run Everything
```bash
cd /Users/tothgabor/Desktop/ai-agents-hu/mini_projects/gabor.toth/1_hw
bash start.sh
```

This starts both backend and frontend automatically.

Services will be available at:
- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:3000
- **API Docs**: http://localhost:3000/docs

## Manual Startup (Alternative)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 3000
```

### Frontend Setup (in new terminal)
```bash
cd frontend
npm install
npm run dev
```

## Using the Application

### 1. Open Frontend
Navigate to: http://localhost:5173

### 2. Generate a Briefing
- Enter a city name (e.g., "Budapest", "Paris", "Tokyo")
- Select an activity (parks, cafes, museums, sport, hiking)
- Click "Generate Briefing"

### 3. View Results
- Personalized activity-aware brief
- Relevant Wikipedia facts filtered by activity
- Nearby places based on activity preference
- AI-generated narrative with recommendations

### 4. Check History
Click "History" tab to see previously generated briefings

## API Endpoints

### GET /api/briefing
Generate an activity-aware city briefing

**Parameters:**
- `city` (required): City name
- `activity` (required): Activity type (parks, cafes, museums, sport, hiking)

**Example:**
```bash
curl "http://localhost:3000/api/briefing?city=budapest&activity=parks"
```

**Response:**
```json
{
  "city_name": "Budapest",
  "activity": "parks",
  "briefing": "Personalized briefing text...",
  "wikipedia_summary": "Relevant facts filtered for parks...",
  "nearby_places": [...],
  "suggested_activities": [...]
}
```

### GET /api/history
Get briefing history

**Example:**
```bash
curl "http://localhost:3000/api/history?limit=10"
```

### GET /health
Health check endpoint

## Stopping the Application
```bash
# If using bash start.sh: Press Ctrl+C
# If running separately: Kill both terminals
```

## Troubleshooting

### Backend won't start: "Port 3000 already in use"
```bash
# Kill existing process
lsof -ti:3000 | xargs kill -9
# Then restart
python -m uvicorn app.main:app --host 0.0.0.0 --port 3000
```

### Frontend won't start: "Port 5173 already in use"
```bash
# Kill existing process
lsof -ti:5173 | xargs kill -9
# Then restart
npm run dev
```

### OPENAI_API_KEY not found
- Make sure `.env` file exists in project root with `OPENAI_API_KEY=sk-...`
- Check that you added the key correctly (no extra spaces)

### No briefing generated
- Ensure the city name is spelled correctly
- Ensure the activity type is valid (parks, cafes, museums, sport, hiking)
- Check backend logs for error details

### ModuleNotFoundError in backend
```bash
cd backend
pip install -r requirements.txt
```

## Architecture

```
Activity-Aware City Briefing
├── Frontend (React 18 + TypeScript + Vite)
│   ├── BriefingForm: City + Activity inputs
│   ├── BriefingView: Display results
│   └── Cards: Activity facts, nearby places
│
└── Backend (FastAPI + Python)
    ├── Nominatim: Geocoding (lat/lon)
    ├── Wikipedia: City facts (activity-filtered)
    ├── Overpass API: POI discovery (nearby_places)
    ├── OpenAI: Briefing generation + fact filtering
    └── History: JSON persistence
```

## Key Features

- **Activity-Aware Filtering**: Wikipedia facts filtered by selected activity
- **Nearby Places**: OSM POIs (5 categories: leisure, sport, tourism, amenity, shop)
- **Personalized Briefings**: OpenAI generates custom narratives per activity
- **Retry Logic**: Automatic retry (3 attempts, 2s delays, 30s timeout)
- **Response Caching**: History storage for quick access
- **Hungarian Interface**: All labels in Hungarian

## Environment Variables

Create `.env` file in project root:
```bash
OPENAI_API_KEY=sk-...  # Required for briefing generation
BACKEND_URL=http://localhost:3000  # For frontend API calls
```

## Learning Resources

- **Backend Structure**: See `backend/app/` (Hexagonal Architecture)
- **Frontend Components**: See `frontend/src/components/`
- **API Details**: Open http://localhost:3000/docs while backend is running
