# Javítások Részletesen - Rossz verzió vs. Jó verzió

**Készült**: 2026. január 17.  
**Cél**: Részletes technikai útmutató a költségoptimalizálási javításokhoz

## 📋 Tartalomjegyzék

1. [Áttekintés](#áttekintés)
2. [Prompt Optimalizálás](#1-prompt-optimalizálás)
3. [Dinamikus Modell Választás](#2-dinamikus-modell-választás)
4. [Gyorsítótárazás Bekapcsolása](#3-gyorsítótárazás-bekapcsolása)
5. [Munkafolyamat Optimalizálás](#4-munkafolyamat-optimalizálás)
6. [Token Költségvetés Korlátozása](#5-token-költségvetés-korlátozása)
7. [Összesített Hatás](#összesített-hatás)

---

## Áttekintés

Ez a dokumentum **konkrét kód példákkal** mutatja be, hogyan kell átdolgozni egy költséges, ineffektív AI ágensrendszert egy production-ready, költségoptimalizált változattá.

### Mit tanulsz ebből a dokumentumból?

- ✅ Hogyan írj rövid, hatékony promptokat
- ✅ Hogyan válassz olcsóbb modelleket egyszerű feladatokhoz
- ✅ Hogyan implementálj node-szintű és embedding cache-t
- ✅ Hogyan kerüld el a felesleges node-ok futtatását
- ✅ Hogyan korlátozd a token outputot

### Verzió Összehasonlítás

| Metrika | Rossz verzió | Jó verzió | Javulás |
|---------|--------------|-----------|---------|
| **Költség/egyszerű lekérdezés** | $0.025 | $0.0015 | **94% csökkenés** |
| **LLM hívások/lekérdezés** | 4 (mindig) | 2-4 (adaptív) | **50% átlag** |
| **Cache találati arány** | 0% | 40-60% | **Új funkció** |
| **p95 latency** | 4-6s | 1-2s | **70% gyorsabb** |
| **Input tokenek (átlag)** | 1200 | 180 | **85% csökkenés** |
| **Output tokenek (átlag)** | 2500 | 250 | **90% csökkenés** |

---

## 1. Prompt Optimalizálás

### Probléma: Hosszú, beszédes promptok

A rossz verzióban a promptok túl hosszúak, felesleges magyarázatokkal, ami drasztikusan növeli az input token költségeket.

### ❌ ROSSZ Példa - Triage Prompt

**Fájl**: `prompts/triage_prompt.txt` (rossz verzió)

```text
Hello! I'm your friendly AI assistant, and I'm here to help you with your question today!

Before I can provide you with the most helpful and accurate response, I need to carefully analyze and classify the type of question you're asking. This is a very important step in our conversation, and I want to make sure I do it right!

Let me explain the classification system I use:

1. SIMPLE questions are straightforward queries that don't require any additional context or deep analysis. These are questions like "What is the capital of France?" or "What's 2+2?" - questions that have clear, direct answers.

2. RETRIEVAL questions are those that require me to look up specific information from a knowledge base or context...

[... további 20 sor magyarázat ...]

Here's your question that I need to classify:
{user_input}

After careful consideration and analysis of your question, taking into account all the nuances and details, my classification is:

Classification:
```

**Token szám**: ~350 input token  
**Költség**: 350 × $0.0001/1K = $0.000035 **csak a promptért**

### ✅ JÓ Példa - Optimalizált Triage Prompt

**Fájl**: `prompts/triage_prompt.txt` (jó verzió)

```text
Classify the query type. Output ONE word only.

Types:
- simple: factual, direct answer
- retrieval: requires looking up information
- complex: needs reasoning or analysis

Query: {user_input}

Classification:
```

**Token szám**: ~45 input token  
**Költség**: 45 × $0.0001/1K = $0.000045  
**Megtakarítás**: **87% kevesebb token**

### Implementáció - Prompt Betöltés

**Fájl**: `app/nodes/triage_node.py`

```python
def _build_prompt(self, user_input: str) -> str:
    """
    Build minimal classification prompt.
    
    Cost optimization: Very short prompt to minimize input tokens.
    """
    # Load optimized prompt from file
    try:
        with open("prompts/triage_prompt.txt", "r") as f:
            template = f.read()
        return template.replace("{user_input}", user_input)
    except FileNotFoundError:
        # Fallback to inline prompt
        return f"""Classify query type. Output ONE word only.

Types:
- simple: factual, direct answer
- retrieval: requires looking up information
- complex: needs reasoning or analysis

Query: {user_input}

Classification:"""
```

### Reasoning Prompt Optimalizálás

**❌ ROSSZ** (`prompts/reasoning_prompt.txt`):
```text
Greetings! I am your dedicated expert analyst, and I'm absolutely thrilled to help you work through this complex question today!

Let me introduce myself and explain my approach: I am a highly sophisticated analytical system...

[... 40 sor fölösleges bevezetés ...]
```

**✅ JÓ** (`prompts/reasoning_prompt.txt`):
```text
Analyze this complex question using step-by-step reasoning.

Question: {user_input}
{context}
Analysis:
```

**Javulás**: 95% token csökkenés a reasoning promptban

### Summary Prompt Optimalizálás

**❌ ROSSZ** (`prompts/summary_prompt.txt`):
```text
Welcome! I'm your friendly AI assistant, and I'm here to help you get the perfect answer to your question!

Thank you so much for your patience as I've been working hard to gather all the information you need...

[... 30 sor köszönetnyilvánítás és magyarázat ...]
```

**✅ JÓ** (`prompts/summary_prompt.txt`):
```text
Provide a clear, concise answer.

Question: {user_input}
{retrieval_context}{reasoning_output}
Answer:
```

### 📊 Prompt Optimalizálás Hatása

| Node | Rossz prompt (tokenek) | Jó prompt (tokenek) | Megtakarítás |
|------|------------------------|---------------------|--------------|
| Triage | 350 | 45 | **87%** |
| Reasoning | 420 | 25 | **94%** |
| Summary | 380 | 30 | **92%** |
| **Átlag** | **383** | **33** | **91%** |

---

## 2. Dinamikus Modell Választás

### Probléma: Minden feladatra a legdrágább modell

A rossz verzióban minden node GPT-4-et használ, még az egyszerű osztályozáshoz is.

### ❌ ROSSZ Implementáció

**Fájl**: `app/nodes/triage_node.py` (rossz verzió)

```python
def __init__(
    self,
    llm_client: LLMClient,
    cost_tracker: CostTracker,
    model_selector: ModelSelector,
    cache: Cache
):
    self.llm_client = llm_client
    self.cost_tracker = cost_tracker
    self.model_selector = model_selector
    self.cache = cache
    # ❌ BAD PRACTICE: Using expensive model for simple classification task
    self.model_name = model_selector.get_model_name(ModelTier.EXPENSIVE)
```

**Modell**: GPT-4  
**Költség**: $0.01/1K input, $0.03/1K output  
**Probléma**: 10-20x drágább mint kellene

### ✅ JÓ Implementáció - Triage Node

**Fájl**: `app/nodes/triage_node.py` (jó verzió)

```python
def __init__(
    self,
    llm_client: LLMClient,
    cost_tracker: CostTracker,
    model_selector: ModelSelector,
    cache: Cache
):
    self.llm_client = llm_client
    self.cost_tracker = cost_tracker
    self.model_selector = model_selector
    self.cache = cache
    # ✅ GOOD PRACTICE: Use cheapest model for simple classification
    self.model_name = model_selector.get_model_name(ModelTier.CHEAP)
```

**Modell**: GPT-3.5-turbo  
**Költség**: $0.0001/1K input, $0.0002/1K output  
**Megtakarítás**: **100x olcsóbb** input tokenekre

### ✅ JÓ Implementáció - Summary Node

**Fájl**: `app/nodes/summary_node.py` (jó verzió)

```python
def __init__(
    self,
    llm_client: LLMClient,
    cost_tracker: CostTracker,
    model_selector: ModelSelector
):
    self.llm_client = llm_client
    self.cost_tracker = cost_tracker
    self.model_selector = model_selector
    # ✅ GOOD PRACTICE: Use medium model for summary - balance quality and cost
    self.model_name = model_selector.get_model_name(ModelTier.MEDIUM)
```

**Modell**: GPT-4-turbo  
**Költség**: $0.001/1K input, $0.002/1K output  
**Előny**: Jó minőség, de 10x olcsóbb mint GPT-4

### ✅ JÓ Implementáció - Reasoning Node

**Fájl**: `app/nodes/reasoning_node.py` (változatlan)

```python
def __init__(
    self,
    llm_client: LLMClient,
    cost_tracker: CostTracker,
    model_selector: ModelSelector
):
    self.llm_client = llm_client
    self.cost_tracker = cost_tracker
    self.model_selector = model_selector
    # ✅ Expensive model justified for complex reasoning
    self.model_name = model_selector.get_model_name(ModelTier.EXPENSIVE)
```

**Modell**: GPT-4  
**Indoklás**: Csak komplex lekérdezéseknél fut, ahol megéri a magasabb minőség

### ✅ JÓ Implementáció - Retrieval Node

**Fájl**: `app/nodes/retrieval_node.py` (jó verzió)

```python
def __init__(
    self,
    llm_client: LLMClient,
    cost_tracker: CostTracker,
    model_selector: ModelSelector,
    embedding_cache: Cache
):
    self.llm_client = llm_client
    self.cost_tracker = cost_tracker
    self.model_selector = model_selector
    self.embedding_cache = embedding_cache
    # ✅ GOOD PRACTICE: Use cheap model for retrieval/embedding tasks
    self.model_name = model_selector.get_model_name(ModelTier.CHEAP)
```

### Model Tier Definíciók

**Fájl**: `app/llm/models.py`

```python
from enum import Enum

class ModelTier(str, Enum):
    """Model pricing tiers for cost optimization."""
    CHEAP = "cheap"      # gpt-3.5-turbo: $0.0001/$0.0002
    MEDIUM = "medium"    # gpt-4-turbo: $0.001/$0.002
    EXPENSIVE = "expensive"  # gpt-4: $0.01/$0.03
```

### 📊 Modell Választás Hatása

Egyszerű lekérdezés példa: "Mi az 2+2?"

| Verzió | Triage | Retrieval | Reasoning | Summary | Össz Költség |
|--------|--------|-----------|-----------|---------|--------------|
| **Rossz** | GPT-4 | GPT-4 | GPT-4 | GPT-4 | **$0.025** |
| **Jó** | GPT-3.5 | Kimarad | Kimarad | GPT-4-turbo | **$0.0015** |
| **Javulás** | 100x olcsóbb | - | - | 10x olcsóbb | **94% megtakarítás** |

---

## 3. Gyorsítótárazás Bekapcsolása

### Probléma: Gyorsítótár kikapcsolva

A rossz verzióban a cache logika megvan, de szándékosan ki van kapcsolva minden node-ban.

### ❌ ROSSZ Implementáció - Triage Cache

**Fájl**: `app/nodes/triage_node.py` (rossz verzió)

```python
async def execute(self, state: AgentState) -> Dict:
    """Execute triage node."""
    logger.info(f"Executing {self.NODE_NAME} node")
    
    async with async_timer() as timer_ctx:
        # Check cache first
        cache_key = generate_cache_key(self.NODE_NAME, state["user_input"])
        
        # ❌ BAD PRACTICE: Caching disabled - every request hits the LLM
        cache_lookup_start = time.time()
        cached_result = None  # Force cache miss
        cache_lookup_time = time.time() - cache_lookup_start
        
        if cached_result is not None:
            # This never executes...
            logger.info(f"Cache hit for {self.NODE_NAME}")
            # ...
        else:
            # Cache miss - call LLM
            logger.info(f"Cache miss for {self.NODE_NAME}")
            # ...
            response = await self.llm_client.complete(...)
            
            # ❌ BAD PRACTICE: Caching disabled - don't save results
            # await self.cache.set(cache_key, classification)
```

**Probléma**: 
- `cached_result = None` - mindig cache miss
- `await self.cache.set(...)` - ki van kommentezve
- Minden azonos lekérdezés újra hívja az LLM-et

### ✅ JÓ Implementáció - Triage Cache Bekapcsolva

**Fájl**: `app/nodes/triage_node.py` (jó verzió)

```python
async def execute(self, state: AgentState) -> Dict:
    """Execute triage node."""
    logger.info(f"Executing {self.NODE_NAME} node")
    
    async with async_timer() as timer_ctx:
        # Check cache first
        cache_key = generate_cache_key(self.NODE_NAME, state["user_input"])
        
        # ✅ GOOD PRACTICE: Enable node-level caching for triage
        cache_lookup_start = time.time()
        cached_result = await self.cache.get(cache_key)  # ← Valódi cache lookup
        cache_lookup_time = time.time() - cache_lookup_start
        
        if cached_result is not None:
            # Cache hit - skip LLM call entirely!
            logger.info(f"Cache hit for {self.NODE_NAME}")
            metrics.record_cache_lookup(
                self.CACHE_NAME,
                self.NODE_NAME,
                hit=True,
                latency=cache_lookup_time
            )
            
            classification = cached_result
        else:
            # Cache miss - call LLM
            logger.info(f"Cache miss for {self.NODE_NAME}")
            metrics.record_cache_lookup(
                self.CACHE_NAME,
                self.NODE_NAME,
                hit=False,
                latency=cache_lookup_time
            )
            
            # Load prompt and call LLM
            prompt = self._build_prompt(state["user_input"])
            response = await self.llm_client.complete(
                prompt=prompt,
                model=self.model_name,
                max_tokens=10,
                temperature=0.0
            )
            
            classification = response.content.strip().lower()
            # Normalize...
            
            # Track cost
            self.cost_tracker.track_usage(...)
            metrics.record_llm_call(...)
            
            # ✅ GOOD PRACTICE: Cache triage results for repeated queries
            await self.cache.set(cache_key, classification)  # ← Mentés cache-be
```

**Változtatások**:
1. `cached_result = await self.cache.get(cache_key)` - valódi lookup
2. `await self.cache.set(cache_key, classification)` - mentés engedélyezve
3. Cache hit esetén: **0 LLM hívás = 0 költség**

### ✅ JÓ Implementáció - Embedding Cache

**Fájl**: `app/nodes/retrieval_node.py` (jó verzió)

```python
async def _get_embedding(self, text: str) -> str:
    """
    Get embedding for text (simulated with caching).
    
    In production, this would call an embedding model.
    Cache prevents recomputing embeddings for the same text.
    """
    cache_key = generate_cache_key(self.CACHE_NAME, text)
    
    # ✅ GOOD PRACTICE: Enable embedding cache to avoid recomputation
    cache_lookup_start = time.time()
    cached_embedding = await self.embedding_cache.get(cache_key)  # ← Lookup
    cache_lookup_time = time.time() - cache_lookup_start
    
    if cached_embedding is not None:
        logger.info(f"Embedding cache hit")
        metrics.record_cache_lookup(
            self.CACHE_NAME,
            self.NODE_NAME,
            hit=True,
            latency=cache_lookup_time
        )
        return cached_embedding
    
    # Cache miss - compute embedding (simulated)
    logger.info(f"Embedding cache miss")
    metrics.record_cache_lookup(
        self.CACHE_NAME,
        self.NODE_NAME,
        hit=False,
        latency=cache_lookup_time
    )
    
    # Simulate embedding as deterministic hash
    embedding = hashlib.sha256(text.encode()).hexdigest()
    
    # ✅ GOOD PRACTICE: Cache embeddings for reuse
    await self.embedding_cache.set(cache_key, embedding)  # ← Mentés
    
    return embedding
```

### Cache Kulcs Generálás

**Fájl**: `app/cache/keys.py`

```python
import hashlib

def generate_cache_key(prefix: str, content: str) -> str:
    """
    Generate deterministic cache key.
    
    Args:
        prefix: Cache namespace (e.g., "triage", "embedding")
        content: Content to hash (e.g., user input)
    
    Returns:
        Deterministic cache key
    """
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    return f"{prefix}:{content_hash}"
```

**Példa**:
- Input: `generate_cache_key("triage", "What is Docker?")`
- Output: `"triage:a3f5c8b2e9d1f4a7"`

### 📊 Cache Hatása

Példa: Ugyanaz a lekérdezés 20x (benchmark mode)

| Futás | Cache Állapot | LLM Hívás | Költség | Latency |
|-------|---------------|-----------|---------|---------|
| 1. | Miss | ✅ Igen | $0.0015 | 1.2s |
| 2-20. | Hit | ❌ Nem | $0.0000 | 0.05s |
| **Össz** | 5% miss, 95% hit | 1 hívás | **$0.0015** | ~0.1s átlag |

**Rossz verzió ugyanerre**: 20 × $0.025 = **$0.50** (333x drágább!)

---

## 4. Munkafolyamat Optimalizálás

### Probléma: Minden node fut minden lekérdezésnél

A rossz verzióban a routing logika ignorálja a triage eredményt és minden node-ot futtat.

### ❌ ROSSZ Implementáció - Agent Graph

**Fájl**: `app/graph/agent_graph.py` (rossz verzió)

```python
def route_after_triage(state: AgentState) -> Literal["retrieval", "reasoning", "summary"]:
    """
    ❌ BAD PRACTICE: Ignoring classification - always go to retrieval.
    This ensures ALL nodes run for EVERY request, regardless of actual need.
    """
    classification = state.get("classification")
    logger.info(f"Routing decision (ignored): {classification} - ALWAYS routing to retrieval")
    
    # ❌ BAD PRACTICE: Always route to retrieval to ensure all nodes execute
    return "retrieval"

workflow.add_conditional_edges(
    "triage",
    route_after_triage,
    {
        "retrieval": "retrieval",
        "reasoning": "retrieval",  # ❌ BAD PRACTICE: Changed to always go to retrieval
        "summary": "retrieval"     # ❌ BAD PRACTICE: Changed to always go to retrieval
    }
)

# ❌ BAD PRACTICE: Chain all nodes together - retrieval → reasoning → summary
# This ensures EVERY node runs for EVERY request
workflow.add_edge("retrieval", "reasoning")
workflow.add_edge("reasoning", "summary")
```

**Probléma**:
- "What is 2+2?" → triage, retrieval, reasoning, summary (4 node)
- "Hello" → triage, retrieval, reasoning, summary (4 node)
- Összes lekérdezés **mindig 4 node-ot** futtat

### ✅ JÓ Implementáció - Intelligens Routing

**Fájl**: `app/graph/agent_graph.py` (jó verzió)

```python
def route_after_triage(state: AgentState) -> Literal["retrieval", "reasoning", "summary"]:
    """
    ✅ GOOD PRACTICE: Intelligent routing based on classification.
    
    This workflow optimization dramatically reduces costs:
    - simple: skip retrieval and reasoning, go straight to summary
    - retrieval: do retrieval, skip reasoning, then summary
    - complex: do retrieval and reasoning, then summary
    
    Graph-level caching opportunity:
    LangGraph supports graph-level persistence/checkpointing which could
    cache entire workflow executions. This would be configured via
    MemorySaver or SqliteSaver when compiling the graph.
    Example: app = workflow.compile(checkpointer=MemorySaver())
    """
    classification = state.get("classification")
    logger.info(f"Routing based on classification: {classification}")
    
    # ✅ GOOD PRACTICE: Route intelligently to skip unnecessary nodes
    if classification == "simple":
        # Simple queries: skip all intermediate steps
        return "summary"
    elif classification == "retrieval":
        # Retrieval queries: get context, then summarize
        return "retrieval"
    else:  # complex
        # Complex queries: full pipeline with retrieval and reasoning
        return "retrieval"

workflow.add_conditional_edges(
    "triage",
    route_after_triage,
    {
        "retrieval": "retrieval",
        "reasoning": "retrieval",
        "summary": "summary"  # ✅ Direct path for simple queries
    }
)

# ✅ GOOD PRACTICE: Conditional routing after retrieval
def route_after_retrieval(state: AgentState) -> Literal["reasoning", "summary"]:
    """
    Route to reasoning only for complex queries, otherwise summarize.
    """
    classification = state.get("classification")
    if classification == "complex":
        return "reasoning"
    return "summary"

workflow.add_conditional_edges(
    "retrieval",
    route_after_retrieval,
    {
        "reasoning": "reasoning",
        "summary": "summary"  # ✅ Skip reasoning for retrieval-only queries
    }
)

# Reasoning always goes to summary
workflow.add_edge("reasoning", "summary")
```

### ✅ JÓ Implementáció - Node-szintű Early Exit

**Fájl**: `app/nodes/reasoning_node.py` (jó verzió)

```python
async def execute(self, state: AgentState) -> Dict:
    """Execute reasoning node."""
    logger.info(f"Executing {self.NODE_NAME} node")
    
    # ✅ GOOD PRACTICE: Only run expensive reasoning for complex queries
    if state.get("classification") != "complex":
        logger.info("Skipping reasoning - not a complex query")
        return {
            "nodes_executed": state.get("nodes_executed", []) + [f"{self.NODE_NAME}_skipped"],
        }
    
    # Continue with expensive reasoning...
    async with async_timer() as timer_ctx:
        prompt = self._build_prompt(state["user_input"], state.get("retrieval_context"))
        
        response = await self.llm_client.complete(
            prompt=prompt,
            model=self.model_name,
            max_tokens=1000,
            temperature=0.3
        )
        # ... rest of implementation
```

**Fájl**: `app/nodes/retrieval_node.py` (jó verzió)

```python
async def execute(self, state: AgentState) -> Dict:
    """Execute retrieval node."""
    logger.info(f"Executing {self.NODE_NAME} node")
    
    # ✅ GOOD PRACTICE: Only run retrieval when classification indicates it's needed
    if state.get("classification") not in ["retrieval", "complex"]:
        logger.info("Skipping retrieval - not needed for this query type")
        return {
            "nodes_executed": state.get("nodes_executed", []) + [f"{self.NODE_NAME}_skipped"],
        }
    
    # Continue with retrieval...
    async with async_timer() as timer_ctx:
        query_embedding = await self._get_embedding(state["user_input"])
        docs = await self._retrieve_documents(state["user_input"], query_embedding)
        # ... rest of implementation
```

### 📊 Routing Hatása

| Lekérdezés Típus | Rossz Verzió | Jó Verzió | Node Megtakarítás |
|------------------|--------------|-----------|-------------------|
| "What is 2+2?" | triage → retrieval → reasoning → summary (4) | triage → summary (2) | **50%** |
| "Find Docker docs" | triage → retrieval → reasoning → summary (4) | triage → retrieval → summary (3) | **25%** |
| "Design distributed system" | triage → retrieval → reasoning → summary (4) | triage → retrieval → reasoning → summary (4) | **0%** (szükséges) |
| **Átlag** | **4 node/lekérdezés** | **2.5 node/lekérdezés** | **~40%** |

---

## 5. Token Költségvetés Korlátozása

### Probléma: Túl magas max_tokens értékek

A rossz verzióban minden node feleslegesen magas `max_tokens` limitet használ.

### ❌ ROSSZ Implementáció - Pazarló Token Limitek

**Fájl**: `app/nodes/triage_node.py` (rossz verzió)

```python
response = await self.llm_client.complete(
    prompt=prompt,
    model=self.model_name,
    max_tokens=2000,  # ❌ Wastefully high for one-word answer
    temperature=0.0
)
```

**Probléma**: Csak egy szót várunk ("simple", "retrieval", "complex"), de 2000 tokent engedélyezünk

**Fájl**: `app/nodes/reasoning_node.py` (rossz verzió)

```python
response = await self.llm_client.complete(
    prompt=prompt,
    model=self.model_name,
    max_tokens=3000,  # ❌ Wastefully high
    temperature=0.3
)
```

**Probléma**: 3000 token = ~2250 szó, sokkal több mint kellene

**Fájl**: `app/nodes/summary_node.py` (rossz verzió)

```python
response = await self.llm_client.complete(
    prompt=prompt,
    model=self.model_name,
    max_tokens=2000,  # ❌ Wastefully high for summary
    temperature=0.5
)
```

**Probléma**: Az összefoglaló rövid kell legyen, 2000 token felesleges

### ✅ JÓ Implementáció - Szigorú Token Limitek

**Fájl**: `app/nodes/triage_node.py` (jó verzió)

```python
response = await self.llm_client.complete(
    prompt=prompt,
    model=self.model_name,
    max_tokens=10,  # ✅ Only need one word
    temperature=0.0  # Deterministic
)
```

**Indoklás**: 
- Kimenet: "simple" (1 token), "retrieval" (1 token), "complex" (1 token)
- 10 token: biztonságos margó
- **200x kevesebb** mint a rossz verzió

**Fájl**: `app/nodes/reasoning_node.py` (jó verzió)

```python
response = await self.llm_client.complete(
    prompt=prompt,
    model=self.model_name,
    max_tokens=1000,  # ✅ Sufficient for most complex queries
    temperature=0.3  # Lower for more focused reasoning
)
```

**Indoklás**:
- 1000 token = ~750 szó
- Elég a legtöbb komplex elemzéshez
- **3x kevesebb** mint a rossz verzió

**Fájl**: `app/nodes/summary_node.py` (jó verzió)

```python
response = await self.llm_client.complete(
    prompt=prompt,
    model=self.model_name,
    max_tokens=500,  # ✅ Enough for quality summary
    temperature=0.5  # Balanced creativity
)
```

**Indoklás**:
- 500 token = ~375 szó
- Elegendő egy jó összefoglalóhoz
- **4x kevesebb** mint a rossz verzió
- Kényszerít tömör válaszokra

### 📊 Token Limit Hatása

GPT-4 output tokenek árazása: **$0.03/1K**

| Node | Rossz max_tokens | Jó max_tokens | Megtakarítás | Költség csökkenés |
|------|------------------|---------------|--------------|-------------------|
| Triage | 2000 | 10 | **99.5%** | $0.06 → $0.0003 |
| Reasoning | 3000 | 1000 | **66%** | $0.09 → $0.03 |
| Summary | 2000 | 500 | **75%** | $0.06 → $0.015 |

**Példa számítás** (complex lekérdezés, mind a 3 node fut):
- Rossz verzió: 2000 + 3000 + 2000 = 7000 max tokens → **$0.21** potenciális költség
- Jó verzió: 10 + 1000 + 500 = 1510 max tokens → **$0.045** potenciális költség
- **Megtakarítás: 78%**

### A max_tokens Fontossága

1. **Költség kontroll**: Output tokenek gyakran drágábbak mint input
2. **Latency kontroll**: Kevesebb token = gyorsabb generálás
3. **Minőség kontroll**: Kényszerít tömörségre, jobb válaszokat eredményez
4. **Kiszámíthatóság**: Fix felső limit a költségekre

---

## Összesített Hatás

### Teljes Példa: Egyszerű Lekérdezés

**Lekérdezés**: "What is 2+2?"

#### ❌ Rossz Verzió Végrehajtás

```
1. TRIAGE NODE
   - Model: GPT-4 ($0.01/$0.03)
   - Prompt: 350 tokens
   - Max tokens: 2000
   - Output: ~5 tokens ("simple")
   - Költség: (350 × 0.01 + 5 × 0.03) / 1000 = $0.0035 + $0.00015 = $0.00365
   - Cache: Nincs

2. RETRIEVAL NODE (felesleges!)
   - Model: GPT-4
   - Embedding compute + lookup
   - Költség: ~$0.004
   - Cache: Nincs

3. REASONING NODE (felesleges!)
   - Model: GPT-4
   - Prompt: 420 tokens
   - Max tokens: 3000
   - Output: ~800 tokens
   - Költség: (420 × 0.01 + 800 × 0.03) / 1000 = $0.0042 + $0.024 = $0.0282
   - Cache: Nincs

4. SUMMARY NODE
   - Model: GPT-4
   - Prompt: 380 tokens
   - Max tokens: 2000
   - Output: ~150 tokens
   - Költség: (380 × 0.01 + 150 × 0.03) / 1000 = $0.0038 + $0.0045 = $0.0083

ÖSSZ KÖLTSÉG: $0.00365 + $0.004 + $0.0282 + $0.0083 = $0.04415
LATENCY: ~5 seconds
NODES: 4
```

#### ✅ Jó Verzió Végrehajtás (első futás)

```
1. TRIAGE NODE
   - Model: GPT-3.5-turbo ($0.0001/$0.0002)
   - Prompt: 45 tokens
   - Max tokens: 10
   - Output: 1 token ("simple")
   - Költség: (45 × 0.0001 + 1 × 0.0002) / 1000 = $0.0000045 + $0.0000002 = $0.0000047
   - Cache: Miss → mentés

2. RETRIEVAL NODE
   - SKIPPED (routing: simple → summary)

3. REASONING NODE
   - SKIPPED (routing: simple → summary)

4. SUMMARY NODE
   - Model: GPT-4-turbo ($0.001/$0.002)
   - Prompt: 30 tokens
   - Max tokens: 500
   - Output: ~20 tokens
   - Költség: (30 × 0.001 + 20 × 0.002) / 1000 = $0.00003 + $0.00004 = $0.00007

ÖSSZ KÖLTSÉG: $0.0000047 + $0.00007 = $0.0000747
LATENCY: ~1.2 seconds
NODES: 2
```

#### ✅ Jó Verzió Végrehajtás (második futás - cache hit)

```
1. TRIAGE NODE
   - Cache HIT! → "simple"
   - LLM hívás: NINCS
   - Költség: $0.00000
   - Latency: ~5ms

2. RETRIEVAL NODE
   - SKIPPED

3. REASONING NODE
   - SKIPPED

4. SUMMARY NODE
   - Model: GPT-4-turbo
   - Költség: ~$0.00007

ÖSSZ KÖLTSÉG: $0.00007
LATENCY: ~0.5 seconds
NODES: 2 (1 cached)
```

### Összehasonlítás

| Metrika | Rossz | Jó (1. futás) | Jó (2. futás) |
|---------|-------|---------------|---------------|
| **Költség** | $0.044 | $0.000075 | $0.00007 |
| **Latency** | 5s | 1.2s | 0.5s |
| **LLM hívások** | 4 | 2 | 1 |
| **Node-ok** | 4 | 2 | 2 |
| **Cache használat** | 0% | 50% | 50% |

**Megtakarítás**:
- Első futás: **99.8%** költség csökkenés
- Második futás: **99.84%** költség csökkenés
- Latency javulás: **76-90%**

### Skálázhatósági Hatás

**Havi 100,000 lekérdezés** (50% egyszerű, 30% retrieval, 20% komplex):

| Verzió | Havi Költség | Éves Költség |
|--------|--------------|--------------|
| Rossz | **$2,200** | **$26,400** |
| Jó (cache nélkül) | **$150** | **$1,800** |
| Jó (40% cache hit) | **$90** | **$1,080** |

**Megtakarítás**: **$25,320/év** (96% csökkenés)

---

## Implementálási Checklist Hallgatóknak

### 1. Prompt Optimalizálás ✅

- [ ] Töröld az összes felesleges bevezetőt és magyarázatot
- [ ] Használj rövid, utasításszerű nyelvezetet
- [ ] Csak a szükséges információkat add meg
- [ ] Teszteld: minimum 80% token csökkenés

**Fájlok**:
- `prompts/triage_prompt.txt`
- `prompts/reasoning_prompt.txt`
- `prompts/summary_prompt.txt`

### 2. Modell Választás ✅

- [ ] Triage node: `ModelTier.CHEAP`
- [ ] Retrieval node: `ModelTier.CHEAP`
- [ ] Summary node: `ModelTier.MEDIUM`
- [ ] Reasoning node: `ModelTier.EXPENSIVE` (csak ha szükséges)

**Fájlok**:
- `app/nodes/triage_node.py` - `__init__` metódus
- `app/nodes/retrieval_node.py` - `__init__` metódus
- `app/nodes/summary_node.py` - `__init__` metódus

### 3. Cache Engedélyezése ✅

- [ ] Triage node: `cached_result = await self.cache.get(cache_key)`
- [ ] Triage node: `await self.cache.set(cache_key, classification)`
- [ ] Retrieval node: `cached_embedding = await self.embedding_cache.get(cache_key)`
- [ ] Retrieval node: `await self.embedding_cache.set(cache_key, embedding)`

**Fájlok**:
- `app/nodes/triage_node.py` - `execute` metódus
- `app/nodes/retrieval_node.py` - `_get_embedding` metódus

### 4. Conditional Routing ✅

- [ ] Implementáld `route_after_triage` intelligens logikával
- [ ] Implementáld `route_after_retrieval` intelligens logikával
- [ ] Add hozzá early exit logikát a reasoning node-hoz
- [ ] Add hozzá early exit logikát a retrieval node-hoz

**Fájlok**:
- `app/graph/agent_graph.py` - routing függvények
- `app/nodes/reasoning_node.py` - `execute` metódus elején
- `app/nodes/retrieval_node.py` - `execute` metódus elején

### 5. Token Limitek ✅

- [ ] Triage: `max_tokens=10`
- [ ] Reasoning: `max_tokens=1000`
- [ ] Summary: `max_tokens=500`

**Fájlok**:
- `app/nodes/triage_node.py` - `execute` metódus, `llm_client.complete` hívás
- `app/nodes/reasoning_node.py` - `execute` metódus, `llm_client.complete` hívás
- `app/nodes/summary_node.py` - `execute` metódus, `llm_client.complete` hívás

---

## Tesztelés

### Lokális Teszt

```bash
# Indítsd el a szolgáltatásokat
docker compose up --build

# Teszt: egyszerű lekérdezés
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": "What is 2+2?"}'

# Elvárt eredmény:
# - nodes_executed: ["triage", "summary"]
# - cache_hits: {triage: false} (első futás)
# - models_used: ["gpt-3.5-turbo", "gpt-4-turbo"]
# - total_cost_usd: ~$0.00008
```

### Cache Teszt

```bash
# Ugyanaz a lekérdezés 3x
for i in {1..3}; do
  curl -X POST http://localhost:8000/run \
    -H "Content-Type: application/json" \
    -d '{"user_input": "What is Docker?"}'
  echo ""
  sleep 2
done

# Elvárt:
# 1. futás: cache_hits: {triage: false}
# 2. futás: cache_hits: {triage: true}  ← FONTOS!
# 3. futás: cache_hits: {triage: true}
```

### Grafana Metrikák

Nyisd meg: http://localhost:3000

Ellenőrizd:
- ✅ `llm_inference_count_total{model="gpt-3.5-turbo"}` - nő (triage)
- ✅ `llm_inference_count_total{model="gpt-4-turbo"}` - nő (summary)
- ✅ `llm_inference_count_total{model="gpt-4"}` - NEM nő (egyszerű lekérdezéseknél)
- ✅ `cache_hit_total{cache="node_cache"}` - nő a második futástól
- ✅ `llm_cost_total_usd` - alacsony marad

---

## Gyakori Hibák és Megoldások

### Hiba 1: Cache nem működik

**Tünet**: `cache_hits` mindig `false`

**Ok**: Elfelejtettél `await` kulcsszót használni

```python
# ❌ ROSSZ
cached_result = self.cache.get(cache_key)  # Nem await!

# ✅ JÓ
cached_result = await self.cache.get(cache_key)
```

### Hiba 2: Minden node mindig fut

**Tünet**: `nodes_executed` mindig 4 node

**Ok**: Nem implementáltad a conditional routing-ot

**Megoldás**: Ellenőrizd `app/graph/agent_graph.py` routing logikát

### Hiba 3: Még mindig drága

**Tünet**: `total_cost_usd` > $0.01 egyszerű lekérdezésnél

**Ok**: 
1. Nem cserélt a cheap model-re a triage
2. Nem csökkentetted a max_tokens-t
3. Verbose prompts használata

**Megoldás**: Ellenőrizd mind az 5 javítási pontot

### Hiba 4: SyntaxError a promptokban

**Tünet**: Prompt fájl betöltési hiba

**Ok**: Elfelejtett `"""` a docstring-ben

**Megoldás**: Ellenőrizd az idézőjeleket:
```python
def _build_prompt(self, state: AgentState) -> str:
    """
    Build prompt.
    """  # ← Fontos: 3 idézőjel
    # ...
```

---

## Következő Lépések

1. ✅ Implementáld mind az 5 javítást
2. ✅ Teszteld lokálisan
3. ✅ Ellenőrizd a Grafana metrikákat
4. ✅ Dokumentáld a változtatásokat
5. ✅ Commit-old a kódot git-be

**Sikeres implementáció jele**:
- 90%+ költség csökkenés
- 40%+ cache hit ratio (második futástól)
- 2-3 node átlagosan (nem mindig 4)
- Sub-second latency cache hit esetén

---

**Készítette**: AI Agent Optimization Course  
**Dátum**: 2026. január 17.  
**Verzió**: 1.0  
**Licenc**: MIT - Oktatási célokra
