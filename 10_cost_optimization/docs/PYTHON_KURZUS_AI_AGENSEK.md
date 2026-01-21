# Python Kurzus: AI Ágensek Programozása

**Készült**: 2026. január 20.  
**Célközönség**: Haladó Python fejlesztők, AI mérnökök  
**Előfeltétel**: Alapvető Python ismeretek, API tapasztalat  
**Időtartam**: 8-10 óra gyakorlati anyag

---

## 📋 Tartalomjegyzék

1. [Aszinkron Python (async/await)](#1-aszinkron-python-asyncawait)
2. [Decoratorok és Metaprogramozás](#2-decoratorok-és-metaprogramozás)
3. [Type Hints és Protocol-ok](#3-type-hints-és-protocol-ok)
4. [Context Managerek](#4-context-managerek)
5. [Dependency Injection és Factory Pattern](#5-dependency-injection-és-factory-pattern)
6. [Pydantic és Adatvalidáció](#6-pydantic-és-adatvalidáció)
7. [FastAPI és REST API-k](#7-fastapi-és-rest-api-k)
8. [LangGraph és Workflow Orchestration](#8-langgraph-és-workflow-orchestration)
9. [Observability és Metrics](#9-observability-és-metrics)
10. [Best Practices AI Ágenseknél](#10-best-practices-ai-ágenseknél)

---

## 1. Aszinkron Python (async/await)

### 1.1 Mi az az Aszinkron Programozás?

Az aszinkron programozás lehetővé teszi, hogy **egyidejűleg több műveletet is végrehajtsunk** anélkül, hogy megvárnánk az egyik befejezését.

**Miért fontos AI ágenseknél?**
- LLM API hívások lassúak (1-5 másodperc)
- Több node párhuzamosan futhat
- I/O-bound műveletek (hálózat, fájl, cache)

### 1.2 Alapok: async def és await

**Fájl**: `app/nodes/triage_node.py`

```python
async def execute(self, state: AgentState) -> Dict:
    """
    Async function - nem blokkolja a programot.
    """
    # await = "várj meg, de közben más is futhat"
    cached_result = await self.cache.get(cache_key)
    
    if cached_result is not None:
        return {"classification": cached_result}
    
    # Async LLM hívás
    response = await self.llm_client.complete(
        prompt=prompt,
        model=self.model_name,
        max_tokens=10
    )
    
    return {"classification": response.content}
```

**Magyarázat:**
- `async def` = aszinkron függvény definíció
- `await` = vár az eredményre, de **nem blokkolja** a thread-et
- Más async műveletek futhatnak közben

### 1.3 Gyakorlati Példa: Párhuzamos API Hívások

```python
import asyncio

async def fetch_model_cheap(query: str):
    """Olcsó modell hívás - gyors (0.5s)"""
    await asyncio.sleep(0.5)  # Szimuláció
    return "cheap_response"

async def fetch_model_expensive(query: str):
    """Drága modell hívás - lassú (2s)"""
    await asyncio.sleep(2.0)
    return "expensive_response"

# ❌ ROSSZ: Szekvenciális - 2.5s
async def bad_approach():
    cheap = await fetch_model_cheap("query")
    expensive = await fetch_model_expensive("query")
    return cheap, expensive

# ✅ JÓ: Párhuzamos - 2s (csak a leglassabb)
async def good_approach():
    results = await asyncio.gather(
        fetch_model_cheap("query"),
        fetch_model_expensive("query")
    )
    return results

# Futtatás
import asyncio
cheap, expensive = asyncio.run(good_approach())
```

**Időbeli különbség:**
- Szekvenciális: 0.5s + 2s = **2.5s**
- Párhuzamos: max(0.5s, 2s) = **2s** (20% gyorsabb)

### 1.4 Async Cache Műveletek

**Fájl**: `app/cache/memory_cache.py`

```python
class MemoryCache:
    async def get(self, key: str) -> Optional[Any]:
        """
        Async get - non-blocking cache lookup.
        
        Miért async?
        - In-memory: gyors, de async interfész konzisztencia
        - Redis/DB cache esetén: hálózati I/O
        """
        if key not in self._cache:
            return None
        
        value, timestamp = self._cache[key]
        
        # TTL check
        if time.time() - timestamp > self._ttl:
            del self._cache[key]
            return None
        
        return value
    
    async def set(self, key: str, value: Any) -> None:
        """Async set - konzisztens interfész."""
        self._cache[key] = (value, time.time())
```

**Miért async cache in-memory esetén?**
1. **Konzisztens interfész**: Redis cache async, így minden cache async
2. **Jövőbiztos**: könnyen cserélhető Redis-re
3. **Type safety**: Cache Protocol async műveleteket ír elő

### 1.5 Async Context Manager

**Fájl**: `app/utils/timing.py`

```python
from contextlib import asynccontextmanager
import time

@asynccontextmanager
async def async_timer(callback=None):
    """
    Async context manager - időmérés.
    
    Használat:
        async with async_timer() as timer:
            await expensive_operation()
            print(f"Took {timer['elapsed']}s")
    """
    start = time.time()
    elapsed_container = {"elapsed": 0.0}
    
    try:
        yield elapsed_container
    finally:
        elapsed = time.time() - start
        elapsed_container["elapsed"] = elapsed
        if callback:
            callback(elapsed)

# Használat node-ban:
async def execute(self, state):
    async with async_timer() as timer:
        result = await self.llm_client.complete(...)
    
    logger.info(f"LLM call took {timer['elapsed']:.2f}s")
```

**Előnyök:**
- Automatikus cleanup (finally blokk)
- Elegáns szintaxis
- Exception-safe

### 1.6 FastAPI Async Endpoints

**Fájl**: `app/main.py`

```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/run")
async def run_agent(request: RunRequest):
    """
    Async endpoint - több kérést is kezel párhuzamosan.
    
    FastAPI automatikusan:
    - Több request párhuzamosan fut
    - Non-blocking I/O
    - High throughput
    """
    # Async LangGraph hívás
    result = await agent_graph.ainvoke(initial_state)
    
    return {"answer": result["final_answer"]}
```

**Teljesítmény:**
- Szinkron endpoint: 1 request/másodperc
- Async endpoint: 50-100 request/másodperc (I/O-bound esetén)

### 1.7 Gyakorló Feladatok

**Feladat 1: Párhuzamos Cache Check**

```python
async def check_multiple_caches(keys: List[str]) -> Dict[str, Any]:
    """
    Ellenőrizz több cache key-t párhuzamosan.
    
    TODO: Implementáld asyncio.gather() használatával!
    """
    # Megoldás:
    results = await asyncio.gather(
        *[cache.get(key) for key in keys]
    )
    return dict(zip(keys, results))
```

**Feladat 2: Timeout Kezelés**

```python
import asyncio

async def llm_call_with_timeout(prompt: str, timeout: float = 5.0):
    """
    LLM hívás timeout-tal.
    
    TODO: Implementáld asyncio.wait_for() használatával!
    """
    try:
        result = await asyncio.wait_for(
            llm_client.complete(prompt),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        logger.error(f"LLM call timed out after {timeout}s")
        raise HTTPException(504, "Request timeout")
```

---

## 2. Decoratorok és Metaprogramozás

### 2.1 Mi az a Decorator?

A decorator egy **függvény, ami módosít egy másik függvényt vagy osztályt**.

**Szintaxis:**
```python
@decorator_name
def function():
    pass

# Egyenértékű ezzel:
def function():
    pass
function = decorator_name(function)
```

### 2.2 Context Manager Decoratorok

**Fájl**: `app/utils/timing.py`

```python
from contextlib import contextmanager

@contextmanager
def timer(callback=None):
    """
    @contextmanager decorator - egyszerűsíti a context manager írást.
    
    Nélküle:
        class Timer:
            def __enter__(self): ...
            def __exit__(self): ...
    
    Vele:
        Csak egy függvény generator-ral.
    """
    start = time.time()
    elapsed_container = {"elapsed": 0.0}
    
    try:
        yield elapsed_container  # Itt fut a with blokk tartalma
    finally:
        # Cleanup - mindig lefut
        elapsed = time.time() - start
        elapsed_container["elapsed"] = elapsed
```

**Hogyan működik?**
1. `@contextmanager` = decorator, ami generátorból context managert csinál
2. `yield` előtti rész = `__enter__`
3. `yield` utáni rész = `__exit__`

### 2.3 Async Context Manager Decorator

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def async_timer(callback=None):
    """
    Async verzió - await-elhető műveletekhez.
    """
    start = time.time()
    elapsed = {"value": 0.0}
    
    try:
        yield elapsed
    finally:
        elapsed["value"] = time.time() - start
        if callback:
            callback(elapsed["value"])

# Használat:
async def node_execution():
    async with async_timer(lambda t: logger.info(f"Took {t}s")):
        result = await llm_client.complete(prompt)
```

**Miért kell az async verzió?**
- `yield` körül async műveletek lehetnek
- Cleanup fázisban is lehet await

### 2.4 FastAPI Route Decoratorok

**Fájl**: `app/main.py`

```python
from fastapi import FastAPI

app = FastAPI()

# @app.post = route decorator
@app.post("/run", response_model=RunResponse)
async def run_agent(request: RunRequest):
    """
    @app.post decorator hatásai:
    1. Regisztrálja az endpoint-ot
    2. POST method
    3. /run URL path
    4. Automatic request validation (RunRequest)
    5. Automatic response validation (RunResponse)
    6. OpenAPI dokumentáció generálás
    """
    return await process_request(request)

# Egyenértékű ezzel:
async def run_agent(request: RunRequest):
    return await process_request(request)

app.add_api_route(
    "/run",
    run_agent,
    methods=["POST"],
    response_model=RunResponse
)
```

**Több decorator kombinálása:**

```python
@app.post("/run")
@cache_response(ttl=60)  # Custom decorator
@rate_limit(requests=100, window=60)  # Custom decorator
async def run_agent(request: RunRequest):
    """Decoratorok alulról felfelé hajtódnak végre."""
    return result
```

### 2.5 Dataclass Decorator

**Fájl**: `app/cache/memory_cache.py`

```python
from dataclasses import dataclass

@dataclass
class CacheEntry:
    """
    @dataclass decorator automatikusan generál:
    - __init__()
    - __repr__()
    - __eq__()
    - __hash__() (ha frozen=True)
    """
    value: Any
    timestamp: float
    ttl: int

# Használat:
entry = CacheEntry(value="result", timestamp=time.time(), ttl=3600)
print(entry)  # CacheEntry(value='result', timestamp=1234567890.0, ttl=3600)
```

**Előnyök:**
- Kevesebb boilerplate kód
- Type hints támogatás
- Immutable osztályok (frozen=True)

### 2.6 Lifespan Context Manager (FastAPI)

**Fájl**: `app/main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Startup:
        - LLM client inicializálás
        - Cache setup
        - DB kapcsolat
    
    Shutdown:
        - Connection lezárás
        - Cache flush
        - Cleanup
    """
    # STARTUP - yield előtt
    logger.info("Starting application...")
    
    global llm_client, cache
    llm_client = OpenAIClient(api_key=settings.openai_api_key)
    cache = MemoryCache(ttl_seconds=3600)
    
    logger.info("Application ready")
    
    yield  # Itt fut az alkalmazás
    
    # SHUTDOWN - yield után
    logger.info("Shutting down...")
    await cache.clear()
    logger.info("Cleanup complete")

# Alkalmazás setup
app = FastAPI(lifespan=lifespan)
```

**Előnyök:**
- Központosított setup/teardown
- Exception safety
- Clean code

### 2.7 Custom Decorator Példa: Retry Logic

```python
import functools
import asyncio
from typing import Callable

def async_retry(max_retries: int = 3, delay: float = 1.0):
    """
    Retry decorator async függvényekhez.
    
    Használat:
        @async_retry(max_retries=3, delay=2.0)
        async def unstable_api_call():
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)  # Megőrzi az eredeti függvény metadatáit
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed: {e}"
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
            
            # Ha minden retry failed
            raise last_exception
        
        return wrapper
    return decorator

# Használat:
@async_retry(max_retries=5, delay=1.0)
async def call_openai_api(prompt: str):
    response = await openai.chat.completions.create(...)
    return response
```

### 2.8 Gyakorló Feladatok

**Feladat 1: Logging Decorator**

```python
def log_execution(func):
    """
    TODO: Írj decoratort, ami logolja a függvény nevét és futási idejét.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger.info(f"Executing {func.__name__}")
        start = time.time()
        
        result = await func(*args, **kwargs)
        
        elapsed = time.time() - start
        logger.info(f"{func.__name__} took {elapsed:.2f}s")
        
        return result
    return wrapper
```

**Feladat 2: Cache Decorator**

```python
def cached(ttl: int = 3600):
    """
    TODO: Írj cache decoratort függvényekhez.
    """
    def decorator(func):
        cache_dict = {}
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Cache key generálás args-ból
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # Check cache
            if cache_key in cache_dict:
                value, timestamp = cache_dict[cache_key]
                if time.time() - timestamp < ttl:
                    return value
            
            # Cache miss
            result = await func(*args, **kwargs)
            cache_dict[cache_key] = (result, time.time())
            
            return result
        return wrapper
    return decorator
```

---

## 3. Type Hints és Protocol-ok

### 3.1 Miért Fontosak a Type Hintek?

**AI ágens projekteknél kritikusak:**
1. **Code completion**: IDE segít
2. **Type safety**: Hibák a futás előtt
3. **Documentation**: Self-documenting code
4. **Refactoring**: Biztonságos változtatások

### 3.2 Alapvető Type Hints

**Fájl**: `app/nodes/triage_node.py`

```python
from typing import Dict, List, Optional, Any

async def execute(self, state: AgentState) -> Dict:
    """
    Type hints minden paraméterhez és return értékhez.
    
    state: AgentState - custom TypedDict
    -> Dict - visszatérési érték típusa
    """
    classification: str = "simple"  # Lokális változó hint
    cache_key: Optional[str] = None  # Lehet None is
    
    return {"classification": classification}
```

**Típus kategóriák:**
- `str`, `int`, `float`, `bool` - primitívek
- `List[str]` - lista string-ekből
- `Dict[str, int]` - dictionary
- `Optional[str]` - lehet str vagy None
- `Any` - bármilyen típus (kerülendő)

### 3.3 Protocol - Strukturális Típusrendszer

**Fájl**: `app/cache/interfaces.py`

```python
from typing import Protocol, Optional, Any

class Cache(Protocol):
    """
    Protocol = interfész Python-ban.
    
    Nem kell explicit implementálni (duck typing),
    elég ha a metódusok megvannak.
    """
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        ...
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value in cache."""
        ...
    
    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        ...
    
    async def clear(self) -> None:
        """Clear all cached items."""
        ...
```

**Implementáció:**

```python
class MemoryCache:
    """
    NEM kell: class MemoryCache(Cache)
    
    Elég ha a metódusok stimmelnek!
    """
    
    async def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        self._cache[key] = value
    
    # ... többi metódus
```

**Használat:**

```python
def create_node(cache: Cache):  # Protocol type hint
    """
    Elfogad BÁRMILYEN objektumot, ami megfelel a Cache protocol-nak.
    
    Lehet:
    - MemoryCache
    - RedisCache
    - FileCache
    
    Mindegy, csak a metódusok legyenek meg!
    """
    return TriageNode(cache=cache)
```

**Előnyök Protocol használata:**
- **Dependency Inversion Principle**: Függünk az absztrakciótól, nem a konkrét implementációtól
- **Testability**: Könnyű mockolni
- **Flexibility**: Könnyű cserélni az implementációt

### 3.4 LLM Client Protocol

**Fájl**: `app/llm/interfaces.py`

```python
from typing import Protocol, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class CompletionResponse:
    """Response model LLM hívásokhoz."""
    content: str
    input_tokens: int
    output_tokens: int
    latency_seconds: float
    model: str

class LLMClient(Protocol):
    """
    Protocol minden LLM client-hez.
    
    Implementációk:
    - OpenAIClient (production)
    - MockLLMClient (testing)
    - AnthropicClient (jövőbeli)
    """
    
    async def complete(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> CompletionResponse:
        """Complete text prompt."""
        ...
```

**Használat node-okban:**

```python
class TriageNode:
    def __init__(self, llm_client: LLMClient):
        """
        llm_client: LLMClient protocol
        
        Runtime-ban lehet:
        - OpenAIClient (API key van)
        - MockLLMClient (nincs API key)
        """
        self.llm_client = llm_client
    
    async def execute(self, state):
        response = await self.llm_client.complete(
            prompt="Classify this",
            model="gpt-3.5-turbo",
            max_tokens=10
        )
        return response.content
```

### 3.5 TypedDict - Strukturált Dictionary

**Fájl**: `app/graph/state.py`

```python
from typing_extensions import TypedDict
from typing import List, Dict, Any, Optional

class AgentState(TypedDict, total=False):
    """
    TypedDict = típusozott dictionary.
    
    total=False = mindegyik mező optional
    
    Előnyök:
    - IDE autocomplete működik
    - Type checker látja a hibákat
    - Self-documenting
    """
    user_input: str
    classification: Optional[str]
    retrieved_docs: List[str]
    retrieval_context: Optional[str]
    reasoning_output: Optional[str]
    final_answer: Optional[str]
    nodes_executed: List[str]
    models_used: List[str]
    timings: Dict[str, float]
    cache_hits: Dict[str, int]

# Használat:
def process_state(state: AgentState) -> AgentState:
    """
    IDE tudja, hogy state["user_input"] string!
    
    state["typo"]  # ← Type checker error!
    """
    print(state["user_input"])  # ✅ OK
    print(state["invalid_key"])  # ❌ Type error
    
    return state
```

### 3.6 Literal - Konkrét Értékek Típusa

**Fájl**: `app/graph/agent_graph.py`

```python
from typing import Literal

def route_after_triage(state: AgentState) -> Literal["retrieval", "summary"]:
    """
    Literal["retrieval", "summary"] = csak ezek a 2 string megengedett!
    
    Visszaadhat:
    - "retrieval" ✅
    - "summary" ✅
    - "something_else" ❌ Type error!
    """
    classification = state.get("classification")
    
    if classification == "simple":
        return "summary"  # ✅ OK
    
    return "retrieval"  # ✅ OK
    
    # return "invalid"  # ❌ Type checker hiba!
```

**Használat LangGraph-nál:**

```python
from langgraph.graph import StateGraph

workflow = StateGraph(AgentState)

# Conditional edges mapping
workflow.add_conditional_edges(
    "triage",
    route_after_triage,  # Literal return type
    {
        "retrieval": "retrieval",  # Literal nevek kell
        "summary": "summary"
    }
)
```

**Előnyök:**
- **Type safety**: Nem lehet elírni a routing target-et
- **Autocomplete**: IDE javasolja a lehetőségeket
- **Refactoring**: Könnyű átnevezni node-okat

### 3.7 Generic Types

```python
from typing import TypeVar, Generic, List

T = TypeVar('T')  # Generic type variable

class CacheWrapper(Generic[T]):
    """
    Generic cache - bármilyen típushoz.
    
    Használat:
        cache: CacheWrapper[str] = CacheWrapper()
        cache: CacheWrapper[int] = CacheWrapper()
    """
    
    def __init__(self):
        self._storage: Dict[str, T] = {}
    
    async def get(self, key: str) -> Optional[T]:
        return self._storage.get(key)
    
    async def set(self, key: str, value: T) -> None:
        self._storage[key] = value

# Használat:
string_cache: CacheWrapper[str] = CacheWrapper()
await string_cache.set("key", "value")  # ✅ OK
await string_cache.set("key", 123)  # ❌ Type error - int nem str!

int_cache: CacheWrapper[int] = CacheWrapper()
await int_cache.set("key", 123)  # ✅ OK
```

### 3.8 Gyakorló Feladatok

**Feladat 1: Protocol Implementáció**

```python
from typing import Protocol

class MetricsCollector(Protocol):
    """
    TODO: Definiálj Protocol-t metrikák gyűjtéséhez.
    
    Metódusok:
    - record_count(name: str, value: int)
    - record_latency(name: str, seconds: float)
    - get_metrics() -> Dict[str, Any]
    """
    pass

# Implementáció:
class PrometheusCollector:
    """TODO: Implementáld a Protocol-t."""
    pass
```

**Feladat 2: TypedDict State**

```python
from typing_extensions import TypedDict
from typing import List, Optional

class WorkflowState(TypedDict, total=False):
    """
    TODO: Definiálj state-et egy egyszerű workflow-hoz.
    
    Mezők:
    - task_name: str
    - status: Literal["pending", "running", "complete", "failed"]
    - result: Optional[str]
    - error: Optional[str]
    - start_time: float
    - end_time: Optional[float]
    """
    pass
```

---

## 4. Context Managerek

### 4.1 Mi az a Context Manager?

A context manager **automatikus resource kezelést** biztosít: setup és cleanup.

**Klasszikus példa:**

```python
# ❌ ROSSZ - file leak veszély
file = open("data.txt")
data = file.read()
# Ha exception van, file nem záródik le!

# ✅ JÓ - with statement
with open("data.txt") as file:
    data = file.read()
# Automatikusan lezárja, még exception esetén is!
```

### 4.2 Timing Context Manager

**Fájl**: `app/utils/timing.py`

```python
from contextlib import contextmanager
import time

@contextmanager
def timer(callback=None):
    """
    Időmérő context manager.
    
    Használat:
        with timer(lambda t: print(f"Took {t}s")):
            expensive_operation()
    """
    start = time.time()
    elapsed_container = {"elapsed": 0.0}
    
    try:
        yield elapsed_container  # Visszaadja a container-t
    finally:
        # MINDIG lefut, még exception esetén is!
        elapsed = time.time() - start
        elapsed_container["elapsed"] = elapsed
        
        if callback:
            callback(elapsed)

# Használat:
with timer() as t:
    process_data()
    print(f"Processing took {t['elapsed']:.2f}s")
```

**Hogyan működik?**
1. `__enter__`: `start = time.time()` + `yield`
2. `with` blokk kódja fut
3. `__exit__`: `finally` blokk (elapsed számítás, callback)

### 4.3 Async Timing Context Manager

**Ugyanaz, async verzióban:**

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def async_timer(callback=None):
    """
    Async timing - await-elhető műveletekhez.
    """
    start = time.time()
    elapsed = {"value": 0.0}
    
    try:
        yield elapsed
    finally:
        elapsed["value"] = time.time() - start
        if callback:
            callback(elapsed["value"])

# Használat:
async def node_execute():
    async with async_timer(lambda t: logger.info(f"Node took {t}s")):
        result = await llm_client.complete(prompt)
    
    return result
```

### 4.4 Gyakorlati Példa: Node Időmérés

**Fájl**: `app/nodes/triage_node.py`

```python
async def execute(self, state: AgentState) -> Dict:
    """Execute triage with automatic timing."""
    
    # Context manager timing
    async with async_timer() as timer_ctx:
        # Cache check
        cached_result = await self.cache.get(cache_key)
        
        if cached_result is not None:
            classification = cached_result
        else:
            # LLM call
            response = await self.llm_client.complete(...)
            classification = response.content
    
    # Timer automatikusan frissítette az elapsed-et
    logger.info(f"Triage took {timer_ctx['elapsed']:.3f}s")
    
    return {"classification": classification}
```

**Előnyök:**
- **Exception safe**: Mindig méri az időt, még hiba esetén is
- **Clean code**: Nem kell `try/finally` minden node-ban
- **Konzisztens**: Ugyanaz a pattern minden node-nál

### 4.5 FastAPI Lifespan Context Manager

**Fájl**: `app/main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.
    
    Startup (yield előtt):
    - Global változók inicializálása
    - DB kapcsolat
    - Cache setup
    - LLM client
    
    Shutdown (yield után):
    - Kapcsolatok lezárása
    - Cache flush
    - Cleanup
    """
    # === STARTUP ===
    global llm_client, cache, agent_graph
    
    logger.info("🚀 Starting application...")
    
    # LLM client init
    if settings.openai_api_key:
        llm_client = OpenAIClient(api_key=settings.openai_api_key)
    else:
        llm_client = MockLLMClient()
    
    # Cache init
    cache = MemoryCache(ttl_seconds=3600)
    
    # Agent graph
    agent_graph = create_agent_graph(
        llm_client=llm_client,
        cache=cache
    )
    
    logger.info("✅ Application ready")
    
    # === RUN ===
    yield  # App runs here
    
    # === SHUTDOWN ===
    logger.info("🛑 Shutting down...")
    
    await cache.clear()
    # Close DB connections
    # Flush metrics
    
    logger.info("✅ Cleanup complete")

# Create app with lifespan
app = FastAPI(lifespan=lifespan)
```

**Miért fontos?**
- **Resource management**: Nem leak-elnek a connection-ök
- **Graceful shutdown**: Adatok nem vesznek el
- **Centralizált**: Egy helyen az összes setup/teardown

### 4.6 Custom Context Manager Class

**Klasszikus __enter__/__exit__ szintaxis:**

```python
class TransactionManager:
    """
    Database transaction manager.
    
    Példa class-based context manager-re.
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.transaction = None
    
    def __enter__(self):
        """Called when entering 'with' block."""
        self.transaction = self.db.begin_transaction()
        logger.info("Transaction started")
        return self.transaction
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Called when exiting 'with' block.
        
        Args:
            exc_type: Exception type (if exception occurred)
            exc_val: Exception value
            exc_tb: Exception traceback
            
        Returns:
            False = re-raise exception
            True = suppress exception
        """
        if exc_type is None:
            # Success - commit
            self.transaction.commit()
            logger.info("Transaction committed")
        else:
            # Error - rollback
            self.transaction.rollback()
            logger.error(f"Transaction rolled back: {exc_val}")
        
        return False  # Re-raise exception

# Használat:
with TransactionManager(db) as txn:
    txn.insert("users", {"name": "John"})
    txn.insert("orders", {"user_id": 123})
    # Ha hiba van, automatikusan rollback!
```

### 4.7 Async Context Manager Class

```python
class AsyncDatabaseConnection:
    """Async DB connection manager."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
    
    async def __aenter__(self):
        """Async enter."""
        self.connection = await async_connect(self.connection_string)
        logger.info("DB connected")
        return self.connection
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async exit."""
        if self.connection:
            await self.connection.close()
            logger.info("DB connection closed")
        
        return False

# Használat:
async with AsyncDatabaseConnection("postgresql://...") as conn:
    result = await conn.execute("SELECT * FROM users")
# Connection automatikusan lezárul
```

### 4.8 Gyakorló Feladatok

**Feladat 1: Rate Limiter Context Manager**

```python
@contextmanager
def rate_limit(max_requests: int, window_seconds: int):
    """
    TODO: Írj context managert rate limiting-hez.
    
    Dobjon RateLimitError-t, ha túl sok request.
    """
    # Megoldás:
    if get_request_count(window_seconds) >= max_requests:
        raise RateLimitError("Too many requests")
    
    increment_request_count()
    
    try:
        yield
    finally:
        # Cleanup
        pass

# Használat:
with rate_limit(max_requests=100, window_seconds=60):
    process_request()
```

**Feladat 2: Metrics Context Manager**

```python
@asynccontextmanager
async def track_metrics(operation_name: str):
    """
    TODO: Írj context managert metrikák automatikus rögzítéséhez.
    
    - Mérje az időt
    - Számlálja a hívásokat
    - Rögzítse az errorokat
    """
    start = time.time()
    
    try:
        yield
        # Success
        metrics.count(f"{operation_name}_success").inc()
    except Exception as e:
        # Error
        metrics.count(f"{operation_name}_error").inc()
        raise
    finally:
        elapsed = time.time() - start
        metrics.histogram(f"{operation_name}_latency").observe(elapsed)
```

---

## 5. Dependency Injection és Factory Pattern

### 5.1 Mi az a Dependency Injection (DI)?

**Dependency Injection** = függőségek kívülről való átadása konstruktoron keresztül.

**❌ ROSSZ - Hard-coded dependency:**

```python
class TriageNode:
    def __init__(self):
        # Hard-coded - nem tesztelhető!
        self.llm_client = OpenAIClient(api_key="sk-...")
        self.cache = MemoryCache()
```

**✅ JÓ - Dependency Injection:**

```python
class TriageNode:
    def __init__(
        self,
        llm_client: LLMClient,  # Protocol!
        cache: Cache  # Protocol!
    ):
        # Kívülről kapjuk - tesztelhető!
        self.llm_client = llm_client
        self.cache = cache
```

**Előnyök:**
1. **Testability**: Mock objektumokat adhatunk át
2. **Flexibility**: Könnyen cserélhető az implementáció
3. **SOLID principles**: Dependency Inversion Principle

### 5.2 Node Dependency Injection

**Fájl**: `app/nodes/triage_node.py`

```python
from app.llm.interfaces import LLMClient
from app.cache.interfaces import Cache
from app.llm.cost_tracker import CostTracker
from app.llm.models import ModelSelector

class TriageNode:
    """
    Triage node with full DI.
    
    Minden dependency Protocol típusú!
    """
    
    def __init__(
        self,
        llm_client: LLMClient,  # ← Interfész, nem konkrét osztály!
        cost_tracker: CostTracker,
        model_selector: ModelSelector,
        cache: Cache  # ← Interfész!
    ):
        """
        Constructor injection.
        
        Args:
            llm_client: LLM client protocol
            cost_tracker: Cost tracking service
            model_selector: Model selection service
            cache: Cache protocol
        """
        self.llm_client = llm_client
        self.cost_tracker = cost_tracker
        self.model_selector = model_selector
        self.cache = cache
        
        # Model selection AFTER injection
        self.model_name = model_selector.get_model_name(ModelTier.CHEAP)
    
    async def execute(self, state: AgentState) -> Dict:
        """Execute using injected dependencies."""
        # Use protocol methods
        cached = await self.cache.get(key)
        response = await self.llm_client.complete(prompt, self.model_name)
        
        return {"classification": response.content}
```

**Használat:**

```python
# Production
llm_client = OpenAIClient(api_key=settings.api_key)
cache = MemoryCache(ttl_seconds=3600)

node = TriageNode(
    llm_client=llm_client,
    cost_tracker=cost_tracker,
    model_selector=model_selector,
    cache=cache
)

# Testing
mock_llm = MockLLMClient()
mock_cache = MockCache()

test_node = TriageNode(
    llm_client=mock_llm,  # Mock!
    cost_tracker=mock_tracker,
    model_selector=mock_selector,
    cache=mock_cache  # Mock!
)
```

### 5.3 Factory Pattern

**Fájl**: `app/graph/agent_graph.py`

```python
class AgentGraphFactory:
    """
    Factory for creating agent graphs.
    
    Centralizált dependency management és graph assembly.
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        model_selector: ModelSelector,
        cost_tracker: CostTracker,
        node_cache: Cache,
        embedding_cache: Cache
    ):
        """
        Factory constructor - minden dependency itt.
        """
        self.llm_client = llm_client
        self.model_selector = model_selector
        self.cost_tracker = cost_tracker
        self.node_cache = node_cache
        self.embedding_cache = embedding_cache
    
    def create_graph(self):
        """
        Create and assemble the full agent graph.
        
        Ez a "composition root" - itt történik minden wiring.
        """
        # Create nodes with DI
        triage_node = TriageNode(
            llm_client=self.llm_client,
            cost_tracker=self.cost_tracker,
            model_selector=self.model_selector,
            cache=self.node_cache
        )
        
        retrieval_node = RetrievalNode(
            llm_client=self.llm_client,
            cost_tracker=self.cost_tracker,
            model_selector=self.model_selector,
            embedding_cache=self.embedding_cache
        )
        
        reasoning_node = ReasoningNode(
            llm_client=self.llm_client,
            cost_tracker=self.cost_tracker,
            model_selector=self.model_selector
        )
        
        summary_node = SummaryNode(
            llm_client=self.llm_client,
            cost_tracker=self.cost_tracker,
            model_selector=self.model_selector
        )
        
        # Build LangGraph workflow
        workflow = StateGraph(AgentState)
        workflow.add_node("triage", triage_node.execute)
        workflow.add_node("retrieval", retrieval_node.execute)
        workflow.add_node("reasoning", reasoning_node.execute)
        workflow.add_node("summary", summary_node.execute)
        
        # Add edges...
        workflow.set_entry_point("triage")
        # ... routing logic ...
        
        # Compile and return
        return workflow.compile()
```

**Előnyök:**
- **Separation of Concerns**: Factory != business logic
- **Centralizált wiring**: Egy helyen minden dependency
- **Tesztelhetőség**: Factory-t mockolni könnyű

### 5.4 Convenience Factory Function

**Fájl**: `app/graph/agent_graph.py`

```python
def create_agent_graph(
    llm_client: LLMClient,
    model_selector: ModelSelector,
    cost_tracker: CostTracker,
    node_cache: Cache,
    embedding_cache: Cache
):
    """
    Convenience function - egyszerűsíti a használatot.
    
    Usage:
        graph = create_agent_graph(
            llm_client=client,
            model_selector=selector,
            cost_tracker=tracker,
            node_cache=cache1,
            embedding_cache=cache2
        )
    """
    factory = AgentGraphFactory(
        llm_client=llm_client,
        model_selector=model_selector,
        cost_tracker=cost_tracker,
        node_cache=node_cache,
        embedding_cache=embedding_cache
    )
    
    return factory.create_graph()
```

### 5.5 Application-Level DI (main.py)

**Fájl**: `app/main.py`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan - ez a ROOT composition.
    
    Itt történik az ÖSSZES dependency létrehozása és wiring.
    """
    global llm_client, model_selector, cache, agent_graph
    
    # 1. Create basic dependencies
    model_selector = ModelSelector()
    
    # 2. Create LLM client (runtime decision)
    if settings.openai_api_key:
        llm_client = OpenAIClient(api_key=settings.openai_api_key)
    else:
        llm_client = MockLLMClient(latency_ms=100)
    
    # 3. Create caches
    node_cache = MemoryCache(ttl_seconds=3600)
    embedding_cache = MemoryCache(ttl_seconds=86400)
    
    # 4. Create cost tracker
    cost_tracker = CostTracker(model_selector)
    
    # 5. Create agent graph via factory
    agent_graph = create_agent_graph(
        llm_client=llm_client,
        model_selector=model_selector,
        cost_tracker=cost_tracker,
        node_cache=node_cache,
        embedding_cache=embedding_cache
    )
    
    logger.info("✅ All dependencies wired")
    
    yield
    
    # Cleanup
    await node_cache.clear()
    await embedding_cache.clear()
```

**Dependency Graph:**

```
main.py (composition root)
  ├── ModelSelector
  ├── OpenAIClient / MockLLMClient
  ├── MemoryCache (node_cache)
  ├── MemoryCache (embedding_cache)
  ├── CostTracker
  └── AgentGraphFactory
        ├── TriageNode
        │     ├── llm_client
        │     ├── cost_tracker
        │     ├── model_selector
        │     └── node_cache
        ├── RetrievalNode
        │     ├── llm_client
        │     ├── cost_tracker
        │     ├── model_selector
        │     └── embedding_cache
        ├── ReasoningNode
        │     ├── llm_client
        │     ├── cost_tracker
        │     └── model_selector
        └── SummaryNode
              ├── llm_client
              ├── cost_tracker
              └── model_selector
```

### 5.6 Testing with DI

**Test file example:**

```python
import pytest
from app.nodes.triage_node import TriageNode
from app.llm.mock_client import MockLLMClient

@pytest.mark.asyncio
async def test_triage_node_classification():
    """Test triage node with mock dependencies."""
    
    # Create mock dependencies
    mock_llm = MockLLMClient(latency_ms=10)
    mock_cache = MockCache()
    mock_tracker = MockCostTracker()
    mock_selector = MockModelSelector()
    
    # Inject mocks
    node = TriageNode(
        llm_client=mock_llm,  # ← Mock!
        cost_tracker=mock_tracker,
        model_selector=mock_selector,
        cache=mock_cache
    )
    
    # Test
    state = {"user_input": "What is Docker?"}
    result = await node.execute(state)
    
    # Assert
    assert result["classification"] in ["simple", "retrieval", "complex"]
    assert mock_llm.call_count == 1  # Verify mock was called
```

**Előnyök:**
- Gyors tesztek (nincs hálózati hívás)
- Determinisztikus (mock mindig ugyanazt adja vissza)
- Izoláció (csak egy node-ot tesztelünk)

### 5.7 Gyakorló Feladatok

**Feladat 1: Custom Service DI**

```python
class MetricsService:
    """
    TODO: Implementálj metrics service-t DI-val.
    
    Dependencies:
    - prometheus_client (Protocol)
    - logger (logging.Logger)
    """
    
    def __init__(self, prometheus_client, logger):
        self.prometheus = prometheus_client
        self.logger = logger
    
    def record_llm_call(self, model: str, tokens: int, cost: float):
        """TODO: Record metrics."""
        pass
```

**Feladat 2: Factory with Conditional Dependencies**

```python
class CacheFactory:
    """
    TODO: Írj factory-t, ami runtime-ban dönti el melyik cache-t használja.
    
    Ha REDIS_URL van:
        RedisCache
    Különben:
        MemoryCache
    """
    
    @staticmethod
    def create(settings: Settings) -> Cache:
        if settings.redis_url:
            return RedisCache(url=settings.redis_url)
        else:
            return MemoryCache(ttl_seconds=settings.cache_ttl)
```

---

## 6. Pydantic és Adatvalidáció

### 6.1 Mi az a Pydantic?

**Pydantic** = adatvalidációs library Python-hoz, type hints alapján.

**Előnyök:**
- Automatikus validáció
- Type conversion
- JSON serialization/deserialization
- IDE support
- FastAPI integrációval

### 6.2 BaseModel - Alapok

**Fájl**: `app/main.py`

```python
from pydantic import BaseModel, Field
from typing import Optional

class RunRequest(BaseModel):
    """
    Request model a /run endpoint-hoz.
    
    Pydantic automatikusan:
    - Validálja a típusokat
    - Konvertál (str -> int, stb.)
    - Hibát dob rossz adat esetén
    """
    user_input: str = Field(..., description="User query")
    scenario: Optional[str] = Field(None, description="Optional scenario hint")

# Használat:
request_data = {
    "user_input": "What is Docker?",
    "scenario": "simple"
}

request = RunRequest(**request_data)  # ✅ Validáció sikeres
print(request.user_input)  # "What is Docker?"

# Hibás adat:
bad_data = {"user_input": 123}  # user_input nem string!
request = RunRequest(**bad_data)  # ❌ ValidationError!
```

**Field paraméterek:**
- `...` = kötelező mező
- `None` = default érték
- `description` = OpenAPI dokumentációhoz
- `min_length`, `max_length` = validációs szabályok

### 6.3 Nested Models

**Fájl**: `app/main.py`

```python
class CostBreakdown(BaseModel):
    """Nested model - cost breakdown."""
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    by_node: Dict[str, Dict[str, Any]]
    by_model: Dict[str, Dict[str, Any]]

class RunResponse(BaseModel):
    """
    Response model - tartalmaz nested model-t.
    """
    answer: str
    debug: Dict[str, Any]
    benchmark: Optional[BenchmarkSummary] = None

# JSON → Pydantic object:
response_data = {
    "answer": "Docker is a containerization platform",
    "debug": {
        "cost_report": {
            "total_input_tokens": 47,
            "total_output_tokens": 15,
            "total_cost_usd": 0.0015,
            "by_node": {...},
            "by_model": {...}
        }
    }
}

response = RunResponse(**response_data)

# Pydantic object → JSON:
json_str = response.model_dump_json()
```

### 6.4 Field Validators

```python
from pydantic import BaseModel, Field, field_validator

class QueryRequest(BaseModel):
    """Request with custom validation."""
    
    user_input: str = Field(..., min_length=1, max_length=10000)
    max_tokens: int = Field(100, ge=1, le=4000)  # ge=greater or equal
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    
    @field_validator("user_input")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Custom validator - nem lehet csak whitespace."""
        if not v.strip():
            raise ValueError("Input cannot be empty or whitespace only")
        return v.strip()
    
    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Custom validator - figyelmeztetés magas értéknél."""
        if v > 1.0:
            import warnings
            warnings.warn(f"Temperature {v} is unusually high")
        return v

# Használat:
request = QueryRequest(
    user_input="  What is Python?  ",  # Trimmed automatically
    max_tokens=500,
    temperature=0.8
)
print(request.user_input)  # "What is Python?" (trimmed)

# Hibás:
bad_request = QueryRequest(user_input="   ")  # ❌ ValidationError!
```

### 6.5 Settings Management

**Fájl**: `app/config.py`

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    Application settings - environment változókból.
    
    Pydantic automatikusan:
    - Beolvassa az .env fájlt
    - Konvertálja a típusokat
    - Validálja az értékeket
    """
    
    # API settings
    openai_api_key: Optional[str] = None
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Model settings
    model_cheap: str = "gpt-3.5-turbo"
    model_medium: str = "gpt-4-turbo"
    model_expensive: str = "gpt-4"
    
    # Cache settings
    cache_ttl_seconds: int = 3600
    cache_max_size: int = 1000
    
    class Config:
        env_file = ".env"  # Load from .env file
        case_sensitive = False  # Environment variables case-insensitive

# Használat:
settings = Settings()  # Automatikusan beolvassa az .env-t

print(settings.openai_api_key)  # Vagy None, vagy az .env-ből
print(settings.port)  # 8000 (default) vagy .env-ből
```

**.env fájl:**

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Server
PORT=8080

# Models
MODEL_CHEAP=gpt-3.5-turbo
MODEL_EXPENSIVE=gpt-4

# Cache
CACHE_TTL_SECONDS=7200
CACHE_MAX_SIZE=5000
```

**Előnyök:**
- **Type safety**: Minden setting típusozott
- **Validation**: Hibás config → startup error
- **Defaults**: Sensible defaults, de felülírható
- **Documentation**: Self-documenting

### 6.6 FastAPI Integration

**Automatikus validáció endpoint-okban:**

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.post("/run", response_model=RunResponse)
async def run_agent(request: RunRequest):
    """
    FastAPI + Pydantic magic:
    
    1. Request validation:
       - JSON → RunRequest object
       - Type checking
       - Field validation
       
    2. Response validation:
       - Return value → RunResponse
       - Type checking
       - JSON serialization
    
    3. OpenAPI docs:
       - Automatic schema generation
       - /docs endpoint
    """
    # request már validált RunRequest object!
    print(request.user_input)  # Type-safe
    
    result = await process(request)
    
    # result MUST be RunResponse, vagy ValidationError!
    return result
```

**Ha rossz adat jön:**

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_input": 123}'  # ❌ user_input nem string!

# Response:
{
  "detail": [
    {
      "loc": ["body", "user_input"],
      "msg": "str type expected",
      "type": "type_error.str"
    }
  ]
}
```

### 6.7 JSON Schema Generation

```python
from pydantic import BaseModel

class AgentMetadata(BaseModel):
    """Agent execution metadata."""
    nodes_executed: List[str]
    total_cost_usd: float
    cache_hit_ratio: float
    latency_seconds: float

# JSON schema generálás:
schema = AgentMetadata.model_json_schema()

print(schema)
# {
#   "title": "AgentMetadata",
#   "type": "object",
#   "properties": {
#     "nodes_executed": {
#       "title": "Nodes Executed",
#       "type": "array",
#       "items": {"type": "string"}
#     },
#     "total_cost_usd": {
#       "title": "Total Cost Usd",
#       "type": "number"
#     },
#     ...
#   },
#   "required": ["nodes_executed", "total_cost_usd", ...]
# }
```

**Használat:**
- OpenAPI dokumentáció
- JSON Schema validátorok
- Frontend type generation (TypeScript)

### 6.8 Gyakorló Feladatok

**Feladat 1: Model with Validation**

```python
from pydantic import BaseModel, Field, field_validator

class AgentConfig(BaseModel):
    """
    TODO: Hozz létre config modelt validációval.
    
    Mezők:
    - max_retries: int (1-10 között)
    - timeout_seconds: float (>0)
    - model_tier: Literal["cheap", "medium", "expensive"]
    - enable_cache: bool
    """
    pass
```

**Feladat 2: Nested Response Model**

```python
class NodeExecutionResult(BaseModel):
    """TODO: Node futás eredménye."""
    node_name: str
    latency_seconds: float
    input_tokens: int
    output_tokens: int
    cost_usd: float

class AgentResponse(BaseModel):
    """
    TODO: Teljes agent response nested model-lel.
    
    Mezők:
    - answer: str
    - node_results: List[NodeExecutionResult]
    - total_cost_usd: float
    """
    pass
```

---

## 7. FastAPI és REST API-k

### 7.1 FastAPI Alapok

**FastAPI** = modern, gyors web framework Python-hoz.

**Előnyök AI ágenseknél:**
- **Async support**: Nagy teljesítmény
- **Type hints**: Pydantic integráció
- **OpenAPI docs**: Automatikus dokumentáció
- **Dependency injection**: Built-in DI rendszer

### 7.2 Endpoint Definition

**Fájl**: `app/main.py`

```python
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI(
    title="AI Agent Cost Optimization Demo",
    description="Educational LangGraph demo",
    version="1.0.0"
)

@app.post("/run", response_model=RunResponse)
async def run_agent(
    request: RunRequest,
    repeat: Optional[int] = Query(None, ge=1, le=1000)
):
    """
    Run the agent workflow.
    
    Args:
        request: RunRequest body (JSON)
        repeat: Optional query param for benchmark mode
        
    Returns:
        RunResponse with answer and debug info
    """
    if repeat and repeat > 1:
        return await _run_benchmark(request, repeat)
    else:
        return await _run_single(request)
```

**URL patterns:**
- `POST /run` - single execution
- `POST /run?repeat=10` - benchmark mode

### 7.3 Request/Response Models

```python
class RunRequest(BaseModel):
    """Request body."""
    user_input: str = Field(..., description="User query")
    scenario: Optional[str] = Field(None, description="Scenario hint")

class RunResponse(BaseModel):
    """Response body."""
    answer: str
    debug: Dict[str, Any]
    benchmark: Optional[BenchmarkSummary] = None

# FastAPI automatikusan:
# 1. Validálja a request body-t
# 2. Deserializálja JSON → RunRequest
# 3. Validálja a response-t
# 4. Serializálja RunResponse → JSON
```

### 7.4 Query Parameters

```python
@app.get("/metrics")
async def get_metrics(
    node: Optional[str] = Query(None, description="Filter by node name"),
    time_range: int = Query(3600, ge=60, le=86400, description="Time range in seconds")
):
    """
    Get metrics with query parameters.
    
    URL: /metrics?node=triage&time_range=7200
    
    Query parameters:
    - node: Optional filter
    - time_range: Required, default 3600, range 60-86400
    """
    metrics = fetch_metrics(node=node, time_range=time_range)
    return metrics
```

### 7.5 Path Parameters

```python
@app.get("/agent/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """
    Path parameter example.
    
    URL: /agent/abc123/status
    agent_id = "abc123"
    """
    status = get_status(agent_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return status
```

### 7.6 Error Handling

```python
from fastapi import HTTPException

@app.post("/run")
async def run_agent(request: RunRequest):
    """Proper error handling."""
    
    try:
        result = await agent_graph.ainvoke(state)
        return result
        
    except ValueError as e:
        # Client error - bad input
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input: {str(e)}"
        )
    
    except TimeoutError:
        # Server error - timeout
        raise HTTPException(
            status_code=504,
            detail="Request timeout"
        )
    
    except Exception as e:
        # Unknown error
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
```

### 7.7 Middleware

**Fájl**: `app/observability/middleware.py`

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware = köztes réteg minden request-nél.
    
    Használat:
    - Metrics rögzítés
    - Logging
    - Authentication
    - Rate limiting
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Called for EVERY request.
        
        Args:
            request: Incoming request
            call_next: Next middleware/endpoint
        """
        # === BEFORE REQUEST ===
        start_time = time.time()
        path = request.url.path
        method = request.method
        
        logger.info(f"{method} {path} - started")
        
        # === PROCESS REQUEST ===
        try:
            response = await call_next(request)
            
            # === AFTER REQUEST (success) ===
            latency = time.time() - start_time
            status = response.status_code
            
            # Record metrics
            http_requests_total.labels(
                path=path,
                method=method,
                status=status
            ).inc()
            
            http_request_latency_seconds.labels(
                path=path,
                method=method
            ).observe(latency)
            
            logger.info(f"{method} {path} - {status} - {latency:.3f}s")
            
            return response
            
        except Exception as e:
            # === AFTER REQUEST (error) ===
            latency = time.time() - start_time
            
            logger.error(f"{method} {path} - ERROR: {e}")
            
            http_requests_total.labels(
                path=path,
                method=method,
                status=500
            ).inc()
            
            raise

# Register middleware:
app.add_middleware(MetricsMiddleware)
```

### 7.8 Lifespan Events

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle hooks.
    
    Startup:
    - DB connections
    - Cache init
    - Load models
    
    Shutdown:
    - Close connections
    - Flush caches
    - Cleanup
    """
    # STARTUP
    logger.info("🚀 Starting...")
    
    global db, cache
    db = await connect_database()
    cache = MemoryCache()
    
    logger.info("✅ Ready")
    
    yield  # App runs
    
    # SHUTDOWN
    logger.info("🛑 Shutting down...")
    
    await db.close()
    await cache.clear()
    
    logger.info("✅ Cleanup done")

app = FastAPI(lifespan=lifespan)
```

### 7.9 Gyakorló Feladatok

**Feladat 1: CRUD Endpoints**

```python
@app.post("/agents", response_model=Agent)
async def create_agent(agent: AgentCreate):
    """TODO: Create new agent."""
    pass

@app.get("/agents/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str):
    """TODO: Get agent by ID."""
    pass

@app.put("/agents/{agent_id}", response_model=Agent)
async def update_agent(agent_id: str, agent: AgentUpdate):
    """TODO: Update agent."""
    pass

@app.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """TODO: Delete agent."""
    pass
```

**Feladat 2: Rate Limiting Middleware**

```python
class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    TODO: Implementálj rate limiting middleware-t.
    
    - Max 100 req/min per IP
    - 429 status ha túllépés
    - X-RateLimit-* headerek
    """
    pass
```

---

## 8. LangGraph és Workflow Orchestration

### 8.1 Mi az a LangGraph?

**LangGraph** = workflow orchestration framework AI ágensekhez.

**Kulcs fogalmak:**
- **State**: Shared state az összes node között
- **Node**: Workflow lépés (függvény)
- **Edge**: Kapcsolat node-ok között
- **Conditional Edge**: Dinamikus routing

### 8.2 StateGraph Alapok

**Fájl**: `app/graph/state.py`

```python
from typing_extensions import TypedDict
from typing import List, Dict, Optional

class AgentState(TypedDict, total=False):
    """
    Shared state minden node számára.
    
    total=False = minden mező optional
    """
    user_input: str
    classification: Optional[str]
    retrieved_docs: List[str]
    reasoning_output: Optional[str]
    final_answer: Optional[str]
    nodes_executed: List[str]

# Node function signature:
async def node_function(state: AgentState) -> Dict:
    """
    Node function:
    - Kapja a state-et
    - Visszaad dictionary-t (state update)
    - LangGraph merge-eli a state-be
    """
    return {"classification": "simple"}
```

### 8.3 Graph Building

**Fájl**: `app/graph/agent_graph.py`

```python
from langgraph.graph import StateGraph, END

def create_graph():
    """Build LangGraph workflow."""
    
    # 1. Create graph
    workflow = StateGraph(AgentState)
    
    # 2. Add nodes
    workflow.add_node("triage", triage_node.execute)
    workflow.add_node("retrieval", retrieval_node.execute)
    workflow.add_node("reasoning", reasoning_node.execute)
    workflow.add_node("summary", summary_node.execute)
    
    # 3. Set entry point
    workflow.set_entry_point("triage")
    
    # 4. Add edges
    workflow.add_edge("reasoning", "summary")
    workflow.add_edge("summary", END)
    
    # 5. Compile
    app = workflow.compile()
    
    return app
```

### 8.4 Conditional Routing

```python
from typing import Literal

def route_after_triage(state: AgentState) -> Literal["retrieval", "summary"]:
    """
    Routing function - dönti el a következő node-ot.
    
    Returns:
        Node name (must match Literal types)
    """
    classification = state.get("classification")
    
    if classification == "simple":
        return "summary"  # Skip retrieval
    else:
        return "retrieval"  # Need docs

# Add conditional edge:
workflow.add_conditional_edges(
    "triage",  # From node
    route_after_triage,  # Routing function
    {
        "retrieval": "retrieval",  # Mapping
        "summary": "summary"
    }
)
```

### 8.5 Node Implementation Pattern

```python
class TriageNode:
    """
    Node class pattern.
    
    Best practice:
    - Dependency injection via constructor
    - execute() method returns state update
    - Logging and metrics
    """
    
    def __init__(self, llm_client: LLMClient, cache: Cache):
        self.llm_client = llm_client
        self.cache = cache
    
    async def execute(self, state: AgentState) -> Dict:
        """
        Execute node logic.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with state updates
        """
        # 1. Extract from state
        user_input = state["user_input"]
        
        # 2. Process
        classification = await self._classify(user_input)
        
        # 3. Update state
        nodes_executed = state.get("nodes_executed", [])
        nodes_executed.append("triage")
        
        # 4. Return updates
        return {
            "classification": classification,
            "nodes_executed": nodes_executed
        }
```

### 8.6 Execution

```python
# Create graph
graph = create_agent_graph(...)

# Initial state
initial_state: AgentState = {
    "user_input": "What is Docker?",
    "nodes_executed": [],
    "retrieved_docs": []
}

# Execute workflow
final_state = await graph.ainvoke(initial_state)

# Access results
print(final_state["final_answer"])
print(final_state["nodes_executed"])  # ["triage", "summary"]
```

### 8.7 Gyakorló Feladatok

**Feladat 1: Simple Workflow**

```python
def create_simple_workflow():
    """
    TODO: Hozz létre egyszerű workflow-t:
    
    START → validate → process → format → END
    
    State:
    - input: str
    - is_valid: bool
    - result: Optional[str]
    - formatted: Optional[str]
    """
    pass
```

**Feladat 2: Conditional Workflow**

```python
def create_conditional_workflow():
    """
    TODO: Workflow conditional routing-gal:
    
    START → check → (success → process → END)
                  → (failure → retry → check)
    
    Max 3 retry után END
    """
    pass
```

---

## 9. Observability és Metrics

### 9.1 Prometheus Metrics

**Fájl**: `app/observability/metrics.py`

```python
from prometheus_client import Counter, Histogram

# Counter - növekvő szám
llm_inference_count_total = Counter(
    'llm_inference_count_total',
    'Total LLM inference calls',
    ['model', 'node', 'status']  # Labels
)

# Histogram - distribution
llm_inference_latency_seconds = Histogram(
    'llm_inference_latency_seconds',
    'LLM inference latency',
    ['model', 'node'],
    buckets=[0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
)
```

**Használat:**

```python
# Increment counter
llm_inference_count_total.labels(
    model="gpt-3.5-turbo",
    node="triage",
    status="success"
).inc()

# Record latency
llm_inference_latency_seconds.labels(
    model="gpt-3.5-turbo",
    node="triage"
).observe(0.523)  # 523ms
```

### 9.2 Helper Functions

```python
def record_llm_call(
    model: str,
    node: str,
    latency: float,
    input_tokens: int,
    output_tokens: int,
    cost: float,
    status: str = "success"
):
    """
    Helper function - egyetlen hívással minden metrika.
    """
    llm_inference_count_total.labels(
        model=model,
        node=node,
        status=status
    ).inc()
    
    llm_inference_latency_seconds.labels(
        model=model,
        node=node
    ).observe(latency)
    
    llm_inference_token_input_total.labels(
        model=model,
        node=node
    ).inc(input_tokens)
    
    llm_inference_token_output_total.labels(
        model=model,
        node=node
    ).inc(output_tokens)
    
    llm_cost_total_usd.labels(
        model=model,
        node=node
    ).inc(cost)
```

### 9.3 Gyakorló Feladatok

**Feladat 1: Custom Metrics**

```python
# TODO: Definiálj metrikákat cache monitoring-hoz
cache_size_bytes = Histogram(...)
cache_eviction_total = Counter(...)
```

**Feladat 2: Metrics Middleware**

```python
class MetricsMiddleware:
    """TODO: HTTP metrics middleware."""
    
    async def dispatch(self, request, call_next):
        # Record request metrics
        pass
```

---

## 10. Best Practices AI Ágenseknél

### 10.1 Költségoptimalizálás

1. **Model tier selection**: Cheap models egyszerű feladatokhoz
2. **Prompt minimalizálás**: Rövid, hatékony promptok
3. **Caching**: Node és embedding cache
4. **Early exit**: Skip felesleges node-ok
5. **Token limits**: max_tokens beállítása

### 10.2 Teljesítmény

1. **Async everywhere**: I/O-bound műveletek async
2. **Parallel execution**: asyncio.gather()
3. **Connection pooling**: Reuse connections
4. **Caching strategies**: Multi-level cache

### 10.3 Code Quality

1. **Type hints**: Minden függvény típusozott
2. **Protocols**: Interface-alapú tervezés
3. **Dependency Injection**: Testable code
4. **Error handling**: Explicit exception kezelés

### 10.4 Observability

1. **Structured logging**: JSON logs
2. **Metrics**: Prometheus metrics minden kritikus pontnál
3. **Tracing**: Request ID végigkövetése
4. **Alerting**: Threshold-based alerts

---

## Összefoglalás

Ez a kurzus bemutatta a **Python AI ágensek fejlesztéséhez** szükséges haladó technikákat:

1. ✅ **Async/await**: Párhuzamos LLM hívások
2. ✅ **Decoratorok**: Context managerek, middleware
3. ✅ **Type hints**: Protocol-ok, TypedDict
4. ✅ **DI pattern**: Testable, flexible kód
5. ✅ **Pydantic**: Automatikus validáció
6. ✅ **FastAPI**: Modern REST API-k
7. ✅ **LangGraph**: Workflow orchestration
8. ✅ **Observability**: Prometheus metrics

**További tanuláshoz:**
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [Python Async](https://docs.python.org/3/library/asyncio.html)

---

**Készítette**: AI Agent Optimization Course  
**Verzió**: 1.0  
**Dátum**: 2026. január 20.  
**Licenc**: MIT - Oktatási célokra
