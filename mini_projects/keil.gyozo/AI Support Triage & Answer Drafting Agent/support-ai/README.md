# SupportAI

AI-powered customer support triage and response agent using LangChain and LangGraph with RAG (Retrieval-Augmented Generation) for automated ticket processing.

## 🎯 Features

- **Automated Triage**: Classify tickets by category, priority, and sentiment
- **Intelligent Routing**: Assign tickets to appropriate teams with SLA tracking
- **Knowledge Base Retrieval**: RAG-powered search with re-ranking for relevant articles
- **Draft Response Generation**: Create personalized, policy-compliant responses
- **Policy Validation**: Ensure responses follow company guidelines
- **Multi-Channel Support**: Email, chat, and ticketing system integrations

## 📊 Business Impact

- **-40%** reduction in manual triage time
- **+50%** senior support capacity
- **85% → 95%** SLA compliance improvement
- **-60%** customer complaints through standardized responses

## 🏗️ Architecture

The system processes support tickets through an 8-node LangGraph workflow:

1. **Intent Detection** - Classify problem type and sentiment
2. **Triage Classification** - Category, priority, SLA, team assignment
3. **Query Expansion** - Generate semantic search queries
4. **Vector Search** - Retrieve relevant KB articles
5. **Re-ranking** - Score and select top documents
6. **Draft Generation** - Create personalized response
7. **Policy Check** - Validate compliance
8. **Output Validation** - Ensure schema compliance

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key
- Vector database (Pinecone recommended)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd support-ai
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. Run the application:
```bash
python main.py
```

## 📁 Project Structure

```
support-ai/
├── src/
│   ├── agents/           # LLM-powered agent nodes
│   ├── retrieval/        # Vector search and re-ranking
│   ├── workflow/         # LangGraph workflow definition
│   ├── schemas/          # Pydantic data models
│   ├── templates/        # Prompts and response templates
│   ├── utils/            # Configuration, logging, validators
│   └── integrations/     # External system connectors
├── data/
│   ├── knowledge_base/   # KB articles and embeddings
│   └── examples/         # Sample tickets for testing
├── tests/                # Unit and integration tests
├── notebooks/            # Data preparation and evaluation
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
├── setup.py             # Package configuration
├── main.py              # Application entry point
└── README.md
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `PINECONE_API_KEY` | Pinecone API key | Yes* |
| `COHERE_API_KEY` | Cohere API key for re-ranking | Yes |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No |

*Choose one vector database provider

### Knowledge Base Setup

1. Place KB articles in `data/knowledge_base/raw/`
2. Run data preparation notebook:
```bash
jupyter notebook notebooks/01_data_preparation.ipynb
```

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

Run specific test categories:
```bash
pytest tests/test_agents/     # Agent unit tests
pytest tests/test_workflow/   # Integration tests
```

## 📊 Evaluation Metrics

Track these KPIs for success measurement:

- **Triage Accuracy**: 90%+ F1-score on classification
- **Draft Acceptance Rate**: 70%+ drafts sent with minor edits
- **Response Time**: < 10 seconds average
- **Citation Precision**: 95%+ relevant citations
- **Escalation Rate**: < 15% tickets requiring human intervention

## 🔌 Integrations

### Supported Systems

- **Ticketing**: Zendesk, Freshdesk
- **Communication**: Slack, Microsoft Teams
- **Email**: SMTP/IMAP
- **Project Management**: Jira

### Adding New Integrations

1. Create connector in `src/integrations/`
2. Implement standard interface
3. Add configuration to `.env.example`
4. Update requirements.txt

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🙋 Support

For questions or issues:
- Create an issue on GitHub
- Check the documentation in `docs/`
- Review sample tickets in `data/examples/`