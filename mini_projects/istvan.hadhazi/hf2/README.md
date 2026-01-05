# AI Knowledge Router - RAG System

**Házi Feladat #2 - AI Internal Knowledge Router & Workflow Automation Agent**

Multi-domain tudásbázis rendszer RAG (Retrieval-Augmented Generation) technológiával.

## Leírás

Ez az alkalmazás egy intelligens tudásirányító, amely:
- 📚 Több domain tudásbázist kezel (IT, HR, Finance)
- 🔍 Szemantikus keresés vector embeddings segítségével
- 🤖 GPT-4o alapú válaszgenerálás forrás citációkkal
- 📝 Markdown dokumentumok automatikus betöltése és chunkolása

## Architektúra

A projekt SOLID elvek szerint épül:

```
hf2/
├── domain/                 # Domain layer (models, interfaces)
│   ├── models.py          # Data models
│   └── interfaces.py      # Abstract interfaces
├── infrastructure/         # Infrastructure layer
│   ├── vector_store.py    # Qdrant vector store
│   ├── llm_client.py      # OpenAI client
│   └── document_loader.py # Document chunking & loading
├── services/              # Business logic
│   └── rag_service.py     # RAG implementation
├── documents/             # Knowledge base
│   ├── it/               # IT domain documents
│   ├── hr/               # HR domain documents
│   └── finance/          # Finance domain documents
├── app.py                # Main application
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Technológiai Stack

- **Python 3.11+**
- **OpenAI GPT-4o** - LLM
- **OpenAI text-embedding-3-large** - Embeddings
- **Qdrant** - Vector database
- **LangChain** - Document processing
- **SOLID principles** - Clean architecture

## Funkciók

✅ **Multi-domain tudásbázis**
- IT: VPN, software, hardware support
- HR: szabadság, benefits, policy
- Finance: költségek, számla, fizetés

✅ **RAG Pipeline**
1. Document chunking (500 token chunks, 50 overlap)
2. Embedding generation (OpenAI)
3. Vector search (top-5 similarity)
4. Context-aware answer generation
5. Source citation

✅ **Interaktív konzol**
- Kérdés-válasz interfész
- Forrás dokumentumok megjelenítése
- Relevancia score mutatása

## Gyors Indítás

### 1. Környezeti változók

```bash
cd mini_projects/istvan.hadhazi/hf2
cp env.example .env
```

Szerkeszd a `.env` fájlt:
```env
OPENAI_API_KEY=sk-your-api-key-here
```

### 2. Docker indítás

```bash
# Teljes stack (Qdrant + App)
docker-compose up --build

# Vagy Makefile-lal
make run
```

### 3. Lokális futtatás

```bash
# Qdrant indítása
docker run -p 6333:6333 qdrant/qdrant

# Python környezet
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Indítás
python app.py
```

## Használat

Az alkalmazás indítása után:

```
====================================
  AI Knowledge Router - RAG System
====================================

Dokumentumok betöltése...
✓ IT: 3 dokumentum (5 chunk)
✓ HR: 2 dokumentum (4 chunk)  
✓ Finance: 2 dokumentum (3 chunk)

Összesen: 7 dokumentum, 12 chunk

Kérdezz bármit! ('exit' - kilépés)
-----------------------------------

Kérdés: Hogyan igényeljek szabadságot?

🔍 Releváns dokumentumok:
  [1] hr/szabadsag_policy.md (0.89)
  [2] hr/benefits.md (0.75)

📄 Válasz:
A szabadságigényléshez...

[Forrás: hr/szabadsag_policy.md]

---

Kérdés: exit
Viszlát!
```

## Példa Kérdések

**IT Domain:**
- "Hogyan kapcsolódjak a VPN-hez?"
- "Milyen szoftvereket telepíthetek?"
- "Nem működik a gépem, mit tegyek?"

**HR Domain:**
- "Mennyi szabadság jár nekem?"
- "Hogyan igényeljek home office-t?"
- "Mik a benefit lehetőségeim?"

**Finance Domain:**
- "Hogyan nyújtsak be költségtérítést?"
- "Mikor érkezik a fizetés?"
- "Milyen költségeket térítetek?"

## Konfiguráció

`.env` fájl beállítások:

```env
# OpenAI
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=knowledge_base

# RAG
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RESULTS=5
```

## Dokumentum Hozzáadása

Új dokumentumok hozzáadása egyszerű:

```bash
# 1. Hozz létre egy új .md fájlt
echo "# Új IT Policy" > documents/it/new_policy.md

# 2. Töltsd be újra az adatbázist
python app.py
```

A dokumentumok automatikusan betöltődnek indításkor.

## Projekt Jellemzők

### SOLID Principles

- **S** - Single Responsibility: Minden osztály egy felelősséggel
- **O** - Open/Closed: Bővíthető új domain-ekkel
- **L** - Liskov Substitution: Interface-ek használata
- **I** - Interface Segregation: Kisebb, specifikus interface-ek
- **D** - Dependency Inversion: Abstrakciókra épül

### Design Patterns

- **Repository Pattern** - Vector store abstrakció
- **Strategy Pattern** - Különböző chunking stratégiák
- **Factory Pattern** - Document loader factory

## Bővítési Lehetőségek

Későbbi fejlesztések (nem része ennek a HF-nak):

- [ ] LangGraph workflow integration
- [ ] Multi-step reasoning
- [ ] Workflow automation
- [ ] Domain routing optimization
- [ ] Citation tracking
- [ ] Answer quality metrics

## Követelmények

- Python 3.11+
- Docker (Qdrant futtatásához)
- OpenAI API key

## Licenc

MIT License

