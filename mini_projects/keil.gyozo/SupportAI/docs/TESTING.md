# SupportAI - Testing Guide

## Testing Philosophy

Our testing strategy follows the testing pyramid:
- **60% Unit Tests**: Fast, isolated, extensive coverage
- **30% Integration Tests**: Service interactions, API endpoints
- **10% E2E Tests**: Full workflow, real services

## Quick Start

```bash
# Run all tests
make test

# Run specific test types
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-e2e          # End-to-end tests

# With coverage
make test-coverage

# Parallel execution (faster)
make test-parallel

# Watch mode (re-run on changes)
make test-watch
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_nodes/
│   │   ├── test_intent_detection.py
│   │   ├── test_triage_classify.py
│   │   ├── test_query_expansion.py
│   │   ├── test_rag_search.py
│   │   ├── test_rerank.py
│   │   ├── test_draft_answer.py
│   │   ├── test_policy_check.py
│   │   └── test_validation.py
│   ├── test_services/
│   │   ├── test_qdrant_service.py
│   │   ├── test_embedding_service.py
│   │   ├── test_llm_service.py
│   │   └── test_cache_service.py
│   └── test_models/
│       ├── test_state.py
│       ├── test_ticket.py
│       └── test_triage.py
├── integration/
│   ├── test_workflow.py
│   ├── test_qdrant.py
│   └── test_api.py
└── e2e/
    └── test_ticket_flow.py
```

## Unit Testing

### Testing Nodes

**Pattern**: Mock LLM, test logic

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_triage_classify_billing_ticket(mock_llm_response):
    """Test billing ticket gets correct priority."""

    # Arrange
    state = {
        "ticket_id": "TKT-001",
        "raw_message": "I was charged twice",
        "problem_type": "billing",
        "sentiment": "frustrated"
    }

    with patch("src.nodes.triage_classify.get_llm") as mock_llm:
        mock_llm.return_value.with_structured_output.return_value.ainvoke = AsyncMock(
            return_value=TriageResult(**mock_llm_response)
        )

        # Act
        result = await triage_classify_node(state)

    # Assert
    assert result["category"] == "Billing"
    assert result["priority"] == "P2"
    assert result["sla_hours"] == 24
```

### Testing Services

**Pattern**: Mock external dependencies

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_qdrant_search():
    """Test Qdrant search returns formatted documents."""

    # Arrange
    mock_client = AsyncMock()
    mock_result = MagicMock()
    mock_result.points = [
        MagicMock(
            payload={"doc_id": "KB-1234", "content": "test"},
            score=0.89
        )
    ]
    mock_client.query_points.return_value = mock_result

    service = QdrantService(https=False)
    service.client = mock_client

    # Act
    results = await service.search([0.1] * 3072, top_k=5)

    # Assert
    assert len(results) == 1
    assert results[0]["doc_id"] == "KB-1234"
```

### Testing Models

**Pattern**: Validate Pydantic schemas

```python
@pytest.mark.unit
def test_ticket_input_validation():
    """Test TicketInput validates email."""

    # Valid ticket
    ticket = TicketInput(
        ticket_id="TKT-001",
        raw_message="Help!",
        customer_name="John",
        customer_email="john@example.com"
    )
    assert ticket.customer_email == "john@example.com"

    # Invalid email
    with pytest.raises(ValidationError):
        TicketInput(
            ticket_id="TKT-002",
            raw_message="Help!",
            customer_name="Jane",
            customer_email="not-an-email"
        )
```

## Integration Testing

### Testing Workflow

**Pattern**: Real services, mocked LLM

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_workflow_execution():
    """Test complete workflow with real Qdrant."""

    # Arrange
    qdrant_service = QdrantService()
    embedding_service = EmbeddingService()

    # Seed test data
    await seed_test_knowledge_base(qdrant_service, embedding_service)

    workflow = build_support_workflow(
        qdrant_service=qdrant_service,
        embedding_service=embedding_service
    )

    initial_state = {
        "ticket_id": "TKT-INT-001",
        "raw_message": "I was charged twice",
        "customer_name": "John Doe",
        "customer_email": "john@example.com"
    }

    # Act
    result = await workflow.ainvoke(initial_state)

    # Assert
    assert result["category"] is not None
    assert result["priority"] in ["P1", "P2", "P3"]
    assert len(result.get("citations", [])) > 0
    assert result["policy_check"]["compliance"] in ["passed", "warning", "failed"]
