# Architektúra Dokumentáció

## SOLID Principles

Ez a projekt szigorúan követi a SOLID elveket:

### 1. Single Responsibility Principle (SRP)

Minden osztály egyetlen felelősséggel rendelkezik:

- **`OpenAIClient`**: Csak OpenAI API hívások
- **`QdrantVectorStore`**: Csak vector store műveletek
- **`MarkdownDocumentLoader`**: Csak dokumentum betöltés és chunkolás
- **`RAGService`**: Csak RAG business logic

### 2. Open/Closed Principle (OCP)

A rendszer könnyen bővíthető új funkciókkal anélkül, hogy módosítani kellene a meglévő kódot:

```python
# Új LLM provider hozzáadása
class ClaudeClient(LLMClientInterface):
    def generate_answer(...):
        # Claude implementáció
        pass

# Használat - csak dependency injection változik
rag_service = RAGService(
    vector_store=vector_store,
    llm_client=ClaudeClient(),  # <- Új provider
    document_loader=document_loader
)
```

### 3. Liskov Substitution Principle (LSP)

Minden implementáció helyettesíthető az interface-ével:

```python
# Bármely VectorStoreInterface implementáció használható
vector_store: VectorStoreInterface = QdrantVectorStore(llm_client)
# vagy
vector_store: VectorStoreInterface = PineconeVectorStore(llm_client)
# vagy
vector_store: VectorStoreInterface = WeaviateVectorStore(llm_client)
```

### 4. Interface Segregation Principle (ISP)

Kis, specifikus interface-ek:

- `VectorStoreInterface` - csak vector store műveletek
- `LLMClientInterface` - csak LLM műveletek
- `DocumentLoaderInterface` - csak document loading

Nem egy nagy "ServiceInterface" minden funkcióval.

### 5. Dependency Inversion Principle (DIP)

A magas szintű modulok (RAGService) nem függenek az alacsony szintű moduloktól (OpenAIClient), hanem mindkettő az absztrakciótól (interface) függ:

```python
class RAGService:
    def __init__(
        self,
        vector_store: VectorStoreInterface,      # <- Absztrakció
        llm_client: LLMClientInterface,          # <- Absztrakció
        document_loader: DocumentLoaderInterface # <- Absztrakció
    ):
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.document_loader = document_loader
```

## Rétegek (Layers)

### Domain Layer

**Felelősség:** Core business models és interface-ek

**Fájlok:**
- `domain/models.py` - Data classes (DocumentChunk, SearchResult, Answer)
- `domain/interfaces.py` - Abstract interfaces

**Függőségek:** NINCS (tiszta domain logic)

### Infrastructure Layer

**Felelősség:** Külső rendszerekkel való kommunikáció

**Fájlok:**
- `infrastructure/llm_client.py` - OpenAI API client
- `infrastructure/vector_store.py` - Qdrant vector database
- `infrastructure/document_loader.py` - File system, document processing

**Függőségek:** 
- Domain interfaces (implementálja őket)
- Külső library-k (openai, qdrant-client, langchain)

### Services Layer

**Felelősség:** Business logic, orchestration

**Fájlok:**
- `services/rag_service.py` - RAG workflow orchestration

**Függőségek:**
- Domain interfaces (használja őket)
- NEM függ az infrastructure konkrét implementációitól

### Application Layer

**Felelősség:** User interface, dependency injection

**Fájlok:**
- `app.py` - Console UI, DI container

**Függőségek:**
- Összes réteg (összerakja a komponenseket)

## Data Flow

### 1. Inicializálás

```
app.py
  ├─> OpenAIClient() 
  ├─> QdrantVectorStore(llm_client)
  ├─> MarkdownDocumentLoader()
  └─> RAGService(vector_store, llm_client, document_loader)
```

### 2. Dokumentum Betöltés

```
RAGService.load_domain_documents()
  ├─> DocumentLoader.load_documents()
  │     ├─> Read .md files
  │     └─> Chunk text (RecursiveCharacterTextSplitter)
  │
  └─> VectorStore.add_chunks()
        ├─> LLMClient.generate_embedding() (OpenAI)
        └─> Qdrant.upsert() (store vectors)
```

