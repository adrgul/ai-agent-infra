# Deployment Útmutató

## 1. Lokális Fejlesztés (Development)

### 1.1 Gyors Start (Javasolt)

```bash
cd /Users/tothgabor/ai-agents-hu/mini_projects/gabor.toth/2_hw

# Backend start
cd backend
export OPENAI_API_KEY="sk-..."
python3.9 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend start (új terminal)
cd frontend
npm install && npm run dev
```

### 1.2 Szerver Portok

| Komponens | Port | URL |
|-----------|------|-----|
| Frontend | 5173 | http://localhost:5173 |
| Backend | 8000 | http://localhost:8000 |

## 2. Docker Deployment (Ajánlott)

### 2.1 Docker Compose (Gyors Start)

```bash
cd /Users/tothgabor/ai-agents-hu/mini_projects/gabor.toth/2_hw

# Environment változók beállítása
export OPENAI_API_KEY="sk-..."
export PYTHONUNBUFFERED=1

# Services indítása
docker-compose up --build

# Services leállítása
docker-compose down
```

**Kimenet:**
```
docker-compose up --build
Creating network "rag_default" with the default driver
Building backend
Building frontend

...

backend_1   | INFO:     Uvicorn running on http://0.0.0.0:8000
frontend_1  | ➜  Local:   http://localhost:5173/
```

### 2.2 Docker Compose Configuration

**docker-compose.yml struktura:**

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      PYTHONUNBUFFERED: 1
    volumes:
      - ./data:/app/data
    command: uvicorn main:app --host 0.0.0.0 --port 8000

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    volumes:
      - ./frontend/src:/app/src
    command: npm run dev

volumes:
  data:
```

### 2.3 Persistent Data Management

**Data Volume:**

```bash
# Data volume létrehozása
docker volume create rag-data

# Volume csatlakoztatása docker-compose-ban
volumes:
  data:
    driver: local

# Volume verifikálása
docker volume ls | grep rag-data
```

## 3. Production Deployment

### 3.1 Production Stack

```
Frontend (React):
  - Build: npm run build → dist/
  - Server: Nginx (reverse proxy, static serving)
  - Port: 80 (HTTP) / 443 (HTTPS)

Backend (FastAPI):
  - Server: Gunicorn + Uvicorn (workers)
  - Port: 8000 (internal)
  - Reverse proxy: Nginx
```

### 3.2 Production Docker Compose

**backend/Dockerfile (Production):**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Függőségek
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Data directories
RUN mkdir -p data/{users,sessions,uploads,derived}

# Gunicorn + Uvicorn
RUN pip install gunicorn

COPY . .

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]
```

**frontend/Dockerfile (Production):**

```dockerfile
# Build stage
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# Serve stage
FROM nginx:alpine

# Nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 3.3 Environment Variables (Production)

**Backend:**

```bash
# .env
OPENAI_API_KEY=sk-...
LOG_LEVEL=info
MAX_ACTIVITY_QUEUE_SIZE=1000
ACTIVITY_POLLING_INTERVAL=1000  # ms
```

**Frontend:**

```bash
# .env.production
VITE_API_URL=https://api.example.com
VITE_ACTIVITY_POLL_INTERVAL=1000  # ms
```

## 4. Cloud Deployment Opciók

### 4.1 Azure App Service

**Backend Deployment:**

```bash
# Create App Service Plan
az appservice plan create \
  --name rag-plan \
  --resource-group my-rg \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --name rag-backend \
  --resource-group my-rg \
  --plan rag-plan \
  --runtime "python|3.11"

# Configure environment
az webapp config appsettings set \
  --resource-group my-rg \
  --name rag-backend \
  --settings OPENAI_API_KEY=$OPENAI_API_KEY

# Deploy
az webapp deployment source config-zip \
  --resource-group my-rg \
  --name rag-backend \
  --src app.zip
```

**Frontend Deployment (Static Web Apps):**

```bash
# Create Static Web App
az staticwebapp create \
  --name rag-frontend \
  --resource-group my-rg \
  --location westeurope \
  --app-location "frontend" \
  --output-location "dist"
```

### 4.2 Azure Container Instances (ACI)

```bash
# Create container registry
az acr create \
  --resource-group my-rg \
  --name ragregistry \
  --sku Basic

# Build & push image
az acr build \
  --registry ragregistry \
  --image rag-backend:latest .

# Deploy backend
az container create \
  --resource-group my-rg \
  --name rag-backend \
  --image ragregistry.azurecr.io/rag-backend:latest \
  --environment-variables OPENAI_API_KEY=$OPENAI_API_KEY \
  --ports 8000 \
  --ip-address Public

