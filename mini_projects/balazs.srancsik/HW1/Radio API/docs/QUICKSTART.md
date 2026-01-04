# AI Agent Demo - Quick Start Guide

## 🚀 Fastest Way to Run

### Using Docker (Recommended)

1. **Set your OpenAI API key**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

2. **Start everything**:
   ```bash
   docker-compose up --build
   ```

3. **Open your browser**: http://localhost:3000

That's it! 🎉

### Using Local Development

1. **Set your OpenAI API key**:
   ```bash
   export OPENAI_API_KEY='your_key_here'
   ```

2. **Run the start script**:
   ```bash
   chmod +x start-dev.sh
   ./start-dev.sh
   ```

3. **Open your browser**: http://localhost:3000

## 💬 Try These Prompts

Once running, try asking:

- "What's the weather in Budapest?"
- "What's the current BTC price in EUR?"
- "Convert 100 EUR to HUF"
- "Locate IP address 8.8.8.8"
- "From now on, answer in English"
- "Save a note: Meeting tomorrow at 3pm"
- "Search our past conversations for 'weather'"
- "reset context" (clears conversation, keeps preferences)

## 📖 Full Documentation

See [README.md](README.md) for:
- Complete architecture explanation
- API documentation
- LangGraph workflow details
- SOLID principles implementation
- How to extend with new tools

## 🆘 Troubleshooting

**Backend won't start?**
- Check OPENAI_API_KEY is set
- Ensure port 8000 is free

**Frontend won't start?**
- Ensure port 3000 is free
- Try `npm install` in frontend/

**Docker issues?**
- Ensure Docker is running
- Try `docker-compose down` then `up --build` again

**Can't reach backend from frontend?**
- Check backend is running on http://localhost:8000
- Check API docs at http://localhost:8000/docs