### 3. Kérdés Feldolgozás (RAG)

```
RAGService.ask_question(question)
  │
  ├─> VectorStore.search(query)
  │     ├─> LLMClient.generate_embedding(query)
  │     └─> Qdrant.search() → SearchResults
  │
  └─> LLMClient.generate_answer(question, context)
        ├─> Build context from SearchResults
        ├─> OpenAI Chat API (GPT-4o)
        └─> Return Answer with citations
```

## Design Patterns

### 1. Repository Pattern

`VectorStoreInterface` - absztrakt repository a vector adatbázishoz

```python
class VectorStoreInterface(ABC):
    @abstractmethod
    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        pass
    
    @abstractmethod
    def search(self, query: str, top_k: int) -> List[SearchResult]:
        pass
```

### 2. Strategy Pattern

Különböző chunking stratégiák:
- `RecursiveCharacterTextSplitter` (jelenlegi)
- Könnyen lecserélhető más stratégiára

### 3. Dependency Injection

Minden függőség constructor-on keresztül injektálódik:

```python
def __init__(
    self,
    vector_store: VectorStoreInterface,
    llm_client: LLMClientInterface,
    document_loader: DocumentLoaderInterface
):
```

### 4. Factory Pattern (implicit)

`KnowledgeRouterApp.__init__()` factory-ként működik, létrehozza és összeköti a komponenseket.

## Bővítési Pontok

### Új LLM Provider

1. Implementáld a `LLMClientInterface`-t
2. Cseréld ki a DI-ban

```python
class AnthropicClient(LLMClientInterface):
    def generate_answer(self, question, context):
        # Claude API hívás
        pass
    
    def generate_embedding(self, text):
        # Anthropic embedding
        pass
```

### Új Vector Store

1. Implementáld a `VectorStoreInterface`-t
2. Cseréld ki a DI-ban

```python
class PineconeVectorStore(VectorStoreInterface):
    def add_chunks(self, chunks):
        # Pinecone upsert
        pass
    
    def search(self, query, top_k):
        # Pinecone search
        pass
```

### Új Document Format

1. Implementáld a `DocumentLoaderInterface`-t
2. Használd a megfelelő loader-t domain-enként

```python
class PDFDocumentLoader(DocumentLoaderInterface):
    def load_documents(self, directory, domain):
        # PDF parsing és chunking
        pass
```

## Tesztelhetőség

A SOLID elvek miatt minden komponens könnyen tesztelhető:

```python
# Mock LLM client
class MockLLMClient(LLMClientInterface):
    def generate_answer(self, question, context):
        return "Mock answer"
    
    def generate_embedding(self, text):
        return [0.1] * 3072

# Test
def test_rag_service():
    mock_llm = MockLLMClient()
    mock_vector = MockVectorStore()
    mock_loader = MockDocumentLoader()
    
    service = RAGService(mock_vector, mock_llm, mock_loader)
    answer = service.ask_question("test")
    
    assert answer.answer == "Mock answer"
```

## Teljesítmény Optimalizálás

### Batch Processing

- `VectorStore.add_chunks()` batch upsert (nem egyesével)
- Embedding generálás párhuzamosítható (future work)

### Caching

- Embedding cache (future work)
- Search results cache (future work)

### Retry Logic

- `@retry` decorator az OpenAI hívásokon
- Exponential backoff

## Biztonság

### API Key Management

- `.env` fájl (git ignore)
- Environment variables
- Soha ne commitolj API key-t!

### Input Validation

- Query sanitization (future work)
- Document validation (future work)

## Skálázhatóság

### Horizontális Skálázás

- Qdrant cluster mode
- Multiple app instances
- Load balancer

### Vertikális Skálázás

- Több CPU core → párhuzamos embedding
- Több RAM → nagyobb batch size
- GPU → gyorsabb embedding (ha local model)