```

### Testing API

**Pattern**: Real FastAPI app, mocked services

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_ticket_endpoint(api_client):
    """Test POST /api/v1/tickets/process."""

    # Arrange
    ticket = {
        "ticket_id": "TKT-API-001",
        "raw_message": "I need help",
        "customer_name": "Test User",
        "customer_email": "test@example.com"
    }

    # Act
    response = await api_client.post(
        "/api/v1/tickets/process",
        json=ticket
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["ticket_id"] == "TKT-API-001"
    assert "triage" in data["result"]
```

## E2E Testing

### Testing Complete Flow

**Pattern**: Real services, real LLM (expensive!)

```python
@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.slow
async def test_real_ticket_processing():
    """Test real ticket with all services.

    WARNING: This test makes real API calls to OpenAI!
    Only run when necessary.
    """

    # Arrange - real services
    qdrant_service = QdrantService()
    embedding_service = EmbeddingService()

    # Ensure KB is seeded
    assert await qdrant_service.collection_exists()

    workflow = build_support_workflow(
        qdrant_service=qdrant_service,
        embedding_service=embedding_service
    )

    ticket = {
        "ticket_id": "TKT-E2E-001",
        "raw_message": (
            "I was charged $29.99 twice for my subscription on January 15th. "
            "This is very frustrating and I need this resolved immediately."
        ),
        "customer_name": "Sarah Johnson",
        "customer_email": "sarah@example.com"
    }

    # Act
    result = await workflow.ainvoke(ticket)

    # Assert - comprehensive checks
    assert result["problem_type"] == "billing"
    assert result["sentiment"] in ["frustrated", "neutral"]
    assert result["category"] == "Billing"
    assert result["priority"] in ["P1", "P2"]  # Frustrated = higher priority
    assert result["sla_hours"] <= 24

    # Check RAG worked
    assert len(result["retrieved_docs"]) > 0
    assert len(result["reranked_docs"]) > 0

    # Check draft quality
    draft = result["answer_draft"]
    assert "Sarah" in draft["greeting"]  # Personalized
    assert len(draft["body"]) > 100  # Substantial response
    assert "[KB-" in draft["body"] or "[FAQ-" in draft["body"]  # Has citations

    # Check policy compliance
    policy = result["policy_check"]
    assert policy["compliance"] in ["passed", "warning"]  # Not failed

    # Check final output
    assert result["output"]["timestamp"] is not None
```

## Test Fixtures (conftest.py)

### Essential Fixtures

```python
@pytest.fixture
def ticket_factory():
    """Factory for creating test tickets."""
    from faker import Faker
    fake = Faker()

    def create(**kwargs):
        defaults = {
            "ticket_id": f"TKT-{fake.uuid4()[:8]}",
            "raw_message": fake.paragraph(),
            "customer_name": fake.name(),
            "customer_email": fake.email()
        }
        return {**defaults, **kwargs}

    return create

@pytest.fixture
def sample_kb_documents():
    """Sample knowledge base documents."""
    return [
        {
            "doc_id": "KB-TEST-001",
            "chunk_id": "KB-TEST-001-c-1",
            "title": "Test Document",
            "content": "Test content about billing issues...",
            "category": "billing",
            # ...
        }
    ]

@pytest.fixture
async def qdrant_service():
    """Qdrant service for integration tests."""
    service = QdrantService(https=False)
    yield service
    await service.close()
```

## Mocking Strategies

### Mock LLM Responses

```python
# Option 1: Direct mock
with patch("src.nodes.triage_classify.get_llm") as mock_llm:
    mock_llm.return_value.with_structured_output.return_value.ainvoke = AsyncMock(
        return_value=TriageResult(
            category="Billing",
            priority="P2",
            # ...
        )
    )

# Option 2: Fixture
@pytest.fixture
def mock_llm_triage():
    def _mock(category="Billing", priority="P2"):
        return TriageResult(
            category=category,
            subcategory="General",
            priority=priority,
            sla_hours=24,
            suggested_team="Support",
            confidence=0.9
        )
    return _mock
```

### Mock Vector Search

```python
@pytest.fixture
def mock_qdrant_search():
    def _search(docs):
        mock_result = MagicMock()
        mock_result.points = [
            MagicMock(payload=doc, score=0.9)
            for doc in docs
        ]
        return mock_result
    return _search
```

## Coverage Requirements

### Minimum Coverage: 80%

```bash
# Generate coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing

# View HTML report
open coverage_html/index.html  # macOS
start coverage_html/index.html  # Windows
```

### Coverage Targets

