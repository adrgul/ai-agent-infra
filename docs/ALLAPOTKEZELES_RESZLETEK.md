# AI Agent Állapotkezelés - Részletes Útmutató

## Tartalomjegyzék

1. [Bevezetés - Mi az Agent Állapot?](#1-bevezetés---mi-az-agent-állapot)
2. [Állapot Típusok](#2-állapot-típusok)
3. [Állapotkezelési Módszerek](#3-állapotkezelési-módszerek)
4. [Tárolási Megoldások](#4-tárolási-megoldások)
5. [Production Környezet - AWS](#5-production-környezet---aws)
6. [Kód Példák és Konfiguráció](#6-kód-példák-és-konfiguráció)
7. [Best Practices](#7-best-practices)

---

## 1. Bevezetés - Mi az Agent Állapot?

Az AI agent állapota **minden olyan adat, amely szükséges a workflow végrehajtásához és követéséhez**. Ez magában foglalja:

- **User input**: a felhasználó kérdése
- **Intermediate results**: köztes eredmények (klasszifikáció, retrieval, reasoning)
- **Final output**: végső válasz
- **Metadata**: futási metaadatok (időzítés, költségek, cache találatok)

### Állapot Lifecycle

```
┌─────────────┐
│  API Call   │  
│  /run       │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Initial State      │  ← State létrehozás (üres mezőkkel)
│  Created            │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Triage Node        │  ← State frissítés: classification
│  Executes           │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Retrieval Node     │  ← State frissítés: retrieved_docs
│  Executes           │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Reasoning Node     │  ← State frissítés: reasoning_output
│  Executes           │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Summary Node       │  ← State frissítés: final_answer
│  Executes           │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Final State        │  ← State visszaadása API válaszban
│  Returned           │
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│  State Discarded    │  ← Állapot megsemmisül (stateless!)
└─────────────────────┘
```

---

## 2. Állapot Típusok

### 2.1 Workflow Állapot (Execution State)

**Definíció:** Az egyetlen kérés végrehajtása során áthaladó adat.

**Lifetime:** Egy API hívás időtartama (~1-10 másodperc)

**Ahol tároljuk:** Memória (Python objektum)

**Példa kód - `app/graph/state.py`:**

```python
from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """
    Workflow execution state.
    
    Ez az állapot egy kérés teljes életciklusa alatt él,
    majd eldobásra kerül a válasz visszaadása után.
    
    MINDEN node látja és módosíthatja ezt az állapotot.
    """
    
    # ============ INPUT ============
    user_input: str                      # Felhasználó kérdése
    scenario: Optional[str]              # Opcionális scenario hint
    
    # ============ NODE OUTPUTS ============
    # Triage node output
    classification: Optional[str]        # "simple" | "retrieval" | "complex"
    
    # Retrieval node output
    retrieved_docs: List[str]            # Visszakeresett dokumentumok
    retrieval_context: Optional[str]     # Összefűzött kontextus
    
    # Reasoning node output
    reasoning_output: Optional[str]      # Reasoning eredmény
    
    # Summary node output
    final_answer: Optional[str]          # Végső válasz
    
    # ============ METADATA ============
    nodes_executed: List[str]            # Végrehajtott node-ok listája
    models_used: List[str]               # Használt LLM modellek
    timings: Dict[str, float]            # Node-onkénti futási idők (mp)
    cache_hits: Dict[str, bool]          # Cache találatok node-onként
```

**Használat a node-okban:**

```python
# app/nodes/triage_node.py - részlet

async def execute(self, state: AgentState) -> Dict:
    """
    Triage node execution.
    
    Args:
        state: Bejövő állapot (user_input-tal)
        
    Returns:
        State frissítések (merge-elődnek a jelenlegi state-be)
    """
    user_input = state["user_input"]  # Olvasás
    
    # ... LLM hívás, klasszifikáció ...
    
    # State frissítés - csak az új mezőket adjuk vissza
    return {
        "classification": classification,
        "nodes_executed": state.get("nodes_executed", []) + ["triage"],
        "models_used": state.get("models_used", []) + [self.model_name],
        "timings": {
            **state.get("timings", {}),
            "triage": execution_time
        },
        "cache_hits": {
            **state.get("cache_hits", {}),
            "triage": cache_hit
        }
    }
```

### 2.2 Cache Állapot (Cached Data)

**Definíció:** Előző futások eredményeinek tárolása a gyorsabb válaszadáshoz.

**Lifetime:** Konfigurálható TTL (pl. 1 óra)

**Ahol tároljuk:** Memória (MemoryCache) vagy Redis (production-ben)

**Példa - `app/cache/memory_cache.py`:**

```python
"""
In-memory cache implementation with TTL support.
"""
import asyncio
import time
from typing import Optional, Any, Dict
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """
    Cache entry with expiration.
    
    Minden cache bejegyzés tartalmazza:
    - value: a tárolt adat (pl. LLM válasz)
    - expires_at: lejárati időbélyeg (Unix timestamp)
    """
    value: Any
    expires_at: float


class MemoryCache:
    """
    TTL-alapú memória cache.
    
    ÁLLAPOT TÍPUS: Cached data
    LIFETIME: cache_ttl_seconds (pl. 3600 mp = 1 óra)
    SCOPE: Alkalmazás szintű (minden kérés megosztja)
    PERSISTENCE: Nincs - újraindításkor elvész
    """
    
    def __init__(self, default_ttl_seconds: int = 3600, max_size: int = 1000):
        """
        Args:
            default_ttl_seconds: Alapértelmezett TTL (másodperc)
            max_size: Maximum cache bejegyzések száma
        """
        self.default_ttl = default_ttl_seconds
        self.max_size = max_size
        self._store: Dict[str, CacheEntry] = {}  # ← ÁLLAPOT ITT
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Érték lekérése cache-ből.
        
        Ha lejárt vagy nincs -> None
        Ha érvényes -> érték
        """
        async with self._lock:
            entry = self._store.get(key)
            
            if entry is None:
                return None
            
            # Lejárat ellenőrzés
            if time.time() > entry.expires_at:
                del self._store[key]  # Törlés
                return None
            
            return entry.value
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """
        Érték tárolása cache-ben TTL-lel.
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expires_at = time.time() + ttl
        
        async with self._lock:
            # LRU eviction ha megtelt
            if len(self._store) >= self.max_size and key not in self._store:
                oldest_key = next(iter(self._store))
                del self._store[oldest_key]
            
            self._store[key] = CacheEntry(value=value, expires_at=expires_at)
```

**Cache használat példa:**

```python
# app/nodes/triage_node.py - cache használat

from app.cache.keys import generate_cache_key

async def execute(self, state: AgentState) -> Dict:
    """Triage node with caching."""
    
    user_input = state["user_input"]
    
    # Cache kulcs generálás (hash alapú)
    cache_key = generate_cache_key("triage", user_input)
    
    # 1. Cache lookup
    cached_result = await self.cache.get(cache_key)
    
    if cached_result is not None:
        # Cache HIT - nincs LLM hívás!
        logger.info("Cache HIT - returning cached classification")
        return {
            "classification": cached_result,
            "cache_hits": {..., "triage": True}
        }
    
    # 2. Cache MISS - LLM hívás szükséges
    logger.info("Cache MISS - calling LLM")
    response = await self.llm_client.complete(prompt, model)
    classification = response.content.strip()
    
    # 3. Cache mentés
    await self.cache.set(cache_key, classification)
    
    return {
        "classification": classification,
        "cache_hits": {..., "triage": False}
    }
```

### 2.3 Perzisztens Állapot (Conversation History)

**Definíció:** Hosszabb távú tárolás (multi-turn conversation, session history).

**Lifetime:** Session lifetime (órák/napok) vagy végtelen

**Ahol tároljuk:** Database (PostgreSQL, DynamoDB) vagy LangGraph Checkpointer

**FONTOS:** Ebben a projektben **NEM HASZNÁLJUK** - minden kérés stateless!

**Elméleti példa (LangGraph checkpointer):**

```python
# NEM HASZNÁLT - csak példa

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.postgres import PostgresSaver

# Memory-based persistence (csak development)
checkpointer = MemorySaver()

# SQLite-based persistence
checkpointer = SqliteSaver.from_conn_string("checkpoints.db")

# PostgreSQL-based persistence (production)
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:pass@host:5432/db"
)

# Graph compile checkpointer-rel
app = workflow.compile(checkpointer=checkpointer)

# Használat thread_id-val (session azonosító)
config = {"configurable": {"thread_id": "user_123_session_456"}}

# Első kérés - state mentésre kerül
result1 = await app.ainvoke(
    {"user_input": "What is AI?"},
    config=config
)

# Második kérés - előző state betöltődik
result2 = await app.ainvoke(
    {"user_input": "Tell me more"},
    config=config  # Ugyanaz a thread_id!
)
```

**Miért NEM használjuk ebben a projektben?**

1. **Egyszerűség**: Minden kérés független (stateless API)
2. **Költség optimalizálás**: Nem kell database-t fenntartani
3. **Skálázhatóság**: Könnyebb horizontal scaling
4. **Oktatási célok**: Fókusz a workflow optimalizáláson, nem session managementen

---

## 3. Állapotkezelési Módszerek

### 3.1 LangGraph State Management

**Módszer:** TypedDict-based state dictionary, node-ok közötti merge

**Működés:**

```python
# 1. Initial state létrehozása
initial_state: AgentState = {
    "user_input": "What is AI?",
    "scenario": None,
    "classification": None,
    "retrieved_docs": [],
    # ... további mezők None-nal ...
    "nodes_executed": [],
    "timings": {},
    "cache_hits": {}
}

# 2. Graph futtatás
final_state = await graph.ainvoke(initial_state)

# 3. Minden node frissíti a state-t (merge)
# Triage node:
state = {**state, "classification": "complex", "nodes_executed": ["triage"]}

# Retrieval node:
state = {**state, "retrieved_docs": [...], "nodes_executed": ["triage", "retrieval"]}

# ... stb
```

**State merge stratégia:**

```python
# app/graph/agent_graph.py - LangGraph automatikusan merge-eli

def triage_node(state: AgentState) -> Dict:
    # Return csak az új/módosított mezőket
    return {
        "classification": "complex"  # ← Ez merge-elődik
    }

def retrieval_node(state: AgentState) -> Dict:
    # state["classification"] már elérhető (triage-ből)
    classification = state["classification"]
    
    # Return új mezőket
    return {
        "retrieved_docs": ["doc1", "doc2"]  # ← Ez is merge-elődik
    }
```

**Előnyök:**
- ✅ Immutábilis pattern (funkcionális programozás)
- ✅ Minden node látja az előző eredményeket
- ✅ Típusbiztos (TypedDict)
- ✅ Könnyű debugolás (látható a state minden lépésnél)

### 3.2 Dependency Injection Pattern

**Módszer:** Cache és cost tracker injektálása a node-okba

**Példa - `app/graph/agent_graph.py`:**

```python
class AgentGraphFactory:
    """
    Agent graph factory with dependency injection.
    
    Ez a "composition root" - itt kötjük össze a dependency-ket.
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        model_selector: ModelSelector,
        cost_tracker: CostTracker,
        node_cache: Cache,           # ← Cache dependency
        embedding_cache: Cache        # ← Cache dependency
    ):
        self.llm_client = llm_client
        self.model_selector = model_selector
        self.cost_tracker = cost_tracker
        self.node_cache = node_cache
        self.embedding_cache = embedding_cache
    
    def create_graph(self):
        """Create graph with injected dependencies."""
        
        # Node-ok létrehozása dependency injection-nel
        triage_node = TriageNode(
            llm_client=self.llm_client,
            cost_tracker=self.cost_tracker,
            model_selector=self.model_selector,
            cache=self.node_cache  # ← Cache injektálás
        )
        
        retrieval_node = RetrievalNode(
            llm_client=self.llm_client,
            cost_tracker=self.cost_tracker,
            model_selector=self.model_selector,
            embedding_cache=self.embedding_cache  # ← Cache injektálás
        )
        
        # Graph építés
        workflow = StateGraph(AgentState)
        workflow.add_node("triage", triage_node.execute)
        workflow.add_node("retrieval", retrieval_node.execute)
        # ...
        
        return workflow.compile()
```

**Előnyök:**
- ✅ Könnyű mock-olás teszteléshez
- ✅ Cache implementáció cserélhető (Memory → Redis)
- ✅ Tiszta dependency láncok
- ✅ SOLID elvek betartása

### 3.3 Cache Key Generation

**Módszer:** Determinisztikus cache kulcs generálás hash alapján

**Példa - `app/cache/keys.py`:**

```python
"""
Cache key generation utilities.
"""
import hashlib
import json
from typing import Any


def generate_cache_key(node_name: str, *args: Any) -> str:
    """
    Generate deterministic cache key.
    
    Args:
        node_name: Node azonosító
        *args: Argumentumok (pl. user_input)
        
    Returns:
        Cache key string (pl. "triage:abc123def456")
    """
    # Serialize argumentumok
    serialized = json.dumps(args, sort_keys=True)
    
    # SHA256 hash
    hash_digest = hashlib.sha256(serialized.encode()).hexdigest()
    
    # Key formátum: "node_name:hash"
    return f"{node_name}:{hash_digest[:16]}"


# Használat
cache_key = generate_cache_key("triage", "What is AI?")
# Eredmény: "triage:7f3a9b2c1e5d8f0a"

# Ugyanaz az input -> ugyanaz a kulcs
cache_key2 = generate_cache_key("triage", "What is AI?")
assert cache_key == cache_key2  # True!

# Más input -> más kulcs
cache_key3 = generate_cache_key("triage", "What is ML?")
assert cache_key != cache_key3  # True!
```

---

## 4. Tárolási Megoldások

### 4.1 Memory-based Storage (Jelenlegi Implementáció)

**Technológia:** Python dictionary (`Dict[str, CacheEntry]`)

**Használat:**
- Development környezet
- Single-instance deployment
- Rövid TTL cache (1 óra)

**Konfiguráció - `app/config.py`:**

```python
class Settings(BaseSettings):
    # Cache konfiguráció
    cache_ttl_seconds: int = 3600    # 1 óra
    cache_max_size: int = 1000       # Max 1000 bejegyzés
```

**Inicializálás - `app/main.py`:**

```python
from app.cache.memory_cache import MemoryCache

# Global cache instances
node_cache: Optional[MemoryCache] = None
embedding_cache: Optional[MemoryCache] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global node_cache, embedding_cache
    
    # Cache inicializálás startup-kor
    node_cache = MemoryCache(
        default_ttl_seconds=settings.cache_ttl_seconds,  # 3600s
        max_size=settings.cache_max_size                  # 1000
    )
    
    embedding_cache = MemoryCache(
        default_ttl_seconds=settings.cache_ttl_seconds,
        max_size=settings.cache_max_size
    )
    
    logger.info("Caches initialized (TTL=3600s, max_size=1000)")
    
    yield
    
    # Cleanup shutdown-kor
    await node_cache.clear()
    await embedding_cache.clear()
```

**Előnyök:**
- ✅ Egyszerű implementáció
- ✅ Nincs külső dependency
- ✅ Gyors (lokális memória)

**Hátrányok:**
- ❌ Nem perzisztens (restart = adatvesztés)
- ❌ Nem osztott (multi-instance esetén)
- ❌ Memória korlát

### 4.2 Redis-based Storage (Production Alternatíva)

**Technológia:** Redis in-memory database

**Mikor használjuk:**
- Multi-instance deployment
- Shared cache több pod között
- Hosszabb TTL (órák/napok)

**Implementáció példa - `app/cache/redis_cache.py`:**

```python
"""
Redis cache implementation (NEM IMPLEMENTÁLT - csak példa).
"""
import json
from typing import Optional, Any
from redis.asyncio import Redis
from app.cache.interfaces import Cache


class RedisCache(Cache):
    """
    Redis-based cache with TTL support.
    
    ÁLLAPOT TÍPUS: Cached data
    STORAGE: Redis (external service)
    PERSISTENCE: Redis RDB/AOF
    SCOPE: Shared across all instances
    """
    
    def __init__(self, redis_url: str, default_ttl_seconds: int = 3600):
        """
        Args:
            redis_url: Redis connection URL
            default_ttl_seconds: Default TTL
        """
        self.redis = Redis.from_url(redis_url)
        self.default_ttl = default_ttl_seconds
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from Redis."""
        value = await self.redis.get(key)
        if value is None:
            return None
        return json.loads(value)
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Set in Redis with TTL."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        serialized = json.dumps(value)
        await self.redis.setex(key, ttl, serialized)
    
    async def delete(self, key: str):
        """Delete from Redis."""
        await self.redis.delete(key)
    
    async def clear(self):
        """Clear all keys (DANGEROUS!)."""
        await self.redis.flushdb()
```

**Docker Compose kiegészítés (ha használnánk):**

```yaml
# docker-compose.yml - Redis hozzáadása

services:
  # ... meglévő services ...
  
  redis:
    image: redis:7-alpine
    container_name: redis-cache
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    networks:
      - monitoring

volumes:
  # ... meglévő volumes ...
  redis-data:
```

**AWS ElastiCache (Production):**

```terraform
# terraform/elasticache.tf - NEM IMPLEMENTÁLT (példa)

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.project_name}-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.redis.id]
  
  tags = {
    Name = "${var.project_name}-redis-cache"
  }
}
```

### 4.3 Database-based Storage (Conversation History)

**Technológia:** PostgreSQL vagy DynamoDB

**Mikor használjuk:**
- Multi-turn conversations
- User session tracking
- Long-term conversation history

**Példa séma (PostgreSQL):**

```sql
-- NEM IMPLEMENTÁLT - csak példa

CREATE TABLE conversation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    thread_id VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES conversation_sessions(id),
    role VARCHAR(50) NOT NULL,  -- 'user' | 'assistant'
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE agent_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id VARCHAR(255) NOT NULL,
    checkpoint_id VARCHAR(255) NOT NULL,
    state JSONB NOT NULL,  -- Teljes AgentState
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(thread_id, checkpoint_id)
);
```

---

## 5. Production Környezet - AWS

### 5.1 Jelenlegi Production Állapot Tárolás

**AWS ECS Fargate - Stateless Containers**

```
┌─────────────────────────────────────────────────┐
│           Application Load Balancer             │
│              (ALB - ELB v2)                     │
└────────────┬────────────────────────────────────┘
             │
             │ HTTP/HTTPS
             │
   ┌─────────▼─────────┐
   │   ECS Service     │
   │   (Fargate)       │
   └─────────┬─────────┘
             │
      ┌──────┴──────┐
      │             │
  ┌───▼──┐      ┌───▼──┐
  │Task 1│      │Task 2│  ← Horizontal scaling (0-N tasks)
  └───┬──┘      └───┬──┘
      │             │
      │  MEMORY     │  MEMORY
      │  ┌──────┐   │  ┌──────┐
      │  │State │   │  │State │  ← Workflow state (per request)
      │  │Cache │   │  │Cache │  ← MemoryCache (TTL=1h)
      │  └──────┘   │  └──────┘
      │             │
      └──────┬──────┘
             │
       Data elvész
       restart után!
```

**Állapot tárolás helye:**

| Állapot Típus | Tárolási Hely | Persistence | Shared |
|---------------|---------------|-------------|--------|
| **Workflow State** | ECS Task memória | Nincs (request scope) | Nem |
| **Cache** | ECS Task memória | Nincs (restart = elvész) | Nem (task-onként külön) |
| **Cost Tracker** | ECS Task memória | Nincs | Nem |
| **Logs** | CloudWatch Logs | Igen (7 nap retention) | Igen |
| **Metrics** | Prometheus → CloudWatch | Igen | Igen |

**Konfigurációs példa - `terraform/ecs.tf`:**

```terraform
resource "aws_ecs_task_definition" "app" {
  family                   = "${var.project_name}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"     # 0.5 vCPU
  memory                   = "1024"    # 1 GB RAM
  
  # ← ÁLLAPOT TÁROLÁS ITT (container memória)
  
  container_definitions = jsonencode([
    {
      name  = "app"
      image = "${aws_ecr_repository.app.repository_url}:latest"
      
      # Memória limit - ha túllépi, OOMKilled
      memory = 512  # MB
      
      environment = [
        {
          name  = "CACHE_TTL_SECONDS"
          value = "3600"  # Cache TTL
        },
        {
          name  = "CACHE_MAX_SIZE"
          value = "1000"  # Max cache entries
        }
      ]
      
      # Logs CloudWatch-ba (perzisztens)
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/ai-agent/app"
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "app"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "main" {
  name            = "${var.project_name}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 2  # ← 2 TASK = 2 külön memória space!
  launch_type     = "FARGATE"
  
  # Load balancer distribution
  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "app"
    container_port   = 8000
  }
}
```

**Következmények:**

1. **Nincs shared cache**: Task 1 és Task 2 külön cache-t használ
   - Ugyanaz a kérdés Task 1-en: cache HIT
   - Ugyanaz a kérdés Task 2-en: cache MISS (újra LLM hívás)

2. **Restart = data loss**: Task restart/redeploy törli a cache-t

3. **Horizontal scaling problémák**: Több task = többszörös cache redundancia

### 5.2 Production-ready Alternatíva: Redis Cache

**Architektúra Redis-szel:**

```
┌─────────────────────────────────────────────────┐
│           Application Load Balancer             │
└────────────┬────────────────────────────────────┘
             │
   ┌─────────▼─────────┐
   │   ECS Service     │
   └─────────┬─────────┘
             │
      ┌──────┴──────┐
      │             │
  ┌───▼──┐      ┌───▼──┐
  │Task 1│      │Task 2│
  └───┬──┘      └───┬──┘
      │             │
      └──────┬──────┘
             │
             │ TCP 6379
             │
   ┌─────────▼─────────────┐
   │   ElastiCache Redis   │  ← SHARED CACHE
   │   (Managed Service)   │
   └───────────────────────┘
         │
         │ Persistence
         │
   ┌─────▼─────┐
   │  RDB/AOF  │  ← Redis snapshots
   └───────────┘
```

**Terraform konfiguráció (példa):**

```terraform
# terraform/elasticache.tf

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.project_name}-redis"
  engine               = "redis"
  engine_version       = "7.0"
  node_type            = "cache.t3.micro"  # 0.5 GB RAM
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  
  subnet_group_name  = aws_elasticache_subnet_group.redis.name
  security_group_ids = [aws_security_group.redis.id]
  
  # Snapshot configuration
  snapshot_retention_limit = 5
  snapshot_window         = "03:00-05:00"
  
  tags = {
    Name = "${var.project_name}-shared-cache"
  }
}

# Security Group - csak ECS tasks férhetnek hozzá
resource "aws_security_group" "redis" {
  name   = "${var.project_name}-redis-sg"
  vpc_id = aws_vpc.main.id
  
  ingress {
    description     = "Redis from ECS"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Environment variable injection
resource "aws_ecs_task_definition" "app" {
  # ...
  
  container_definitions = jsonencode([
    {
      name  = "app"
      # ...
      
      environment = [
        {
          name  = "REDIS_URL"
          value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379"
        },
        {
          name  = "CACHE_BACKEND"
          value = "redis"  # "memory" vagy "redis"
        }
      ]
    }
  ])
}
```

**App konfiguráció update - `app/config.py`:**

```python
class Settings(BaseSettings):
    # ... meglévő beállítások ...
    
    # Cache backend választás
    cache_backend: str = "memory"  # "memory" vagy "redis"
    redis_url: Optional[str] = None
    
    # Cache konfiguráció
    cache_ttl_seconds: int = 3600
    cache_max_size: int = 1000
```

**Cache factory - `app/cache/factory.py`:**

```python
"""
Cache factory for creating appropriate cache backend.
"""
from app.cache.interfaces import Cache
from app.cache.memory_cache import MemoryCache
from app.cache.redis_cache import RedisCache
from app.config import settings


def create_cache() -> Cache:
    """
    Create cache instance based on configuration.
    
    Returns:
        Cache implementation (Memory or Redis)
    """
    if settings.cache_backend == "redis":
        if not settings.redis_url:
            raise ValueError("REDIS_URL required for redis backend")
        
        return RedisCache(
            redis_url=settings.redis_url,
            default_ttl_seconds=settings.cache_ttl_seconds
        )
    else:
        # Default: memory cache
        return MemoryCache(
            default_ttl_seconds=settings.cache_ttl_seconds,
            max_size=settings.cache_max_size
        )
```

### 5.3 DynamoDB State Storage (Conversation Persistence)

**Mikor használjuk:** Multi-turn conversations, session history

**Schema design:**

```terraform
# terraform/dynamodb.tf - NEM IMPLEMENTÁLT (példa)

resource "aws_dynamodb_table" "conversation_sessions" {
  name           = "${var.project_name}-sessions"
  billing_mode   = "PAY_PER_REQUEST"  # On-demand pricing
  hash_key       = "thread_id"
  
  attribute {
    name = "thread_id"
    type = "S"  # String
  }
  
  attribute {
    name = "user_id"
    type = "S"
  }
  
  # GSI for user queries
  global_secondary_index {
    name            = "UserIdIndex"
    hash_key        = "user_id"
    projection_type = "ALL"
  }
  
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
  
  tags = {
    Name = "${var.project_name}-conversation-sessions"
  }
}

resource "aws_dynamodb_table" "agent_checkpoints" {
  name         = "${var.project_name}-checkpoints"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "thread_id"
  range_key    = "checkpoint_id"
  
  attribute {
    name = "thread_id"
    type = "S"
  }
  
  attribute {
    name = "checkpoint_id"
    type = "S"
  }
  
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
}
```

**LangGraph DynamoDB Checkpointer (elméleti):**

```python
# NEM IMPLEMENTÁLT - csak példa

from langgraph.checkpoint.dynamodb import DynamoDBSaver

# DynamoDB checkpointer létrehozása
checkpointer = DynamoDBSaver(
    table_name="ai-agent-checkpoints",
    region_name="us-east-1"
)

# Graph compile checkpointer-rel
app = workflow.compile(checkpointer=checkpointer)

# Thread-based conversation
config = {"configurable": {"thread_id": "user_123"}}

# Első üzenet
result1 = await app.ainvoke(
    {"user_input": "What is AI?"},
    config=config
)
# State automatikusan DynamoDB-be mentve!

# Második üzenet - előző context betöltve
result2 = await app.ainvoke(
    {"user_input": "Explain more about neural networks"},
    config=config  # Ugyanaz a thread_id
)
# Az agent "emlékszik" az előző beszélgetésre!
```

---

## 6. Kód Példák és Konfiguráció

### 6.1 Teljes State Lifecycle

**API Request → State Creation → Node Execution → Response**

```python
# app/main.py - teljes flow

@app.post("/run", response_model=RunResponse)
async def run_agent(request: RunRequest):
    """
    Run agent workflow.
    
    ÁLLAPOT LIFECYCLE:
    1. Initial state creation (üres mezőkkel)
    2. Graph execution (node-ok frissítik)
    3. Final state visszaadása
    4. State megsemmisül (GC)
    """
    
    # === 1. INITIAL STATE CREATION ===
    initial_state: AgentState = {
        # Input
        "user_input": request.user_input,
        "scenario": request.scenario,
        
        # Empty outputs (None)
        "classification": None,
        "retrieved_docs": [],
        "retrieval_context": None,
        "reasoning_output": None,
        "final_answer": None,
        
        # Empty metadata
        "nodes_executed": [],
        "models_used": [],
        "timings": {},
        "cache_hits": {}
    }
    
    # === 2. GRAPH EXECUTION ===
    # Új cost tracker minden kéréshez (stateless!)
    cost_tracker = CostTracker(model_selector)
    
    # Graph létrehozás injected dependencies-szel
    graph = create_agent_graph(
        llm_client=llm_client,
        model_selector=model_selector,
        cost_tracker=cost_tracker,
        node_cache=node_cache,        # ← Shared cache (app-wide)
        embedding_cache=embedding_cache
    )
    
    # Graph futtatás (state node-ok között halad)
    start_time = time.time()
    final_state = await graph.ainvoke(initial_state)
    execution_time = time.time() - start_time
    
    # === 3. COST REPORT ===
    cost_report = cost_tracker.get_report()
    
    # === 4. RESPONSE BUILDING ===
    response = RunResponse(
        answer=final_state.get("final_answer", "No answer"),
        debug={
            "nodes_executed": final_state.get("nodes_executed", []),
            "models_used": final_state.get("models_used", []),
            "timings": final_state.get("timings", {}),
            "cache_hits": final_state.get("cache_hits", {}),
            "cost_report": {
                "total_cost_usd": cost_report.total_cost_usd,
                "total_input_tokens": cost_report.total_input_tokens,
                "total_output_tokens": cost_report.total_output_tokens,
                "by_node": {
                    name: {
                        "cost_usd": node.cost_usd,
                        "tokens": node.input_tokens + node.output_tokens
                    }
                    for name, node in cost_report.by_node.items()
                }
            }
        }
    )
    
    # === 5. STATE CLEANUP ===
    # final_state GC által megsemmisítve (Python)
    # cost_tracker GC által megsemmisítve
    
    return response
```

### 6.2 Node State Management Példa

```python
# app/nodes/reasoning_node.py - részlet

class ReasoningNode:
    """Reasoning node with state management."""
    
    async def execute(self, state: AgentState) -> Dict:
        """
        Execute reasoning node.
        
        STATE OLVASÁS:
        - user_input (triage-től)
        - classification (triage-től)
        - retrieval_context (retrieval-től)
        
        STATE ÍRÁS:
        - reasoning_output
        - nodes_executed frissítés
        - models_used frissítés
        - timings frissítés
        """
        start_time = time.time()
        
        # ===== STATE OLVASÁS =====
        user_input = state["user_input"]
        classification = state.get("classification", "unknown")
        retrieval_context = state.get("retrieval_context", "")
        
        # ===== LLM HÍVÁS =====
        prompt = f"""
        User Question: {user_input}
        Query Type: {classification}
        Context: {retrieval_context}
        
        Provide a detailed answer.
        """
        
        model = self.model_selector.get_model_name(ModelTier.EXPENSIVE)
        response = await self.llm_client.complete(prompt, model)
        
        # ===== COST TRACKING =====
        self.cost_tracker.track_usage(
            node_name="reasoning",
            model=model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens
        )
        
        execution_time = time.time() - start_time
        
        # ===== STATE FRISSÍTÉS (MERGE) =====
        return {
            # Új output
            "reasoning_output": response.content,
            
            # Metadata frissítés (append)
            "nodes_executed": state.get("nodes_executed", []) + ["reasoning"],
            "models_used": state.get("models_used", []) + [model],
            
            # Timing update (merge)
            "timings": {
                **state.get("timings", {}),
                "reasoning": execution_time
            },
            
            # Cache info (no cache for reasoning)
            "cache_hits": {
                **state.get("cache_hits", {}),
                "reasoning": False
            }
        }
```

---

## 7. Best Practices

### 7.1 Stateless Design

✅ **DO:** Minden kérés független
```python
# Minden kéréshez új cost tracker
cost_tracker = CostTracker(model_selector)
```

❌ **DON'T:** Global state megosztása kérések között
```python
# ROSSZ - race condition!
global_cost_tracker = CostTracker(...)  # NE!
```

### 7.2 Cache Stratégia

✅ **DO:** Determinisztikus cache kulcsok
```python
cache_key = generate_cache_key("triage", user_input)
# Ugyanaz az input -> ugyanaz a kulcs
```

✅ **DO:** Megfelelő TTL beállítás
```python
# Gyors változó adatok: rövid TTL
cache.set(key, value, ttl_seconds=300)  # 5 perc

# Stabil adatok: hosszú TTL
cache.set(key, value, ttl_seconds=3600)  # 1 óra
```

❌ **DON'T:** Túl nagy cache entries
```python
# ROSSZ - memória probléma!
await cache.set(key, huge_object)  # MB-os objektum
```

### 7.3 Error Handling

✅ **DO:** Graceful degradation cache failure esetén
```python
try:
    cached = await cache.get(key)
except Exception as e:
    logger.warning(f"Cache error: {e}")
    cached = None  # Continue without cache
```

### 7.4 Monitoring

✅ **DO:** State metadata tracking
```python
return {
    "nodes_executed": [...],
    "timings": {...},
    "cache_hits": {...}
}
```

✅ **DO:** Prometheus metrics
```python
metrics.cache_hit_total.labels(cache="node", node="triage").inc()
```

---

## Összefoglalás

| Kérdés | Válasz |
|--------|--------|
| **Hol van az állapot tárolva lokálisan?** | Python memória (Dict objektumok) |
| **Hol van az állapot tárolva AWS-ben?** | ECS Task memória (nem perzisztens) |
| **Milyen állapot típusok vannak?** | 1) Workflow state (request scope)<br>2) Cache state (TTL-based)<br>3) Persistent state (NEM használt) |
| **Hogyan osztott az állapot?** | Cache: app-wide (de task-onként külön)<br>Workflow: request-specific |
| **Mi történik restart esetén?** | Workflow state: elvész (OK, stateless)<br>Cache: elvész (újra kell építeni) |
| **Shared cache production-ben?** | Redis/ElastiCache szükséges |
| **Conversation history támogatás?** | NEM - minden kérés független |

**Kulcs Tanulság:**
- Jelenlegi rendszer: **Stateless, memory-based, request-scoped**
- Production upgrade: **Redis cache megosztáshoz**
- Multi-turn: **DynamoDB + LangGraph checkpointer**

---

## 8. AI Agent Deploy Checklist - Implementáció Ellenőrzés

### Mi különbözteti meg az AI Agent Deploy-t egy hagyományos backendtől?

**AI Agent = Szoftver + Döntési Logika + Költség**

Az alábbi checklist minden speciális kihívást tartalmaz, és pontosan leírja, hogy **mi biztosítja** a megoldást ebben az alkalmazásban.

---

### ✅ 1. LLM API Kulcsok Kezelése

**Követelmény:** Biztonságos API kulcs tárolás különböző környezetekben (dev, staging, prod).

#### 🔧 Implementáció ebben az app-ban:

| Környezet | Megoldás | Fájl/Konfiguráció |
|-----------|----------|-------------------|
| **Development** | `.env` fájl (gitignore-olva) | `.env` |
| **Konfiguráció betöltés** | Pydantic Settings | `app/config.py` |
| **Docker** | `env_file` docker-compose-ban | `docker-compose.yml` |
| **Production (AWS)** | Environment variables ECS Task Definition-ben | `terraform/ecs.tf` |
| **Alternatíva (Best Practice)** | AWS Secrets Manager | `terraform/ecs.tf` (kommentben példa) |

#### 📝 Konkrét Kód:

**`app/config.py` - Pydantic Settings:**
```python
class Settings(BaseSettings):
    openai_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

**`docker-compose.yml` - Docker környezet:**
```yaml
services:
  agent-demo:
    env_file:
      - .env  # API kulcsok itt
```

**`terraform/ecs.tf` - Production (AWS ECS):**
```terraform
container_definitions = jsonencode([
  {
    environment = [
      {
        name  = "OPENAI_API_KEY"
        value = var.openai_api_key  # GitHub Secrets → Terraform
      }
    ]
  }
])
```

**Alternatíva - AWS Secrets Manager:**
```terraform
secrets = [
  {
    name      = "OPENAI_API_KEY"
    valueFrom = aws_secretsmanager_secret.openai_key.arn
  }
]
```

**✅ Ellenőrzés:** 
- [ ] `.env` fájl létezik és `.gitignore`-ban van
- [ ] `app/config.py` tartalmazza az `openai_api_key` mezőt
- [ ] Docker Compose használja `env_file`-t
- [ ] Terraform ECS task definition tartalmazza az environment változót

---

### ✅ 2. Nem Determinisztikus Futás

**Követelmény:** LLM nem determinisztikus → ugyanaz a prompt különböző válaszokat adhat. Szükséges: mock client teszteléshez, cache konzisztenciához, részletes logging.

#### 🔧 Implementáció ebben az app-ban:

| Megoldás | Célja | Fájl |
|----------|-------|------|
| **Mock LLM Client** | Determinisztikus válaszok teszteléshez | `app/llm/mock_client.py` |
| **MemoryCache** | Ugyanaz az input → ugyanaz a válasz (TTL-en belül) | `app/cache/memory_cache.py` |
| **Cache kulcs generálás** | Hash-alapú kulcsok | `app/cache/keys.py` |
| **Structured logging** | Minden LLM hívás naplózva | `app/logging_conf.py` |
| **Metrics** | Prometheus observability | `app/observability/metrics.py` |

#### 📝 Konkrét Kód:

**`app/llm/mock_client.py` - Determinisztikus mock:**
```python
class MockLLMClient(LLMClient):
    async def complete(self, prompt: str, model: str) -> LLMResponse:
        # Determinisztikus válaszok keyword alapján
        if "classify" in prompt.lower():
            content = "simple"
        elif "retrieve" in prompt.lower():
            content = "Retrieved documents: [Mock Doc 1, Mock Doc 2]"
        # ...
        return LLMResponse(content=content, ...)
```

**`app/cache/memory_cache.py` - Cache konzisztencia:**
```python
class MemoryCache:
    async def get(self, key: str) -> Optional[Any]:
        # Ugyanaz a kulcs → ugyanaz az érték (TTL-en belül)
        entry = self._store.get(key)
        if entry and time.time() <= entry.expires_at:
            return entry.value
        return None
```

**`app/cache/keys.py` - Determinisztikus cache kulcs:**
```python
def generate_cache_key(node_name: str, *args: Any) -> str:
    serialized = json.dumps(args, sort_keys=True)
    hash_digest = hashlib.sha256(serialized.encode()).hexdigest()
    return f"{node_name}:{hash_digest[:16]}"
```

**`app/main.py` - Mock vs OpenAI választás:**
```python
if settings.openai_api_key:
    llm_client = OpenAIClient(api_key=settings.openai_api_key)
else:
    llm_client = MockLLMClient(latency_ms=100)
```

**✅ Ellenőrzés:**
- [ ] `MockLLMClient` létezik és determinisztikus válaszokat ad
- [ ] `MemoryCache` implementálja a `Cache` interface-t
- [ ] `generate_cache_key` hash-alapú
- [ ] Node-ok használják a cache-t (pl. `triage_node.py`)
- [ ] Logging beállítva (`app/logging_conf.py`)

---

### ✅ 3. Külső Toolok és API-k

**Követelmény:** LLM client, cache, embedding service dependency-k kezelése. Interface-alapú architektúra a cserélhetőséghez.

#### 🔧 Implementáció ebben az app-ban:

| Pattern | Célja | Fájl |
|---------|-------|------|
| **Interface Pattern (ABC)** | Függőségek absztrakciója | `app/llm/interfaces.py`, `app/cache/interfaces.py` |
| **Dependency Injection** | Node-ok kapják a dependency-ket | `app/graph/agent_graph.py` |
| **Factory Pattern** | Graph létrehozás DI-vel | `app/graph/agent_graph.py` (AgentGraphFactory) |

#### 📝 Konkrét Kód:

**`app/llm/interfaces.py` - LLM Interface:**
```python
from abc import ABC, abstractmethod

class LLMClient(ABC):
    @abstractmethod
    async def complete(self, prompt: str, model: str) -> LLMResponse:
        pass
```

**`app/cache/interfaces.py` - Cache Interface:**
```python
class Cache(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        pass
```

**`app/graph/agent_graph.py` - Dependency Injection:**
```python
class AgentGraphFactory:
    def __init__(
        self,
        llm_client: LLMClient,      # Interface
        model_selector: ModelSelector,
        cost_tracker: CostTracker,
        node_cache: Cache,          # Interface
        embedding_cache: Cache
    ):
        # Dependency-k tárolása
        
    def create_graph(self):
        # Node-ok létrehozása injected dependency-kkel
        triage_node = TriageNode(
            llm_client=self.llm_client,
            cache=self.node_cache,
            # ...
        )
```

**`app/main.py` - Composition Root:**
```python
# Dependency-k létrehozása
llm_client = OpenAIClient(...) or MockLLMClient(...)
node_cache = MemoryCache(...)
model_selector = ModelSelector()
cost_tracker = CostTracker(model_selector)

# Graph factory
graph = create_agent_graph(
    llm_client=llm_client,
    node_cache=node_cache,
    # ...
)
```

**✅ Ellenőrzés:**
- [ ] `LLMClient` ABC létezik interface-ként
- [ ] `Cache` ABC létezik interface-ként
- [ ] `AgentGraphFactory` használ dependency injection-t
- [ ] Node-ok constructor-ban kapják a dependency-ket
- [ ] `main.py` a "composition root" (összeköti a dependency-ket)

---

### ✅ 4. Állapot (State, Memory)

**Követelmény:** Többlépcsős workflow állapotkezelése, node-ok közötti adatátadás, metadata tracking.

#### 🔧 Implementáció ebben az app-ban:

| Komponens | Célja | Fájl |
|-----------|-------|------|
| **TypedDict State** | Típusbiztos állapot definíció | `app/graph/state.py` |
| **LangGraph StateGraph** | State management workflow-ban | `app/graph/agent_graph.py` |
| **State merge** | Node-ok frissítik a state-t | Minden node (`app/nodes/*.py`) |
| **Metadata tracking** | Futási adatok (timing, cost, cache) | `app/graph/state.py` (AgentState) |
| **MemoryCache** | Node-level caching | `app/cache/memory_cache.py` |

#### 📝 Konkrét Kód:

**`app/graph/state.py` - State definíció:**
```python
class AgentState(TypedDict, total=False):
    # Input
    user_input: str
    scenario: Optional[str]
    
    # Node outputs
    classification: Optional[str]
    retrieved_docs: List[str]
    retrieval_context: Optional[str]
    reasoning_output: Optional[str]
    final_answer: Optional[str]
    
    # Metadata
    nodes_executed: List[str]
    models_used: List[str]
    timings: Dict[str, float]
    cache_hits: Dict[str, bool]
```

**`app/graph/agent_graph.py` - StateGraph használat:**
```python
workflow = StateGraph(AgentState)
workflow.add_node("triage", triage_node.execute)
workflow.add_node("retrieval", retrieval_node.execute)
# ...
app = workflow.compile()
```

**`app/nodes/triage_node.py` - State frissítés:**
```python
async def execute(self, state: AgentState) -> Dict:
    user_input = state["user_input"]  # Olvasás
    # ... LLM hívás ...
    
    return {
        "classification": classification,  # Új mező
        "nodes_executed": state.get("nodes_executed", []) + ["triage"],
        "timings": {**state.get("timings", {}), "triage": exec_time}
    }
```

**`app/main.py` - Initial state creation:**
```python
initial_state: AgentState = {
    "user_input": request.user_input,
    "scenario": request.scenario,
    "classification": None,
    "nodes_executed": [],
    "timings": {},
    # ...
}

final_state = await graph.ainvoke(initial_state)
```

**Tárolás típusok:**

| Állapot Típus | Tárolás Helye | Persistence | Scope |
|---------------|---------------|-------------|-------|
| **Workflow State** | Python memória | Request scope | Egy kérés |
| **Cache State** | `MemoryCache._store` Dict | TTL (1h) | App-wide |
| **Logs** | CloudWatch Logs (AWS) | 7 nap | Global |
| **Metrics** | Prometheus → Grafana | Időbélyeg szerint | Global |

**AWS Production - `terraform/ecs.tf`:**
```terraform
resource "aws_ecs_task_definition" "app" {
  cpu    = "512"   # 0.5 vCPU
  memory = "1024"  # 1 GB RAM ← ÁLLAPOT ITT (container memória)
}
```

**✅ Ellenőrzés:**
- [ ] `AgentState` TypedDict létezik
- [ ] `StateGraph` használja az `AgentState`-t
- [ ] Node-ok return Dict-tel frissítik a state-t
- [ ] Initial state létrehozás `main.py`-ban
- [ ] Metadata tracking (nodes_executed, timings, cache_hits)
- [ ] ECS task definíció tartalmaz memória limitet

---

### ✅ 5. Költség / Token Usage

**Követelmény:** LLM hívások token-alapú költségeinek nyomon követése, node-onkénti és model-enkénti breakdown, Prometheus metrics.

#### 🔧 Implementáció ebben az app-ban:

| Komponens | Célja | Fájl |
|-----------|-------|------|
| **CostTracker** | Token és USD tracking | `app/llm/cost_tracker.py` |
| **ModelSelector** | Model pricing lookup | `app/llm/models.py` |
| **Prometheus Metrics** | Token és cost counter-ek | `app/observability/metrics.py` |
| **Grafana Dashboard** | Cost vizualizáció | `grafana/dashboards/agent-dashboard.json` |
| **API Response** | Cost report minden kérésben | `app/main.py` (RunResponse) |

#### 📝 Konkrét Kód:

**`app/llm/cost_tracker.py` - Cost tracking:**
```python
class CostTracker:
    def track_usage(
        self,
        node_name: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ):
        # Pricing lekérése
        input_price, output_price = self.model_selector.get_pricing(model)
        
        # Költség számítás (USD / 1K token)
        cost = (
            (input_tokens / 1000.0) * input_price +
            (output_tokens / 1000.0) * output_price
        )
        
        # Track by node és by model
        self._node_costs[node_name].cost_usd += cost
        self._model_costs[model].cost_usd += cost
```

**`app/llm/models.py` - Pricing konfiguráció:**
```python
class ModelSelector:
    def get_pricing(self, model: str) -> Tuple[float, float]:
        # Input és output pricing (USD / 1K token)
        pricing_map = {
            "gpt-3.5-turbo": (0.0001, 0.0002),
            "gpt-4-turbo-preview": (0.001, 0.002),
            "gpt-4": (0.01, 0.03)
        }
        return pricing_map.get(model, (0.0, 0.0))
```

**`app/config.py` - Pricing konfiguráció:**
```python
class Settings(BaseSettings):
    # Pricing (USD per 1K tokens)
    price_cheap_input: float = 0.0001
    price_cheap_output: float = 0.0002
    price_medium_input: float = 0.001
    price_medium_output: float = 0.002
    price_expensive_input: float = 0.01
    price_expensive_output: float = 0.03
```

**`app/observability/metrics.py` - Prometheus metrics:**
```python
llm_inference_token_input_total = Counter(
    'llm_inference_token_input_total',
    'Total input tokens consumed',
    ['model', 'node']
)

llm_inference_token_output_total = Counter(
    'llm_inference_token_output_total',
    'Total output tokens generated',
    ['model', 'node']
)

llm_cost_total_usd = Counter(
    'llm_cost_total_usd',
    'Total LLM cost in USD',
    ['model', 'node']
)
```

**Node-okban használat - pl. `app/nodes/reasoning_node.py`:**
```python
# LLM hívás után
self.cost_tracker.track_usage(
    node_name="reasoning",
    model=model,
    input_tokens=response.input_tokens,
    output_tokens=response.output_tokens
)

# Prometheus metrics
metrics.llm_cost_total_usd.labels(
    model=model,
    node="reasoning"
).inc(cost_usd)
```

**`app/main.py` - Cost report API válaszban:**
```python
cost_report = cost_tracker.get_report()

response = RunResponse(
    answer=final_state.get("final_answer"),
    debug={
        "cost_report": {
            "total_cost_usd": cost_report.total_cost_usd,
            "total_input_tokens": cost_report.total_input_tokens,
            "total_output_tokens": cost_report.total_output_tokens,
            "by_node": {...},
            "by_model": {...}
        }
    }
)
```

**✅ Ellenőrzés:**
- [ ] `CostTracker` implementálva
- [ ] `ModelSelector` tartalmazza a pricing map-et
- [ ] `app/config.py` tartalmazza a pricing konstansokat
- [ ] Prometheus metrics definiálva (`llm_cost_total_usd` stb.)
- [ ] Node-ok hívják a `cost_tracker.track_usage()`-t
- [ ] API válasz tartalmaz cost report-ot
- [ ] Grafana dashboard létezik (`grafana/dashboards/`)

---

### ✅ 6. Verziózás (Prompt ≠ Kód)

**Követelmény:** Prompt-ok verziókövetése, mivel az AI viselkedése nem csak a kódtól, hanem a prompt-októl is függ.

#### 🔧 Implementáció ebben az app-ban:

| Megoldás | Célja | Fájl/Mappa |
|----------|-------|------------|
| **Prompt fájlok** | Külön fájlokban tárolva | `prompts/*.txt` |
| **Git tracking** | Prompt változások követhetők | `.git/` (commit history) |
| **Template loading** | Runtime betöltés | Node-ok (pl. `app/nodes/triage_node.py`) |
| **Prompt hash tracking** | Verzió metadata | `app/graph/state.py` (prompt_versions) |

#### 📝 Konkrét Kód:

**Prompt fájlok struktúra:**
```
prompts/
├── triage_prompt.txt       ← Klasszifikációs prompt
├── retrieval_prompt.txt    ← Retrieval prompt
├── reasoning_prompt.txt    ← Reasoning prompt
└── summary_prompt.txt      ← Summary prompt
```

**`prompts/triage_prompt.txt` - példa:**
```text
Classify the query type. Output ONE word only.

Types:
- simple: factual, direct answer
- retrieval: requires looking up information
- complex: needs reasoning or analysis

Query: {user_input}

Classification:
```

**Node-okban prompt betöltés - pl. `app/nodes/triage_node.py`:**
```python
from pathlib import Path

PROMPT_DIR = Path(__file__).parent.parent.parent / "prompts"
TRIAGE_PROMPT_PATH = PROMPT_DIR / "triage_prompt.txt"

def _load_prompt(self) -> str:
    """Load prompt template from file."""
    with open(TRIAGE_PROMPT_PATH, 'r') as f:
        return f.read()

async def execute(self, state: AgentState) -> Dict:
    # Prompt betöltés
    prompt_template = self._load_prompt()
    
    # Változók behelyettesítése
    prompt = prompt_template.format(user_input=state["user_input"])
    
    # LLM hívás
    response = await self.llm_client.complete(prompt, model)
```

**Git commit history:**
```bash
git log --oneline prompts/reasoning_prompt.txt

# Output:
# a3f2e1d Update reasoning prompt to be more specific
# 7b8c9d2 Add context usage instruction
# 1e5f6a3 Initial reasoning prompt
```

**Prompt verzió tracking (opcionális - nem implementált, de példa):**
```python
import hashlib

def get_prompt_hash(prompt: str) -> str:
    """SHA256 hash for versioning."""
    return hashlib.sha256(prompt.encode()).hexdigest()[:8]

# Használat node-ban
prompt_hash = get_prompt_hash(prompt_template)

return {
    "reasoning_output": response.content,
    "prompt_versions": {
        **state.get("prompt_versions", {}),
        "reasoning": prompt_hash
    }
}
```

**✅ Ellenőrzés:**
- [ ] `prompts/` mappa létezik
- [ ] Minden node-hoz tartozik `.txt` prompt fájl
- [ ] Prompt-ok Git-ben követve vannak
- [ ] Node-ok betöltik a prompt-okat fájlból
- [ ] Prompt változások külön commit-ban vannak
- [ ] (Opcionális) Prompt hash tracking implementálva

---

### ✅ 7. Monitoring és Observability

**Követelmény:** Valós idejű monitoring, metrics, dashboardok az LLM költségek, latency, cache hatékonyság követésére.

#### 🔧 Implementáció ebben az app-ban:

| Komponens | Célja | Fájl/Service |
|-----------|-------|--------------|
| **Prometheus** | Metrics gyűjtés | `prometheus/prometheus.yml`, Docker service |
| **Grafana** | Dashboardok | `grafana/`, Docker service |
| **Metrics endpoint** | `/metrics` API | `app/main.py` |
| **Custom metrics** | LLM, cache, agent metrics | `app/observability/metrics.py` |
| **Middleware** | Request tracking | `app/observability/middleware.py` |
| **CloudWatch Logs** | Production logs (AWS) | `terraform/ecs.tf` |

#### 📝 Konkrét Kód:

**`prometheus/prometheus.yml` - Prometheus konfiguráció:**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'agent-demo'
    static_configs:
      - targets: ['agent-demo:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

**`docker-compose.yml` - Prometheus és Grafana:**
```yaml
services:
  prometheus:
    image: prom/prometheus:v2.48.0
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana:10.2.2
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
    ports:
      - "3000:3000"
```

**`app/observability/metrics.py` - Metrics definíciók:**
```python
from prometheus_client import Counter, Histogram

# LLM metrics
llm_inference_count_total = Counter(
    'llm_inference_count_total',
    'Total LLM calls',
    ['model', 'node', 'status']
)

llm_cost_total_usd = Counter(
    'llm_cost_total_usd',
    'Total cost in USD',
    ['model', 'node']
)

# Cache metrics
cache_hit_total = Counter(
    'cache_hit_total',
    'Cache hits',
    ['cache', 'node']
)

# Agent metrics
agent_execution_latency_seconds = Histogram(
    'agent_execution_latency_seconds',
    'Agent execution latency',
    ['graph'],
    buckets=[0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
)
```

**`app/main.py` - Metrics endpoint:**
```python
from prometheus_client import REGISTRY, generate_latest, CONTENT_TYPE_LATEST

@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )
```

**`app/observability/middleware.py` - Request tracking:**
```python
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        latency = time.time() - start_time
        
        # Track HTTP request metrics
        http_requests_total.labels(
            method=request.method,
            path=request.url.path,
            status=response.status_code
        ).inc()
        
        return response
```

**`app/logging_conf.py` - Structured logging:**
```python
import logging

def setup_logging() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger("agent-demo")
```

**AWS CloudWatch - `terraform/ecs.tf`:**
```terraform
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.project_name}/app"
  retention_in_days = 7
}

container_definitions = jsonencode([
  {
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"  = aws_cloudwatch_log_group.app.name
        "awslogs-region" = var.aws_region
      }
    }
  }
])
```

**Grafana Dashboard - `grafana/dashboards/agent-dashboard.json`:**
```json
{
  "title": "AI Agent Monitoring",
  "panels": [
    {
      "title": "Total Cost (USD)",
      "targets": [{
        "expr": "sum(llm_cost_total_usd)"
      }]
    },
    {
      "title": "Cache Hit Rate",
      "targets": [{
        "expr": "sum(cache_hit_total) / (sum(cache_hit_total) + sum(cache_miss_total))"
      }]
    }
  ]
}
```

**✅ Ellenőrzés:**
- [ ] `prometheus/prometheus.yml` létezik és konfigurálja a scrape-et
- [ ] `docker-compose.yml` tartalmazza Prometheus és Grafana service-eket
- [ ] `app/observability/metrics.py` definiálja a custom metrics-eket
- [ ] `/metrics` endpoint elérhető (`app/main.py`)
- [ ] Middleware tracking implementálva
- [ ] Structured logging beállítva
- [ ] Grafana dashboard JSON létezik
- [ ] (Production) CloudWatch log group létrehozva Terraform-mel

---

## 9. Teljes Implementáció Ellenőrző Táblázat

| # | Kihívás | Status | Fő Implementációs Fájlok |
|---|---------|--------|--------------------------|
| 1️⃣ | **LLM API kulcsok** | ✅ | `app/config.py`, `docker-compose.yml`, `terraform/ecs.tf` |
| 2️⃣ | **Nem determinisztikus futás** | ✅ | `app/llm/mock_client.py`, `app/cache/memory_cache.py`, `app/cache/keys.py` |
| 3️⃣ | **Külső toolok és API-k** | ✅ | `app/llm/interfaces.py`, `app/cache/interfaces.py`, `app/graph/agent_graph.py` |
| 4️⃣ | **Állapot (state, memory)** | ✅ | `app/graph/state.py`, `app/graph/agent_graph.py`, `app/nodes/*.py` |
| 5️⃣ | **Költség / token usage** | ✅ | `app/llm/cost_tracker.py`, `app/observability/metrics.py`, `app/config.py` |
| 6️⃣ | **Verziózás (prompt ≠ kód)** | ✅ | `prompts/*.txt`, Git commit history |
| 7️⃣ | **Monitoring és observability** | ✅ | `prometheus/`, `grafana/`, `app/observability/`, `terraform/ecs.tf` (CloudWatch) |

---

## 10. Production Deployment Checklist (AWS)

### Infrastructure (Terraform)

- [ ] **VPC és Networking**: `terraform/vpc.tf`
  - VPC létrehozva
  - Public subnet-ek
  - Internet Gateway
  - Route table-k

- [ ] **ECS Fargate**: `terraform/ecs.tf`
  - ECS cluster
  - Task definition (CPU, Memory)
  - ECS service (desired count)
  - Task role és execution role

- [ ] **Application Load Balancer**: `terraform/alb.tf`
  - ALB létrehozva
  - Target group
  - Listener (HTTP/HTTPS)
  - Health check konfiguráció

- [ ] **ECR Repository**: `terraform/ecr.tf`
  - Docker image repository
  - Lifecycle policy

- [ ] **CloudWatch Logs**: `terraform/ecs.tf`
  - Log groups létrehozva
  - Retention policy (7 nap)

- [ ] **Environment Variables**: `terraform/ecs.tf`
  - OPENAI_API_KEY injected
  - Cache konfiguráció
  - Log level

### Application

- [ ] **Docker Image Build**:
  ```bash
  docker build -t ai-agent-app -f docker/Dockerfile .
  ```

- [ ] **ECR Push**:
  ```bash
  aws ecr get-login-password | docker login --username AWS --password-stdin <ECR_URI>
  docker tag ai-agent-app:latest <ECR_URI>:latest
  docker push <ECR_URI>:latest
  ```

- [ ] **ECS Deployment**:
  ```bash
  terraform apply
  aws ecs update-service --cluster <cluster> --service <service> --force-new-deployment
  ```

### Monitoring

- [ ] **Prometheus**: ECS task-ban fut, scrape-eli az app `/metrics` endpoint-ját
- [ ] **Grafana**: ECS task-ban fut, dashboardok provisioned
- [ ] **CloudWatch Logs**: ECS stdout/stderr → CloudWatch
- [ ] **Alerts**: (Opcionális) CloudWatch Alarms cost threshold-ra

### Security

- [ ] **API Keys**: Environment variables vagy Secrets Manager
- [ ] **Security Groups**: 
  - ALB: 80/443 nyitva
  - ECS tasks: csak ALB-ből elérhető (8000 port)
- [ ] **IAM Roles**: Least privilege principle

---

## Konklúzió

Ez az alkalmazás **minden speciális AI agent kihívást kezel** strukturált, production-ready módon:

✅ **Biztonságos API kulcs kezelés** - környezet-függő konfiguráció  
✅ **Determinisztikus tesztelés** - mock client + cache  
✅ **Dependency injection** - cserélhető komponensek  
✅ **Stateful workflow** - LangGraph TypedDict state  
✅ **Költség tracking** - real-time token és USD monitoring  
✅ **Prompt verziózás** - Git-ben követve  
✅ **Production monitoring** - Prometheus + Grafana + CloudWatch  

**Minden fájl és konfiguráció pontosan dokumentálva.**

---

**Készítette:** AI Agent Team  
**Verzió:** 1.1 (Checklist hozzáadva)  
**Dátum:** 2026-01-22
