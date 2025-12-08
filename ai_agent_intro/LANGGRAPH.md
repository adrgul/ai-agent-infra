# LangGraph Integration

## Overview

The AI Weather Agent now supports **LangGraph** for sophisticated agent orchestration! LangGraph provides a graph-based approach to building AI agents with explicit state management and node-based execution.

## Architecture

### Traditional Approach
- Sequential use case execution
- Direct service calls
- Simple error handling

### LangGraph Approach (New!)
- Graph-based workflow with nodes
- Explicit state management
- Better observability and debugging
- Easier to extend with new tools/nodes

## Graph Structure

```
┌──────────────┐
│   GEOCODE    │  Node 1: Geocode city → coordinates
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ FETCH WEATHER│  Node 2: Get weather forecast
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  GENERATE    │  Node 3: AI briefing with LLM
│   BRIEFING   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   FINALIZE   │  Node 4: Create final response
└──────┬───────┘
       │
       ▼
     [END]
```

## Configuration

Toggle between traditional and LangGraph approaches via environment variable:

```bash
# In .env file
USE_LANGGRAPH=true   # Use LangGraph (default)
# or
USE_LANGGRAPH=false  # Use traditional approach
```

## Benefits of LangGraph

1. **State Management**: Explicit state tracked through the workflow
2. **Observability**: Each node logs its progress
3. **Extensibility**: Easy to add new nodes (e.g., caching, validation)
4. **Error Recovery**: Better error handling at each node
5. **Flexibility**: Can modify graph structure without changing business logic

## Example Logs

With LangGraph, you'll see detailed node-level logging (real execution):

```
[USE CASE] Executing LangGraph workflow for Vienna on 2025-11-20
[AGENT] Starting workflow for Vienna on 2025-11-20
[GEOCODE NODE] Processing city: Vienna
[GEOCODE NODE] Success: Wien, Österreich (48.2083537, 16.3725042)
[WEATHER NODE] Fetching weather for 48.2083537, 16.3725042 on 2025-11-20
[WEATHER NODE] Success: 0.5-4.4°C, 28% rain
[BRIEFING NODE] Generating AI briefing
[BRIEFING NODE] Success: Generated briefing with 3 activities
[FINALIZE NODE] Creating final response
[FINALIZE NODE] Success: Briefing ready
[AGENT] Workflow complete
```

This detailed logging shows:
- **Each node executes sequentially** following the graph edges
- **State flows correctly** from geocode → weather → briefing → finalize
- **Error handling** at each node level
- **Observability** into the agent's decision-making process

## Future Extensions

With LangGraph, we can easily add:

- **Caching Node**: Check if recent briefing exists
- **Validation Node**: Verify data quality
- **Retry Node**: Smart retry logic for failures
- **Multi-City Node**: Parallel processing for multiple cities
- **User Preference Node**: Personalize based on user history

## Technical Details

### Dependencies

- `langgraph`: Graph framework
- `langchain-core`: Core abstractions
- `langchain-openai`: OpenAI integration

### Key Files

- `backend/app/application/langgraph_agent.py`: LangGraph agent implementation
- `backend/app/application/briefing_usecase_langgraph.py`: LangGraph-based use case
- `backend/app/interfaces/container.py`: DI container with LangGraph support

## Switching Implementations

The application automatically uses the configured approach (traditional or LangGraph) based on the `USE_LANGGRAPH` environment variable. Both implementations share the same:

- Domain models
- Infrastructure services (geocoding, weather, LLM)
- REST API endpoints
- Frontend UI

This allows for easy A/B testing and gradual migration.
