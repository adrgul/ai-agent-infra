# 🚀 AI Weather Agent - Quick Reference

## One-Line Start
```bash
./scripts/start.sh
```

## Prerequisites Checklist
- [ ] Docker installed and running
- [ ] Docker Compose installed
- [ ] OpenAI API key ready
- [ ] Ports 5173 and 8000 available

## Initial Setup (First Time Only)
```bash
# 1. Copy environment file
cp .env.sample .env

# 2. Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-actual-key-here

# 3. Make scripts executable (already done)
chmod +x scripts/start.sh scripts/down.sh

# 4. Start everything
./scripts/start.sh
```

## URLs After Startup
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Common Commands

### Start Services
```bash
./scripts/start.sh
```

### Stop Services
```bash
./scripts/down.sh
```

### View Logs (All Services)
```bash
docker compose logs -f
```

### View Logs (Backend Only)
```bash
docker compose logs -f backend
```

### View Logs (Frontend Only)
```bash
docker compose logs -f frontend
```

### Rebuild After Code Changes
```bash
docker compose build
docker compose up -d
```

### Restart a Single Service
```bash
docker compose restart backend
# or
docker compose restart frontend
```

### Check Service Status
```bash
docker compose ps
```

### Execute Commands in Backend Container
```bash
docker compose exec backend bash
```

### Run Backend Tests
```bash
# Option 1: Inside container
docker compose exec backend pytest

# Option 2: Locally
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest
```

## API Examples

### Get Weather Briefing
```bash
curl "http://localhost:8000/api/briefing?city=Budapest&date=2025-11-18" | jq
```

### Get History
```bash
curl "http://localhost:8000/api/history" | jq
```

### Health Check
```bash
curl "http://localhost:8000/health"
```

## Troubleshooting

### Backend Won't Start
```bash
# Check logs
docker compose logs backend

# Common issues:
# 1. Missing OPENAI_API_KEY in .env
# 2. Port 8000 already in use
# 3. Data directory permissions
```

### Frontend Won't Start
```bash
# Check logs
docker compose logs frontend

# Common issues:
# 1. Backend not healthy yet (wait longer)
# 2. Port 5173 already in use
# 3. Build failed (check build logs)
```

### Can't Connect to Backend from Frontend
```bash
# Verify backend is healthy
curl http://localhost:8000/health

# Check network
docker network inspect aiagent_net

# Rebuild frontend with correct API base
docker compose build frontend
docker compose up -d frontend
```

### Clear Everything and Start Fresh
```bash
# Stop and remove all containers, networks, volumes
docker compose down -v

# Remove built images
docker compose down --rmi all

# Start fresh
./scripts/start.sh
```

## File Locations

### Backend Code
```
backend/app/
```

### Frontend Code
```
frontend/src/
```

### Persistent Data
```
data/history.json  # Created after first request
```

### Environment Config
```
.env  # Your local config (gitignored)
.env.sample  # Template for reference
```

## Development Workflow

### Make Backend Changes
1. Edit files in `backend/app/`
2. Rebuild: `docker compose build backend`
3. Restart: `docker compose up -d backend`
4. Test: `docker compose logs -f backend`

### Make Frontend Changes
1. Edit files in `frontend/src/`
2. Rebuild: `docker compose build frontend`
3. Restart: `docker compose up -d frontend`
4. Test in browser: http://localhost:5173

### Run Tests
```bash
cd backend
pytest -v  # All tests
pytest app/tests/test_geocoding.py  # Specific file
pytest -k "test_geocode"  # Specific test
```

## Environment Variables Reference

### Required
- `OPENAI_API_KEY`: Your OpenAI API key

### Optional (with defaults)
- `OPENAI_MODEL`: gpt-4o-mini
- `NOMINATIM_BASE`: https://nominatim.openstreetmap.org
- `OPENMETEO_BASE`: https://api.open-meteo.com/v1
- `LOG_LEVEL`: INFO
- `DATA_DIR`: /app/data
- `PORT`: 8000
- `VITE_API_BASE`: http://localhost:8000

## Performance Tips

### Reduce Build Time
```bash
# Use buildkit for parallel builds
COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker compose build
```

### Clean Docker Cache
```bash
docker system prune -a
```

### Monitor Resource Usage
```bash
docker stats
```

## Security Notes

- Never commit `.env` file (already in .gitignore)
- Keep OpenAI API key secure
- In production, restrict CORS origins in backend
- Use HTTPS in production
- Update dependencies regularly

## Next Steps

1. ✅ Start the application
2. ✅ Test with a few cities
3. ✅ Check the history panel
4. ✅ Read the API docs at /docs
5. ✅ Explore the code
6. ✅ Run the tests
7. ✅ Make it your own!

## Getting Help

- Check logs: `docker compose logs -f`
- Read README.md for detailed info
- Read PROJECT_SUMMARY.md for architecture
- Check API docs: http://localhost:8000/docs
- Verify health: http://localhost:8000/health

---
**Happy coding! 🎉**
