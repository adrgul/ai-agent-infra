# Document Search with RAG

A Retrieval-Augmented Generation (RAG) system that enables intelligent question-answering over markdown documents using OpenAI's embeddings and chat completion models with ChromaDB vector storage. I was a bit confused with this project. All I found was the one liner in the presentation "Dokumentumkeresés implementálása". Hope this is something similar what you meant by that.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [How It Works](#how-it-works)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Limitations](#limitations)
- [License](#license)

## Features

- **Intelligent Document Search**: Uses vector embeddings to find semantically relevant content
- **Context-Aware Responses**: Leverages RAG to provide accurate answers with source citations
- **Markdown Structure Preservation**: Respects document hierarchy (H1, H2 headers) during chunking
- **Interactive CLI**: Simple command-line interface for querying documents
- **Conversation History**: Maintains context across multiple queries in a session
- **Configurable Models**: Support for different OpenAI embedding and completion models
- **Smart Chunking**: Structure-aware document processing with 800 character target size and 150 character overlap

## Prerequisites

- Python 3.13 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd homework.02
```

### 2. Set Up Environment

#### Using uv (Recommended)

```bash
# uv will automatically create a virtual environment and install dependencies
uv sync
```

#### Using pip

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -e .
```

### 3. Add Your Documents

Place your markdown (`.md`) files in the `documents/` directory:

```bash
mkdir -p documents
# Copy your markdown files to documents/
```

The application will automatically scan this directory on startup.

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and configure the following variables:

```env
OPENAI_API_KEY=your_actual_api_key_here
EMBEDDING_MODEL=text-embedding-3-small
COMPLETION_MODEL=gpt-4o-mini
```

#### Configuration Options

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | Your OpenAI API key |
| `EMBEDDING_MODEL` | No | `text-embedding-3-small` | OpenAI embedding model for document vectorization |
| `COMPLETION_MODEL` | No | `gpt-4o-mini` | OpenAI chat model for generating responses |

#### Supported Models

**Embedding Models:**
- `text-embedding-3-small` (recommended, cost-effective)
- `text-embedding-3-large` (higher quality, more expensive)
- `text-embedding-ada-002` (legacy)

**Completion Models:**
- `gpt-4o-mini` (recommended, fast and cost-effective)
- `gpt-4o` (more capable)
- `gpt-4-turbo` (high performance)
- `gpt-3.5-turbo` (budget option)

## Usage

### Running the Application

#### With uv:

```bash
uv run python -m application.main
```

#### With standard Python:

```bash
python -m application.main
```

### Application Workflow

1. **Document Loading**: The application scans the `documents/` directory for markdown files
2. **Chunking**: Splits documents by markdown structure with smart overlap
3. **Embedding Generation**: Creates vector embeddings for each document chunk
4. **Storage**: Stores embeddings in ChromaDB (in-memory)
5. **Interactive Prompt**: Enter your questions at the prompt
6. **Intelligent Responses**: Receive answers with citations from relevant documents

### Example Session

```
Loading documents, please wait...

✓ Loaded neuroplasmic_resonance.md
Generated 17 chunks from document neuroplasmic_resonance.md
Generating embedding for the file... 100% ✓ Done!

✓ Loaded quantum_dynamics_corp.md
Generated 12 chunks from document quantum_dynamics_corp.md
Generating embedding for the file... 100% ✓ Done!

✓ Loaded treaty_of_bergen.md
Generated 21 chunks from document treaty_of_bergen.md
Generating embedding for the file... 100% ✓ Done!

Welcome to the CLI Interface!
Enter your query (or 'exit' to quit): What is neuroplasmic resonance?

Response: Neuroplasmic resonance is a theoretical phenomenon in neuroscience...
[Source: neuroplasmic_resonance.md - Introduction]

Enter your query (or 'exit' to quit): exit
Goodbye!
```

### Exiting

Type `exit` or press `Ctrl+C` to quit the application.

## Project Structure

```
homework.02/
├── application/
│   ├── __init__.py
│   ├── main.py                 # Application entry point and orchestration
│   ├── openai_gateway.py       # OpenAI API integration (embeddings & completions)
│   ├── vector_store.py         # ChromaDB vector database management
│   ├── markdown_chunker.py     # Structure-aware document chunking
│   └── cli_interface.py        # Interactive command-line interface
├── documents/                  # Place your markdown files here
├── .env                        # Environment configuration (create from .env.example)
├── .env.example               # Environment configuration template
├── pyproject.toml             # Project dependencies and metadata
├── uv.lock                    # Dependency lock file (uv)
├── CLAUDE.md                  # Development guidelines for Claude Code
└── README.md                  # This file
```

## Architecture

The system follows a **layered architecture** with dependency injection for clean separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    User (CLI)                           │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                 CliInterface                            │
│  - Interactive query loop                               │
│  - Response formatting                                  │
│  - Conversation history tracking                        │
└──────────┬──────────────────────────┬───────────────────┘
           │                          │
┌──────────▼──────────┐    ┌──────────▼──────────────────┐
│   VectorStore       │    │   MarkdownChunker           │
│  - ChromaDB mgmt    │    │  - Document processing      │
│  - Vector search    │    │  - Structure-aware chunking │
│  - Add documents    │    │  - Metadata preservation    │
└──────────┬──────────┘    └──────────┬──────────────────┘
           │                          │
           └──────────┬───────────────┘
                      │
           ┌──────────▼──────────┐
           │   OpenAIGateway     │
           │  - get_embedding()  │
           │  - get_completion() │
           └──────────┬──────────┘
                      │
           ┌──────────▼──────────┐
           │    OpenAI API       │
           │  - Embeddings       │
           │  - Chat Completions │
           └─────────────────────┘
```

### Component Responsibilities

**main.py** - Application orchestrator:
- Loads environment variables
- Creates OpenAIGateway with configured models
- Initializes VectorStore with document processing
- Launches CliInterface

**openai_gateway.py** - OpenAI API integration:
- `get_embedding(text)` - Generates embeddings via text-embedding API
- `get_completion(prompt, context, history)` - Gets chat completions
- Uses `/chat/completions` endpoint for chat models

**vector_store.py** - Vector database management:
- In-memory ChromaDB instance
- `init(files)` - Processes markdown files and stores embeddings
- `add_vector(text, metadata)` - Adds document chunks with embeddings
- `search(query, n_results)` - Vector similarity search

**markdown_chunker.py** - Document processing:
- Structure-aware chunking (800 char target, 150 char overlap)
- Respects markdown headers (H1, H2)
- Preserves metadata (headers, source file) for citations
- Splits by paragraphs while maintaining word boundaries

**cli_interface.py** - User interaction:
- Query loop
- Searches vector store and formats context for LLM
- Displays responses with conversation history

## How It Works

### 1. Document Loading and Processing

When the application starts, it:

1. **Scans** the `documents/` directory for `.md` files
2. **Reads** each markdown file with UTF-8 encoding
3. **Chunks** documents using structure-aware splitting:
   - Target size: 800 characters per chunk
   - Overlap: 150 characters between chunks
   - Respects markdown headers (H1, H2) as section boundaries
   - Maintains word boundaries (no mid-word splits)
4. **Preserves metadata** for each chunk:
   - Source filename
   - Hierarchical headers (H1, H2)
   - Chunk position in document

### 2. Embedding Generation

For each document chunk:

1. **Generates** vector embedding using OpenAI's embedding model
2. **Stores** in ChromaDB with associated metadata
3. **Creates** searchable vector index

### 3. Query Processing

When you enter a query:

1. **Embeds** your query using the same embedding model
2. **Searches** ChromaDB for most similar document chunks (vector similarity)
3. **Retrieves** top-k most relevant chunks (default: 5)
4. **Extracts** context from matched chunks

### 4. Response Generation

With retrieved context:

1. **Constructs** prompt with:
   - Your query
   - Relevant document context
   - Conversation history
2. **Sends** to OpenAI chat completion model
3. **Receives** response with citations
4. **Displays** answer to you
5. **Updates** conversation history for context-aware follow-ups

### RAG Pipeline

```
User Query
    │
    ├─> Embed Query (OpenAI Embeddings)
    │
    ├─> Vector Similarity Search (ChromaDB)
    │
    ├─> Retrieve Top-K Chunks
    │
    ├─> Format Context + Query
    │
    ├─> Generate Response (OpenAI Chat Completion)
    │
    └─> Display Answer with Citations
```

## Troubleshooting

### Common Issues

#### **Unicode Encoding Errors on Windows**

**Problem**: Terminal displays garbled characters or errors like `UnicodeEncodeError`

**Solution**: The markdown_chunker.py may contain Unicode characters (✓, ✗) that fail on Windows terminals using cp1252 encoding. Replace with ASCII alternatives:
- `✓` → `[OK]`
- `✗` → `[ERROR]`

Or run with UTF-8 encoding:
```bash
# PowerShell
$env:PYTHONIOENCODING="utf-8"
uv run python -m application.main
```

#### **OpenAI API 400 Errors**

**Problem**: `BadRequestError: Error code: 400`

**Causes**:
1. **Wrong endpoint**: Chat models require `/chat/completions`, not `/completions`
2. **Invalid model name**: Check model ID is correct
3. **Malformed request**: Verify request structure

**Solution**: Ensure `openai_gateway.py` uses the correct endpoint for your model type.

#### **No Documents Found**

**Problem**: "No documents found in documents/ directory"

**Solution**:
1. Create the `documents/` directory if it doesn't exist
2. Add `.md` files to the directory
3. Verify file extensions are `.md` (not `.txt` or `.markdown`)

#### **API Key Errors**

**Problem**: `AuthenticationError: Error code: 401`

**Solution**:
1. Verify `.env` file exists and contains `OPENAI_API_KEY`
2. Check API key is valid at [OpenAI Platform](https://platform.openai.com/api-keys)
3. Ensure no extra spaces or quotes around the key in `.env`

#### **ChromaDB Errors**

**Problem**: `RuntimeError: Cannot connect to ChromaDB`

**Solution**: ChromaDB runs in-memory by default. If issues persist:
1. Check Python version is 3.13+
2. Reinstall dependencies: `uv sync --refresh`
3. Try clearing pip cache: `pip cache purge`

#### **Rate Limit Errors**

**Problem**: `RateLimitError: Error code: 429`

**Solution**:
1. Check your OpenAI API usage limits
2. Add delays between requests if processing many documents
3. Consider upgrading your OpenAI plan

## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone <repository-url>
cd homework.02

# Install with development dependencies
uv sync

# Create .env file
cp .env.example .env
# Edit .env with your API key
```

### Code Style

The project follows these conventions:
- **PEP 8** style guide for Python code
- **Type hints** for function signatures (where applicable)
- **Docstrings** for classes and complex functions
- **Dependency injection** for component initialization

### Project Dependencies

Key dependencies (see `pyproject.toml`):
- `openai` - OpenAI API client
- `chromadb` - Vector database
- `python-dotenv` - Environment variable management

### Contributing

1. Create a feature branch
2. Make your changes
3. Ensure code follows project conventions
4. Test manually with sample documents
5. Submit a pull request

### Extending the System

**Adding New Embedding Models**:
Update `EMBEDDING_MODEL` in `.env` to any OpenAI embedding model.

**Adding New Completion Models**:
Update `COMPLETION_MODEL` in `.env` to any OpenAI chat model.

**Changing Chunk Size**:
Modify the chunking parameters in `markdown_chunker.py`:
```python
target_size = 800  # Target characters per chunk
overlap = 150      # Overlap between chunks
```

**Adding Persistent Storage**:
Modify `vector_store.py` to use persistent ChromaDB:
```python
# Replace in-memory client with persistent
client = chromadb.PersistentClient(path="./chroma_db")
```

**Custom Document Types**:
Extend `markdown_chunker.py` to support other formats (e.g., PDF, TXT).

## Limitations

- **No Persistence**: ChromaDB runs in-memory; embeddings are regenerated on each restart
- **Markdown Only**: Only processes `.md` files (no PDF, DOCX, HTML, etc.)
- **No Tests**: No automated test suite or linting configured
- **Basic Error Handling**: Limited handling of API failures or edge cases
- **Single Session History**: Conversation history lost when application exits
- **No Authentication**: Direct API key usage (no OAuth or user management)
- **In-Process Only**: No web API or multi-user support
- **Fixed Chunking Strategy**: No adaptive chunking based on document type
- **No Caching**: Embeddings and completions not cached between sessions
- **Limited Context Window**: May hit token limits with very long documents or conversations

## License

This project is provided as-is for educational purposes. No specific license has been assigned.
