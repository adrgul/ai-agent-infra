# 🌍 City Briefing Agent

An intelligent full-stack AI agent that generates personalized city briefings with Wikipedia facts, nearby points of interest filtered by activity preferences, and activity-aware insights.

**Languages**: 🇭🇺 Hungarian UI | 🇬🇧 Fully localized

## ⚡ Quick Start (3 Steps)

### 1️⃣ Copy Environment File & Add OpenAI API Key


In the Backend library, edit `.env.rename` and add your OpenAI API key, and rename it to .env

In the Frontend library, rename `.env.rename` to .env this is a public API


### 2️⃣ Run the Application

```bash
bash start.sh
```

This script will:
- Kill any existing processes on ports 3000 & 5173
- Start backend (port 3000)
- Start frontend (port 5173)

### 3️⃣ Open in Browser

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:3000
- **API Docs**: http://localhost:3000/docs

---

## 🚀 Running from GitHub

If you cloned from GitHub, follow these additional steps:

```bash
# 1. Clone repository
git clone https://github.com/Global-rd/ai-agents-hu.git
cd ai-agents-hu/mini_projects/gabor.toth/1_hw

# 2. Create environment file
cp .env.sample .env

# 3. Add your OpenAI API key
nano .env
# OPENAI_API_KEY=sk-...

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Install frontend dependencies
cd frontend
npm install
cd ..

# 6. Run the app
bash start.sh
```

---

## ✨ Features

- 🇭🇺 **Hungarian Interface** - Fully localized UI (város, aktivitás, tájékoztató)
- 📍 **Activity-Aware Recommendations** - Filters points of interest by user's desired activity
  - Sport (swimming, tennis, gym, martial arts, etc.)
  - Tourism (museums, viewpoints, castles, galleries, theatres)
  - Amenities (cafes, restaurants, pubs, libraries, cinemas)
  - Leisure (parks, playgrounds, sports centers, stadiums)
  - Shopping (supermarkets, clothing, books, toys, sports)
- 📚 **Wikipedia Integration** - Smart filtering of city facts based on user activity
- 🗺️ **OpenStreetMap POI Discovery** - Real nearby places with distances
- 🏛️ **City Knowledge** - Curated city facts and historical information
- 💾 **History Tracking** - Last 20 briefings saved locally
- ⚡ **Retry Logic** - Smart Overpass API handling with 3-attempt retry system

## 🏗️ Architecture

**Design Pattern**: Hexagonal Architecture (Ports & Adapters)

```
Domain Layer
├─ Models (data structures)
└─ Ports (abstract interfaces)

Application Layer
├─ BriefingService (orchestration)
└─ AgentOrchestrator (pipeline)

Infrastructure Layer (Adapters)
├─ HTTP Client (with retry logic)
├─ Geocoding (Nominatim - OpenStreetMap)
├─ Places (Overpass QL - OpenStreetMap)
├─ Knowledge (Wikipedia)
├─ LLM (OpenAI GPT-4o-mini)
└─ Persistence (JSON file-based)

Interfaces Layer
└─ API (FastAPI routes)
```

## 📋 Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.9+)
- **HTTP**: httpx with retry logic (tenacity)
- **Validation**: Pydantic
- **Storage**: File-based JSON
- **External APIs**: Nominatim, Overpass, Wikipedia, OpenAI

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: TailwindCSS
- **State**: React Query (@tanstack/react-query)
- **HTTP**: Axios

### Infrastructure
- **Containerization**: Docker & Docker Compose (optional)
- **Web Server**: Uvicorn (backend), Vite dev server (frontend)
- **Package Manager**: pip (Python), npm (Node.js)

---

## 🔌 API Endpoints

### Generate City Briefing
```http
GET /api/briefing?city=budapest&activity=sport
```

**Query Parameters:**
- `city` (required): City name (e.g., "Budapest", "Paris")
- `activity` (optional): User's desired activity (e.g., "sport", "museum", "cafe")

