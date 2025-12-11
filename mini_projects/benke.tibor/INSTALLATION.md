# Installation Guide - KnowledgeRouter

Részletes telepítési útmutató Windows, Mac és Linux rendszerekre.

## 📋 Előfeltételek

### Szükséges
- **Docker & Docker Compose** (ajánlott)
  - [Windows](https://docs.docker.com/docker-for-windows/install/)
  - [Mac](https://docs.docker.com/docker-for-mac/install/)
  - [Linux](https://docs.docker.com/engine/install/)

- **Git** (az repo klónozásához)
  - [Download](https://git-scm.com/download)

- **OpenAI API Key**
  - Regisztrálj: https://platform.openai.com/

### Opcionális (Local Dev)
- **Python 3.11+**
  - [Download](https://www.python.org/downloads/)

- **Node.js 18+** (Tailwind CSS build)
  - [Download](https://nodejs.org/)

## 🐳 Docker Installation (Ajánlott)

### 1. Docker Desktop Telepítése

**Windows:**
```powershell
# Vagy töltsd le az installer-t: https://docs.docker.com/docker-for-windows/install/
choco install docker-desktop  # ha Chocolatey van
```

**Mac:**
```bash
brew install --cask docker
```

**Linux:**
```bash
sudo apt-get install docker.io docker-compose
```

### 2. Repository Klónozása

```bash
git clone https://github.com/Global-rd/ai-agents-hu.git
cd ai-agents-hu/benketibor
```

### 3. Environment Setup

```bash
# Másold az .env.example fájlt
cp .env.example .env

# Szerkeszd a .env fájlt (add meg az OPENAI_API_KEY-t)
# Macen: nano .env
# Windowson: notepad .env
```

### 4. Docker Compose Indítása

```bash
docker-compose up --build
```

**Output:**
```
benketibor-backend-1   | Starting Django...
benketibor-qdrant-1    | Qdrant is running...
benketibor-frontend-1  | HTTP server running on port 3000
```

### 5. Hozzáférés

Nyisd meg a böngészőt:

- **App**: http://localhost:3000
- **API Docs**: http://localhost:8001/api/
- **Qdrant Dashboard**: http://localhost:6334

---

## 🖥️ Local Development (BASH/PowerShell)

### Backend Setup

**1. Python Virtual Environment**

```bash
cd benketibor/backend

# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

**2. Dependencies**

```bash
pip install -r requirements.txt
```

**3. Environment Variables**

```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "sk-your-key-here"
$env:DJANGO_SETTINGS_MODULE = "core.settings"

# Mac/Linux
export OPENAI_API_KEY="sk-your-key-here"
export DJANGO_SETTINGS_MODULE="core.settings"
```

**4. Run Django Server**

```bash
python manage.py runserver 0.0.0.0:8000
```

Backend fut: http://localhost:8001

### Frontend Setup

**1. Node Dependencies** (új terminal)

```bash
cd benketibor/frontend
npm install
```

**2. Run HTTP Server**

```bash
npx http-server . -p 3000
```

Frontend fut: http://localhost:3000

---

## 🔐 API Key Konfigurálása

### OpenAI API Key Beszerzés

1. Menj a https://platform.openai.com/account/api-keys-ra
2. Kattints: "Create new secret key"
3. Másold a kulcsot
4. Add meg a `.env` fájlba:

```bash
OPENAI_API_KEY=sk-xxx...yyy
```

### Költségvetés Beállítása (Fontos!)

1. https://platform.openai.com/account/billing/overview
2. Set usage limits (pl. $10/hó)
3. Ez megakadályozza a váratlan költségeket

---

## 🐛 Troubleshooting

### ❌ Docker error: "Ports already in use"

```bash
# Find process on port 8000
# Windows PowerShell
netstat -ano | findstr :8000

# Mac/Linux
lsof -i :8000

# Kill process (Windows PowerShell)
taskkill /PID <PID> /F

# Kill process (Mac/Linux)
kill -9 <PID>
```

### ❌ OPENAI_API_KEY not found

```bash
# Ellenőrizz a .env fájlban
cat .env | grep OPENAI

# Vagy set manuálisan
export OPENAI_API_KEY="sk-..."
```

### ❌ Qdrant connection error

```bash
# Győződj meg, hogy a Qdrant container fut
docker-compose logs qdrant

# Restart containers
docker-compose restart
```

### ❌ Port 3000 / 8000 már használatban van

```bash
# Használj másik portot
docker-compose.yml-ben:
  - "8001:8000"  # Change 8001
  - "3001:3000"  # Change 3001

# Vagy állítsd le az előző containereket
docker-compose down
```

---

## ✅ Verifikáció

### Backend Check

```bash
# Terminal 1
cd backend
python manage.py runserver

# Terminal 2
curl http://localhost:8001/api/
# Válasz: 404 (OK, mert nincs root endpoint)
```

### Frontend Check

```bash
# Terminal 3
cd frontend
npx http-server . -p 3000

# Böngésző: http://localhost:3000
# Látni kell a chat interfészt
```

### API Test

```bash
curl -X POST http://localhost:8001/api/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "query": "Szeretnék szabadságot igényelni"
  }'

# Válasz JSON:
# {
#   "success": true,
#   "data": {
#     "domain": "hr",
#     "answer": "...",
#     "citations": [...]
#   }
# }
```

---

## 🚀 Production Deployment

### Docker Hub Push

```bash
# Build image
docker build -t yourname/knowledgerouter-backend backend/

# Push
docker login
docker push yourname/knowledgerouter-backend
```

### AWS/Google Cloud Deploy

1. Push image to cloud registry
2. Deploy with docker-compose or Kubernetes
3. Set up CI/CD pipeline

---

## 📞 Support

Ha problémák vannak, nézd meg:
- `docker-compose logs`
- Backend: `python manage.py --help`
- Frontend: Browser console (F12)

---

**Vásárlás! 🎉**
