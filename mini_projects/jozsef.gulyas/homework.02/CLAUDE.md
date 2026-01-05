# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Retrieval-Augmented Generation (RAG) Document Search System** that allows users to query markdown documents using natural language through a CLI interface. It uses OpenAI's embedding and completion models with ChromaDB for vector storage.

## Running the Application

```bash
# Run the main application
uv run python -m application.main

# Or without uv
python -m application.main
```

The application:
1. Loads environment variables from `.env`
2. Scans `documents/` directory for markdown files
3. Generates embeddings and stores them in ChromaDB (in-memory)
4. Starts an interactive CLI for querying

## Environment Setup

Required environment variables (see `.env.example`):
- `OPENAI_API_KEY` - Required for embeddings and completions
- `EMBEDDING_MODEL` - Default: `text-embedding-3-small`
- `COMPLETION_MODEL` - Default: `gpt-4o-mini`

## Architecture

The system follows a layered architecture with dependency injection:

```
User (CLI) → CliInterface → VectorStore ↘
                                         OpenAIGateway → OpenAI API
             MarkdownRAGChunker --------↗
```

### Key Components

**main.py** - Orchestrates initialization:
- Loads environment variables
- Creates OpenAIGateway with configured models
- Initializes VectorStore with document processing
- Launches CliInterface

**openai_gateway.py** - Central integration for OpenAI APIs:
- `get_embedding(text)` - Generates embeddings via text-embedding API
- `get_completion(prompt, context, history)` - Gets chat completions via chat/completions endpoint
- **Important**: Must use `/chat/completions` endpoint for chat models like `gpt-4o-mini`
- **Response parsing**: Chat completions return `["choices"][0]["message"]["content"]`, not `["text"]`

**vector_store.py** - ChromaDB vector database management:
- Uses in-memory ChromaDB (no persistence between runs)
- `init(files)` - Processes markdown files and stores embeddings
- `add_vector(text, metadata)` - Adds document chunks with embeddings
- `search(query, n_results)` - Vector similarity search

**markdown_chunker.py** - Structure-aware document processing:
- Chunking strategy: 800 char target size, 150 char overlap
- Respects markdown structure (H1, H2 headers)
- Preserves metadata (headers, source file) for citations
- Splits by paragraphs while maintaining word boundaries

**cli_interface.py** - User interaction layer:
- Simple query loop
- Searches vector store and formats context for LLM
- Displays responses with conversation history tracking

## Common Issues

**Unicode Encoding Errors on Windows**: The markdown_chunker.py may have Unicode characters (✓, ✗) in print statements that fail on Windows terminals using cp1252 encoding. Replace with ASCII alternatives like `[OK]` and `[ERROR]`.

**OpenAI 400 Errors**: Ensure you're using the correct API endpoint:
- Chat models (`gpt-4o-mini`, `gpt-4`, etc.) require `/chat/completions` endpoint
- Legacy completion models require `/completions` endpoint
- Response structure differs between endpoints

## Data Flow

1. **Document Loading**: Scans `documents/` for `.md` files
2. **Chunking**: Splits by markdown structure with overlap (800/150 chars)
3. **Embedding**: Generates vectors via OpenAI embedding model
4. **Storage**: Stores in ChromaDB with metadata (headers, source)
5. **Query**: User query → embed → vector search → top-k results
6. **Completion**: Context + query → chat completion → response with citations

## Limitations

- ChromaDB runs in-memory (no persistence across restarts)
- No automated tests or linting configured
- Conversation history tracked but minimally used in prompts
- No error handling for API failures or missing documents