**Response Example:**
```json
{
  "city": "Budapest",
  "coordinates": { "lat": 47.4979, "lon": 19.0402 },
  "briefing": {
    "paragraph": "Budapest is Hungary's capital..."
  },
  "city_facts": [
    { "title": "Budapest", "content": "Capital city..." }
  ],
  "nearby_places": [
    {
      "name": "Gellért Fürdő",
      "type": "sport=swimming",
      "lat": 47.486,
      "lon": 19.024
    }
  ],
  "fallback_message": null,
  "metadata": {
    "generated_at": "2025-12-22T10:30:00Z"
  }
}
```

### Get Briefing History
```http
GET /api/history?limit=10
```

Returns last N briefings (default 20).

### Health Check
```http
GET /health
```

---

## 📁 Project Structure

```
1_hw/
├── backend/
│   ├── app/
│   │   ├── config/settings.py          # Configuration (Pydantic)
│   │   ├── domain/
│   │   │   ├── models.py               # Data models
│   │   │   └── ports.py                # Abstract interfaces
│   │   ├── application/
│   │   │   ├── briefing_service.py     # Main orchestration logic
│   │   │   └── agent_orchestrator.py   # Pipeline execution
│   │   ├── infrastructure/
│   │   │   ├── http/client.py          # Async HTTP with retries
│   │   │   ├── geocoding/nominatim.py  # City coordinates
│   │   │   ├── places/overpass.py      # POI discovery (3 retry attempts)
│   │   │   ├── knowledge/wikipedia.py  # City facts
│   │   │   ├── llm/openai_llm.py       # OpenAI integration
│   │   │   └── persistence/history_repo.py # JSON storage
│   │   ├── interfaces/api/routes.py    # FastAPI endpoints
│   │   └── main.py                     # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts               # Axios API client
│   │   │   └── types.ts                # TypeScript interfaces
│   │   ├── hooks/useBriefing.ts        # React Query hooks
│   │   ├── components/
│   │   │   ├── BriefingForm.tsx        # City + activity input
│   │   │   ├── BriefingView.tsx        # Briefing display
│   │   │   └── Cards.tsx               # City facts & places
│   │   ├── App.tsx                     # Main component
│   │   ├── main.tsx                    # Entry point
│   │   └── index.css                   # Tailwind styles
│   ├── package.json
│   └── Dockerfile
│
├── data/                                # JSON history storage
├── .env                                 # Environment variables
├── .env.sample                          # Environment template
├── start.sh                             # Launch script
└── README.md                            # This file
```

---

## 🎯 How It Works

### 1. User Input
User enters city name (e.g., "Budapest") and desired activity (e.g., "sport=swimming")

### 2. City Briefing Generation
The system:
1. **Geocodes** city → coordinates via Nominatim
2. **Discovers Places** → queries Overpass for nearby POIs matching activity (with retry logic)
3. **Fetches Facts** → retrieves Wikipedia city facts, filters by activity relevance
4. **Generates Briefing** → OpenAI creates personalized narrative
5. **Saves History** → stores briefing in JSON file

### 3. Display
Frontend shows:
- City facts (filtered by activity)
- Nearby places (with walking distances)
- AI-generated briefing text
- Previous briefings in history tab

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```bash
# 🔑 OpenAI API Key (required for AI briefings)
OPENAI_API_KEY=sk-your-key-here

# 🌍 External API URLs (defaults provided)
NOMINATIM_URL=https://nominatim.openstreetmap.org
OVERPASS_URL=https://overpass-api.de/api/interpreter
WIKIDATA_URL=https://query.wikidata.org/sparql

# 🖥️ Server Configuration
API_HOST=0.0.0.0
API_PORT=3000
LOG_LEVEL=INFO

# 📊 Application Settings
DATA_DIR=./data
MAX_HISTORY_ENTRIES=20
```

---

## 🔧 Development

### Backend Development
```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Run Both Simultaneously
```bash
bash start.sh
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| **Port already in use** | Kill process: `lsof -ti:3000,5173 \| xargs kill -9` |
| **City not found** | Use English city names, check spelling |
| **No OpenAI key error** | Add `OPENAI_API_KEY` to `.env` |
| **Slow API response** | Overpass queries can timeout; retry or try different city |
| **No nearby places found** | Some cities have limited POI data; check Overpass directly |
| **npm command not found** | Install Node.js from nodejs.org |
| **python command not found** | Install Python 3.9+ from python.org |