| Module | Target | Current |
|--------|--------|---------|
| models/ | 95% | ✅ |
| services/ | 90% | ✅ |
| nodes/ | 85% | ✅ |
| workflow/ | 90% | ✅ |
| api/ | 80% | ✅ |
| utils/ | 85% | ✅ |

## Test Markers

### Using Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only E2E tests
pytest -m e2e

# Run fast tests (skip slow)
pytest -m "not slow"

# Run specific combinations
pytest -m "unit or integration"
```

### Available Markers

```python
# In pytest.ini
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (require external services)
    e2e: End-to-end tests (full workflow)
    slow: Slow running tests (LLM calls)
```

## Performance Testing

### Benchmark Tests

```python
@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_workflow_performance(benchmark):
    """Benchmark full workflow execution time."""

    async def run_workflow():
        workflow = build_support_workflow()
        state = {...}
        return await workflow.ainvoke(state)

    result = benchmark(run_workflow)

    # Assert performance requirements
    assert result.stats.mean < 5.0  # Average < 5 seconds
```

### Load Testing

```bash
# Use locust for load testing
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## Test Data Management

### Test Database

```python
@pytest.fixture(scope="session")
async def test_qdrant():
    """Create test Qdrant collection."""
    service = QdrantService()

    # Create test collection
    await service.create_collection()

    # Seed test data
    await seed_test_data(service)

    yield service

    # Cleanup
    await service.delete_collection()
```

### Test Isolation

```python
@pytest.fixture(autouse=True)
async def reset_state():
    """Reset global state between tests."""
    # Clear caches
    # Reset counters
    # Clean up temp files
    yield
    # Cleanup after test
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      qdrant:
        image: qdrant/qdrant:v1.13.2
        ports:
          - 6333:6333
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install

      - name: Run tests
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          poetry run pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Debugging Tests

### Run Single Test

```bash
# Run specific test file
pytest tests/unit/test_nodes/test_triage_classify.py

# Run specific test function
pytest tests/unit/test_nodes/test_triage_classify.py::test_billing_ticket

# Run with verbose output
pytest -v tests/unit/

# Run with print statements
pytest -s tests/unit/

# Stop on first failure
pytest -x tests/
```

### Debug with PDB

```python
@pytest.mark.unit
def test_something():
    # Add breakpoint
    import pdb; pdb.set_trace()

    # Or use pytest's built-in
    pytest.set_trace()
```

### View Full Diffs

```bash
# Show full assertion diffs
pytest --tb=long

# Show locals in traceback
pytest --showlocals
```

## Common Testing Patterns

### Parameterized Tests

```python
@pytest.mark.parametrize("priority,sla_hours", [
    ("P1", 4),
    ("P2", 24),
    ("P3", 72),
])
@pytest.mark.unit
def test_sla_mapping(priority, sla_hours):
    """Test priority to SLA mapping."""
    assert get_sla_hours(priority) == sla_hours
```

### Test Async Functions

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_function()
    assert result is not None
```

### Test Exceptions

```python
@pytest.mark.unit
def test_invalid_input_raises():
    """Test that invalid input raises ValueError."""
    with pytest.raises(ValueError, match="Invalid priority"):
        validate_priority("P5")
```

## Best Practices

### DO ✅

1. **Use descriptive test names**
   ```python
   def test_frustrated_customer_gets_priority_boost()
   ```

2. **Follow AAA pattern** (Arrange, Act, Assert)
   ```python
   # Arrange
   state = {...}

   # Act
   result = await node(state)

   # Assert
   assert result["priority"] == "P2"
   ```

3. **One assertion per test** (when possible)

4. **Use fixtures for common setup**

5. **Mock external dependencies**

6. **Test edge cases**

### DON'T ❌

1. **Don't test implementation details**
   - Test behavior, not internal structure

2. **Don't make real API calls in unit tests**
   - Use mocks for OpenAI, Qdrant in unit tests
   - Real calls only in integration/E2E

3. **Don't write flaky tests**
   - Avoid time-dependent assertions
   - Use deterministic data

4. **Don't ignore warnings**
   - Fix deprecation warnings
   - Treat warnings as errors in CI

## Test Maintenance

### Regular Tasks

1. **Update test data** when KB changes
2. **Review slow tests** and optimize
3. **Check coverage** and fill gaps
4. **Refactor duplicated** test code
5. **Update mocks** when APIs change

### Metrics to Track

- Test execution time
- Code coverage percentage
- Number of flaky tests
- Test-to-code ratio

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Faker](https://faker.readthedocs.io/)
- [Factory Boy](https://factoryboy.readthedocs.io/)