# Deploy frontend
az container create \
  --resource-group my-rg \
  --name rag-frontend \
  --image ragregistry.azurecr.io/rag-frontend:latest \
  --ports 80 \
  --ip-address Public
```

### 4.3 Docker Hub

```bash
# Login
docker login

# Tag image
docker tag rag-backend:latest username/rag-backend:latest

# Push
docker push username/rag-backend:latest

# Deploy from Docker Hub
docker pull username/rag-backend:latest
docker run -d -p 8000:8000 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  username/rag-backend:latest
```

## 5. Scaling Stratégiák

### 5.1 Horizontal Scaling (Több instance)

**Backend Load Balancing:**

```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    listen 80;
    location /api/ {
        proxy_pass http://backend;
    }
}
```

**Docker Swarm (Multiple Nodes):**

```bash
# Initialize Swarm
docker swarm init

# Deploy service
docker service create \
  --name rag-backend \
  --replicas 3 \
  -p 8000:8000 \
  rag-backend:latest

# Scale dynamically
docker service scale rag-backend=5
```

### 5.2 Activity Logger Optimization (High Load)

**Cache Backend Activities:**

```python
# Redis caching
import redis

cache = redis.Redis(host='localhost', port=6379, db=0)

@app.get("/api/activities")
async def get_activities(count: int = 50):
    # Try cache first
    cached = cache.get(f"activities:{count}")
    if cached:
        return json.loads(cached)
    
    # Fetch & cache
    activities = await activity_callback.get_activities(count)
    cache.setex(f"activities:{count}", 1, json.dumps(activities))
    return {"activities": activities}
```

**WebSocket Real-Time (vs. Polling):**

```python
# WebSocket endpoint (reduces polling overhead)
@app.websocket("/ws/activities")
async def websocket_activities(websocket: WebSocket):
    await websocket.accept()
    while True:
        activities = await activity_callback.get_activities(100)
        await websocket.send_json({"activities": activities})
        await asyncio.sleep(1)
```

## 6. Database Optimization (Scale)

### 6.1 PostgreSQL + pgvector (vs. JSON)

**Backend:**

```python
import psycopg2
from pgvector.psycopg2 import register_vector

# Replace ChromaDB with pgvector
class PgvectorStore(VectorStore):
    def __init__(self, connection_string):
        self.conn = psycopg2.connect(connection_string)
        register_vector(self.conn)
    
    async def add_chunks(self, collection_name, chunks, embeddings):
        # Insert into PostgreSQL
        cursor = self.conn.cursor()
        for chunk, embedding in zip(chunks, embeddings):
            cursor.execute(
                "INSERT INTO chunks (collection, content, vector) VALUES (%s, %s, %s)",
                (collection_name, chunk.content, embedding)
            )
        self.conn.commit()
```

**Data Migration:**

```bash
# Export ChromaDB data
python scripts/export_chroma.py

# Import to PostgreSQL
psql -d rag_db -f data_export.sql
```

## 7. Monitoring & Logging

### 7.1 Application Insights (Azure)

```python
from opencensus.ext.azure.log_exporter import AzureLogHandler
import logging

handler = AzureLogHandler(
    connection_string='InstrumentationKey=<key>'
)
logger = logging.getLogger('rag')
logger.addHandler(handler)

# Log backend events
logger.info("Document uploaded", extra={
    "custom_dimensions": {
        "category": "Machine Learning",
        "chunk_count": 12
    }
})
```

### 7.2 Health Checks

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "openai_api": await check_openai(),
            "chroma_db": await check_chroma(),
            "file_storage": await check_storage()
        }
    }
```

## 8. Security Checklist

- [ ] OPENAI_API_KEY in environment variables (NOT in code)
- [ ] HTTPS/TLS enabled (443 redirect to 80)
- [ ] CORS configured for specific origins
- [ ] SQL injection prevention (parameterized queries)
- [ ] Rate limiting on API endpoints
- [ ] Input validation (file uploads, chat messages)
- [ ] API authentication (future: JWT tokens)
- [ ] Data encryption at rest (PostgreSQL encryption)
- [ ] Data encryption in transit (HTTPS)
- [ ] Regular backups (data/ directory)

## 9. Deployment Checklist

- [ ] Environment variables configured
- [ ] Data directories exist and writable
- [ ] OPENAI_API_KEY is valid
- [ ] Ports 8000 & 5173 accessible (or proxied)
- [ ] Database/vector store initialized
- [ ] Health check endpoint responds
- [ ] Activity Logger polling works
- [ ] Frontend assets built & served
- [ ] Backend logs configured
- [ ] Monitoring/alerting setup

---

**Verzió**: 1.0  
**Legutolsó frissítés**: 2026. január 1.