---

## 📦 Dependencies

### Backend
- fastapi 0.109.0
- uvicorn 0.27.0
- httpx 0.25.2
- pydantic 2.5.2
- tenacity 8.2.3 (retry logic)
- openai 1.6.1

### Frontend
- react 18.2.0
- react-dom 18.2.0
- @tanstack/react-query 5.28.0
- axios 1.6.2
- tailwindcss 3.4.1

---

## 🚦 Retry Logic

The backend implements intelligent retry handling for Overpass API queries:
- **Max Attempts**: 3
- **Retry Delay**: 2 seconds between attempts
- **Timeout**: 30 seconds per request
- **Trigger**: When 0 results returned (allows Overpass time to process)

---

## 🗺️ Activity Recognition & OSM Conversion

### How It Works

The activity field is **free text input** - users can type anything naturally (e.g., "swimming", "coffee shop", "hiking"):

1. **User Input** (free text) → "I want to swim"
2. **OpenAI Processing** → Analyzes intent and converts to OpenStreetMap (OSM) tags
3. **OSM Query** → Searches for relevant places using standardized keys
4. **Results** → Returns filtered nearby places and Wikipedia facts

### Example Conversions

```
User Input              → OSM Key Conversion        → Query Result
────────────────────────────────────────────────────────────────
"swimming"             → leisure=swimming_pool      → Find pools, thermal baths
"coffee shop"          → amenity=cafe               → Find cafes, coffee shops
"hiking trails"        → leisure=track              → Find walking paths, trails
"art museum"           → tourism=museum             → Find museums, galleries
"running"              → sport=running              → Find running tracks, paths
"shopping"             → shop=supermarket           → Find shops, malls
"sports activities"    → sport=*                    → Find all sports facilities
"thermal baths"        → leisure=thermal_bath       → Find thermal bathhouses
```

### Supported OSM Categories

| Category | OSM Tag Format | Examples |
|----------|----------------|----------|
| **leisure** | `leisure=*` | park, track, playground, swimming_pool, sports_centre, stadium |
| **sport** | `sport=*` | swimming, soccer, tennis, gym, martial_arts, running |
| **tourism** | `tourism=*` | museum, viewpoint, artwork, castle, monument, gallery, theatre |
| **amenity** | `amenity=*` | cafe, restaurant, pub, bar, library, theatre, cinema, parking |
| **shop** | `shop=*` | supermarket, mall, clothing, food, books, toys, sports |

### Behind the Scenes

When you enter an activity:

```
User: "Szeretnék úszni Budapesten"
      ↓
OpenAI LLM Analysis
├─ Language: Hungarian
├─ Intent: Swimming activity
└─ OSM Mapping: leisure=swimming_pool
      ↓
Overpass Query: [out:json];nwr["leisure"="swimming_pool"](...);out;
      ↓
Results: Gellért Fürdő, Széchenyi Thermal Bath, Rudas Thermal Bath
      ↓
Wikipedia Filtering: "Relevans swimming-hez: ..."
      ↓
Display: Activity-specific briefing with nearest pools
```

> **Note**: This allows natural language input while maintaining accuracy with OpenStreetMap's standardized tagging system

---

## 📝 Example Usage

### Get Budapest Sports Briefing
```bash
curl "http://localhost:3000/api/briefing?city=budapest&activity=sport=swimming"
```

### Get Paris Museum Facts
```bash
curl "http://localhost:3000/api/briefing?city=paris&activity=tourism=museum"
```

### View Previous Briefings
```bash
curl "http://localhost:3000/api/history?limit=5"
```

---

## 🎓 Learning Resources

- **OpenStreetMap/Overpass**: https://wiki.openstreetmap.org/wiki/Overpass_API
- **Nominatim Geocoding**: https://nominatim.org/
- **Wikipedia API**: https://en.wikipedia.org/w/api.php
- **OpenAI API**: https://platform.openai.com/docs/api-reference

---

## 🚦 RELEASE OF PORTS WORKS WITH YOUR OWN USER PASSWORD!

## 📄 License

MIT License

## 👤 Author

City Briefing Agent - Intelligent city insights powered by OpenAI and OpenStreetMap
