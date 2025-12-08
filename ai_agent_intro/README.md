# 🤖 AI Weather Agent

A containerized full-stack AI agent application that generates personalized daily weather briefings with outfit recommendations and activity suggestions.

## 🏗️ Architecture

```
┌─────────────────┐
│  React Frontend │  (Vite + TypeScript + TailwindCSS)
│   Port 5173     │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│ FastAPI Backend │  (Python 3.11 + SOLID-ish architecture)
│   Port 8000     │
└────────┬────────┘
         │
    ┌────┴─────┬──────────┬──────────┐
    │          │          │          │
    ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Nominatim│ │Open-   │ │OpenAI  │ │File    │
│Geocoding│ │Meteo   │ │LLM     │ │Storage │
│         │ │Weather │ │        │ │(JSON)  │
└─────────┘ └────────┘ └────────┘ └────────┘
```

### Stack

**Backend:**
- Python 3.11+ with FastAPI
- Libraries: `httpx`, `pydantic`, `tenacity`, `python-dotenv`, `uvicorn`, `loguru`
- Testing: `pytest`, `ruff`, `mypy`

**Frontend:**
- React 18+ with TypeScript
- Vite build tool
- TanStack Query (React Query)
- TailwindCSS for styling

**AI & APIs:**
- **LangGraph** for graph-based agent orchestration (see [LANGGRAPH.md](./LANGGRAPH.md))
- OpenAI GPT (configurable model)
- Nominatim (OpenStreetMap geocoding)
- Open-Meteo (weather forecasts)

**Containerization:**
- Multi-stage Docker builds for minimal images
- Docker Compose orchestration
- Shared network and bind-mounted volumes

### Backend Architecture (SOLID-ish)

```
backend/app/
├── domain/           # Business entities, interfaces
├── application/      # Use cases, agent orchestration
├── infrastructure/   # External service implementations
│   ├── http/        # HTTP client
│   ├── geocoding/   # Nominatim
│   ├── weather/     # Open-Meteo
│   ├── llm/         # OpenAI
│   └── persistence/ # File-based JSON storage
├── interfaces/      # API routes, dependency injection
├── config/          # Settings management
└── utils/           # Logging, helpers
```

**Key Patterns:**
- Dependency Injection via container
- Protocol-based abstractions (`GeocodingService`, `WeatherService`, `LLMService`, `HistoryRepository`)
- Agent loop: Goal → Plan → Act (tools) → Observe → Reflect
- Validated JSON responses with Pydantic

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- OpenAI API key

### Run the Application

1. **Clone and configure:**

```bash
# Copy environment template
cp .env.sample .env

# Edit .env and set your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

2. **Start all services:**

```bash
chmod +x scripts/start.sh scripts/down.sh
./scripts/start.sh
```

The script will:
- Build Docker images for backend and frontend
- Start both services with health checks
- Create the `data/` directory for persistence

3. **Access the application:**

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Stop the Application

```bash
./scripts/down.sh
```

## 📡 API Reference

### Get Weather Briefing

```bash
GET /api/briefing?city=Budapest&date=2025-11-18
```

**Query Parameters:**
- `city` (required): City name to get weather for
- `date` (optional): ISO-8601 date (defaults to today)

**Example Response:**

```json
{
  "city": "Budapest",
  "country": "Hungary",
  "coordinates": {
    "lat": 47.4979,
    "lon": 19.0402
  },
  "date": "2025-11-18",
  "weather": {
    "temperature_min": 8.5,
    "temperature_max": 14.2,
    "wind_speed": 3.5,
    "precipitation_probability": 20
  },
  "briefing": {
    "summary": "Expect a mild autumn day with partly cloudy skies and a low chance of rain.",
    "outfit": "Layer up with a light jacket, jeans, and comfortable walking shoes. Bring a small umbrella just in case.",
    "activities": [
      "Take a scenic walk along the Danube riverside",
      "Visit the Hungarian National Museum",
      "Enjoy a coffee at a traditional Budapest café"
    ],
    "note": null
  },
  "timestamp": "2025-11-17T10:30:45.123456"
}
```

### Get Request History

```bash
GET /api/history
```

Returns the last 20 briefing requests.

### Health Check

```bash
GET /health
```

Returns `{"status": "healthy"}` when the service is ready.

## 🧪 Development

### Run Backend Tests

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
pytest
```

### Local Development (without Docker)

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp ../.env.sample ../.env  # configure
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## ⚙️ Configuration

All configuration is managed through environment variables (see `.env.sample`):

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4o-mini` |
| `USE_LANGGRAPH` | Enable LangGraph agent (true/false) | `true` |
| `NOMINATIM_BASE` | Nominatim API base URL | `https://nominatim.openstreetmap.org` |
| `OPENMETEO_BASE` | Open-Meteo API base URL | `https://api.open-meteo.com/v1` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DATA_DIR` | Directory for JSON persistence | `/app/data` |
| `VITE_API_BASE` | Frontend API base URL | `http://localhost:8000` |

**NEW:** Set `USE_LANGGRAPH=true` to enable graph-based agent orchestration. See [LANGGRAPH.md](./LANGGRAPH.md) for details on the LangGraph integration, benefits, and architecture.

## 📝 Data Persistence

- **No database required** – uses simple JSON file storage
- Request history stored in `data/history.json` (last 20 entries)
- Atomic writes ensure data integrity
- Volume-mounted in Docker for persistence across container restarts

## ⚠️ Important Notes

### API Rate Limits & Terms of Service

**Nominatim (OpenStreetMap):**
- Free geocoding service
- **Required:** Set `User-Agent` header (implemented)
- Rate limit: ~1 request/second
- [Usage Policy](https://operations.osmfoundation.org/policies/nominatim/)

**Open-Meteo:**
- Free weather API, no API key required
- Rate limit: ~10,000 requests/day
- [Terms of Service](https://open-meteo.com/en/terms)

**OpenAI:**
- Requires API key and credits
- Costs vary by model (gpt-4o-mini is cost-effective)
- [Pricing](https://openai.com/pricing)

### Weather Forecast Accuracy

- Open-Meteo provides forecasts up to 16 days
- Accuracy decreases for dates further in the future
- The AI briefing includes uncertainty notes for dates >7 days ahead

## 🐛 Troubleshooting

**Backend won't start:**
- Check `.env` file exists and `OPENAI_API_KEY` is set
- Verify `data/` directory has write permissions
- Check logs: `docker compose logs backend`

**Frontend can't reach backend:**
- Ensure backend health check passes: `curl http://localhost:8000/health`
- Check `VITE_API_BASE` in `.env` is correct
- Verify both containers are on the same network: `docker network inspect aiagent_net`

**OpenAI errors:**
- Verify API key is valid
- Check you have sufficient credits
- Try a different model in `.env` (e.g., `gpt-3.5-turbo`)

## 📄 License

MIT

## 🙏 Acknowledgments

- [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/) for geocoding
- [Open-Meteo](https://open-meteo.com/) for weather data
- [OpenAI](https://openai.com/) for AI capabilities
