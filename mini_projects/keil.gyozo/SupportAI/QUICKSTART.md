# SupportAI - Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Step 1: Install Dependencies

```bash
# Install Poetry if you don't have it
pip install poetry

# Install project dependencies
poetry install
```

### Step 2: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

### Step 3: Start Services

```bash
# Start Qdrant and Redis with Docker
docker compose -f docker/docker-compose.yml up -d

# Wait for services to be ready (check with docker ps)
docker compose -f docker/docker-compose.yml ps
```

### Step 4: Seed Knowledge Base

```bash
# Populate Qdrant with sample KB articles
poetry run python scripts/seed_qdrant.py
```

### Step 5: Run the Application

```bash
# Start the FastAPI server
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 6: Test It!

Visit `http://localhost:8000/docs` for interactive API documentation.

Or use curl:

```bash
curl -X POST http://localhost:8000/api/v1/tickets/process \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TKT-TEST-001",
    "raw_message": "I was charged twice for my subscription this month",
    "customer_name": "John Doe",
    "customer_email": "john@example.com"
  }'
```

## 📋 Expected Response

```json
{
  "success": true,
  "ticket_id": "TKT-TEST-001",
  "result": {
    "ticket_id": "TKT-TEST-001",
    "timestamp": "2025-01-23T10:30:00+00:00",
    "triage": {
      "category": "Billing",
      "subcategory": "Duplicate Charge",
      "priority": "P2",
      "sla_hours": 24,
      "suggested_team": "Finance Team",
      "sentiment": "frustrated",
      "confidence": 0.92
    },
    "answer_draft": {
      "greeting": "Hi John,",
      "body": "I understand your concern about being charged twice...",
      "closing": "Best regards,\nSupport Team",
      "tone": "empathetic_professional"
    },
    "citations": [...],
    "policy_check": {
      "refund_promise": false,
      "sla_mentioned": true,
      "escalation_needed": false,
      "compliance": "passed"
    }
  }
}
```

## 🛠️ Troubleshooting

### Qdrant Connection Error

If you see `[SSL: WRONG_VERSION_NUMBER]`:
- Check that `QDRANT_HTTPS=false` in your `.env`
- Verify Qdrant is running: `docker ps | grep qdrant`

### OpenAI API Error

- Verify your API key is correct in `.env`
- Check you have credits: https://platform.openai.com/usage

### Import Errors

```bash
# Make sure you're in the Poetry environment
poetry shell

# Or prefix commands with poetry run
poetry run python scripts/seed_qdrant.py
```

## 📚 Next Steps

1. **Customize Knowledge Base**: Edit `scripts/seed_qdrant.py` with your own documents
2. **Adjust Workflow**: Modify nodes in `src/nodes/` for your business logic
3. **Add Integrations**: Connect to Zendesk, Jira, or Slack (see `.env.example`)
4. **Deploy**: Use provided Dockerfile and docker-compose.yml

## 🔑 Key Files

- [src/main.py](src/main.py) - FastAPI application entry point
- [src/workflow/graph.py](src/workflow/graph.py) - LangGraph workflow definition
- [src/nodes/](src/nodes/) - Individual workflow nodes
- [src/services/](src/services/) - External service integrations
- [scripts/seed_qdrant.py](scripts/seed_qdrant.py) - Knowledge base seeding

## 💡 Pro Tips

1. **Use Makefile**: Run `make help` to see all available commands
2. **Check Metrics**: Visit `http://localhost:8000/api/v1/tickets/metrics`
3. **Monitor Logs**: Use `docker compose logs -f` to watch service logs
4. **Test Workflow**: See `tests/` for examples of testing individual nodes

## ⚠️ Remember

- Node names ≠ state field names (use `check_policy` not `policy_check`)
- Always use `datetime.now(timezone.utc)` not `datetime.utcnow()`
- Qdrant point IDs must be UUIDs, not strings
- Local Qdrant = `https=False`, Cloud = `https=True`

Happy building! 🎉
