# Prometheus & Grafana Monitoring Útmutató

**Teljes Programozási Útmutató AI Agent Megfigyelhetőséghez**

Utolsó frissítés: 2026. január 15.

---

## 📋 Tartalomjegyzék

1. [Áttekintés](#áttekintés)
2. [Architektúra és Adatfolyam](#architektúra-és-adatfolyam)
3. [Metrika Típusok Részletesen](#metrika-típusok-részletesen)
4. [Python Implementáció](#python-implementáció)
5. [LangGraph Integráció](#langgraph-integráció)
6. [Grafana Dashboard Konfiguráció](#grafana-dashboard-konfiguráció)
7. [Teljes Példák](#teljes-példák)
8. [Legjobb Gyakorlatok](#legjobb-gyakorlatok)

---

## 📊 Áttekintés

### Mi ez a monitoring stack?

Az AI Agent projekt egy **háromszintű megfigyelhetőségi stacket** használ:

```
Python Alkalmazás (LangGraph Agent)
         ↓ (metrikákat rögzít)
    Prometheus Client Library
         ↓ (/metrics végpontot szolgáltat)
    Prometheus Szerver (gyűjt és tárol)
         ↓ (lekérdezés PromQL-lel)
    Grafana Dashboardok (vizualizál)
```

### Főbb Komponensek

| Komponens | Szerep | Port | Technológia |
|-----------|--------|------|-------------|
| **Backend** | Metrikákat generál az agent végrehajtás során | 8001 | FastAPI + LangGraph + prometheus_client |
| **Prometheus** | Gyűjt, idősorozat adatokat tárol | 9090 | Prometheus TSDB |
| **Grafana** | Metrikákat vizualizál dashboardokon | 3001 | Grafana |

---

## 🏗️ Architektúra és Adatfolyam

### Teljes Monitoring Folyamat

```
┌─────────────────────────────────────────────────────────────────┐
│                 1. FELHASZNÁLÓ ÜZENETET KÜLD                    │
│               "Milyen idő van Budapesten?"                      │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              2. LANGGRAPH AGENT FELDOLGOZZA A KÉRÉST            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Node: agent_decide                                      │  │
│  │  → record_node_duration("agent_decide") időzítő indul    │  │
│  │  → instrumented_llm_call() LLM metrikákat rögzít:        │  │
│  │     • llm_inference_count +1                             │  │
│  │     • llm_inference_token_input_total +450               │  │
│  │     • llm_inference_token_output_total +85               │  │
│  │     • llm_inference_latency_seconds 1.2s                 │  │
│  │     • llm_cost_total_usd +$0.015                         │  │
│  │  → record_node_duration() befejeződik:                   │  │
│  │     • node_execution_latency_seconds{node="agent_decide"}│  │
│  └──────────────────────────────────────────────────────────┘  │
│                         ↓                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Node: tool_execution                                    │  │
│  │  → record_tool_call("weather") időzítő indul             │  │
│  │  → Weather API hívás                                     │  │
│  │  → record_tool_call() befejeződik:                       │  │
│  │     • tool_invocation_count{tool="weather"} +1           │  │
│  │     • agent_tool_duration_seconds{tool="weather"} 0.8s   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                         ↓                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Agent befejezi a végrehajtást                           │  │
│  │  → agent_execution_count +1                              │  │
│  │  → agent_execution_latency_seconds 2.5s                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│       3. BACKEND KISZOLGÁLJA A METRIKÁKAT /metrics VÉGPONTON    │
│                                                                 │
│  GET http://localhost:8001/metrics visszaad:                   │
│                                                                 │
│  # HELP llm_inference_count Összes LLM inferencia hívás        │
│  # TYPE llm_inference_count counter                            │
│  llm_inference_count{model="gpt-4o-mini"} 1.0                  │
│                                                                 │
│  # HELP llm_inference_token_input_total Bemeneti tokenek       │
│  # TYPE llm_inference_token_input_total counter                │
│  llm_inference_token_input_total{model="gpt-4o-mini"} 450.0    │
│                                                                 │
│  # HELP tool_invocation_count Eszköz hívások                   │
│  # TYPE tool_invocation_count counter                          │
│  tool_invocation_count{tool="weather"} 1.0                     │
│                                                                 │
│  ... (és 20+ további metrika)                                  │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│      4. PROMETHEUS LEGYŰJTI A /metrics-t 15 MÁSODPERCENKÉNT     │
│                                                                 │
│  Prometheus konfiguráció (prometheus.yml):                     │
│                                                                 │
│  scrape_configs:                                               │
│    - job_name: 'ai-agent'                                      │
│      static_configs:                                           │
│        - targets: ['ai-agent-backend:8000']                    │
│      scrape_interval: 15s                                      │
│                                                                 │
│  → Prometheus tárolja a metrikákat idősorozat adatbázisban     │
│  → Megőrzés: 15 nap vagy 10GB                                  │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│          5. GRAFANA LEKÉRDEZI A PROMETHEUS-t PromQL-lel         │
│                                                                 │
│  Dashboard Panel Konfiguráció:                                 │
│                                                                 │
│  Lekérdezés: rate(llm_inference_count[5m])                     │
│  Jelmagyarázat: {{model}}                                      │
│  Vizualizáció: Idősorozat Grafikon                             │
│                                                                 │
│  → Grafana lekéri az adatokat Prometheus-ból 5-30s-enként      │
│  → Interaktív grafikonokat jelenít meg zoom, pan, időtartomány │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📏 Metrika Típusok Részletesen

A Prometheus **4 fő metrika típust** támogat. Megértésük kritikus a helyes instrumentációhoz.

### 1. Counter (Számláló)

**Definíció**: Monoton növekvő érték, ami csak nő (vagy újraindul nullára restart esetén).

**Mikor használjuk**: Események számolása, amik idővel felhalmozódnak.

**Python Példa**:
```python
from prometheus_client import Counter

# Számláló definiálása
llm_inference_count = Counter(
    name='llm_inference_count',
    documentation='Összes LLM inferencia hívás',
    labelnames=['model']  # Címkék csoportosításhoz
)

# Számláló használata
llm_inference_count.labels(model="gpt-4o-mini").inc()  # Növelés 1-gyel
llm_inference_count.labels(model="gpt-4o-mini").inc(5)  # Növelés 5-tel
```

**Valós példa a projektből**:
```python
# Fájl: backend/observability/metrics.py

tool_invocation_count = Counter(
    name='tool_invocation_count',
    documentation='Összes eszköz hívás',
    labelnames=['tool']
)

# Használat a backend/services/tools.py-ban:
with record_tool_call("weather"):
    result = await self.client.get_forecast(...)
    # Belül növeli: tool_invocation_count{tool="weather"}
```

**PromQL lekérdezések számlálókhoz**:
```promql
# Teljes szám
llm_inference_count{model="gpt-4o-mini"}

# Másodpercenkénti arány 5 perc alatt
rate(llm_inference_count[5m])

# Teljes növekedés 1 óra alatt
increase(llm_inference_count[1h])
```

---

### 2. Gauge (Mérő)

**Definíció**: Érték, ami nőhet vagy csökkenhet (aktuális állapot/szint).

**Mikor használjuk**: Aktuális értékek mérése, mint hőmérséklet, memóriahasználat, sorhossz.

**Python Példa**:
```python
from prometheus_client import Gauge

# Mérő definiálása
active_connections = Gauge(
    name='active_connections',
    documentation='Aktív kapcsolatok jelenlegi száma'
)

# Mérő használata
active_connections.set(42)  # Beállítás konkrét értékre
active_connections.inc()    # Növelés 1-gyel
active_connections.dec(5)   # Csökkentés 5-tel
```

**Valós példa a projektből**:
```python
# Fájl: backend/observability/metrics.py

rag_recall_rate = Gauge(
    name='rag_recall_rate',
    documentation='RAG visszahívási arány (származtatott relevancia metrika)'
)

# Használat:
rag_recall_rate.set(0.87)  # 87% visszahívási arány
```

**PromQL lekérdezések mérőkhöz**:
```promql
# Jelenlegi érték
rag_recall_rate

# Átlag időben
avg_over_time(rag_recall_rate[5m])

# Maximum érték az elmúlt órában
max_over_time(rag_recall_rate[1h])
```

---

### 3. Histogram (Hisztogram)

**Definíció**: Megfigyeléseket mintáz és konfigurálható kosárba számolja őket. Automatikusan szolgáltat count, sum és kvantilis számításokat.

**Mikor használjuk**: Eloszlások mérése (késleltetés, kérés méretek, időtartamok).

**Python Példa**:
```python
from prometheus_client import Histogram

# Hisztogram definiálása
request_duration_seconds = Histogram(
    name='request_duration_seconds',
    documentation='Kérés időtartama másodpercben',
    labelnames=['method'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]  # Egyéni kosarak
)

# Hisztogram használata
request_duration_seconds.labels(method="GET").observe(1.2)  # 1.2 mp rögzítése
```

**Valós példa a projektből**:
```python
# Fájl: backend/observability/metrics.py

llm_inference_latency_seconds = Histogram(
    name='llm_inference_latency_seconds',
    documentation='LLM inferencia hívások késleltetése másodpercben',
    labelnames=['model'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

# Használat a backend/observability/llm_instrumentation.py-ban:
start_time = time.time()
response = await llm.ainvoke(messages)
duration = time.time() - start_time
llm_inference_latency_seconds.labels(model="gpt-4o-mini").observe(duration)
```

**Mit hoz létre a hisztogram**:
```
# Három metrika automatikusan generálódik:
llm_inference_latency_seconds_bucket{model="gpt-4o-mini",le="0.5"} 10
llm_inference_latency_seconds_bucket{model="gpt-4o-mini",le="1.0"} 45
llm_inference_latency_seconds_bucket{model="gpt-4o-mini",le="5.0"} 98
llm_inference_latency_seconds_sum{model="gpt-4o-mini"} 123.4
llm_inference_latency_seconds_count{model="gpt-4o-mini"} 100
```

**PromQL lekérdezések hisztogramokhoz**:
```promql
# 95. percentilis késleltetés számítása
histogram_quantile(0.95, rate(llm_inference_latency_seconds_bucket[5m]))

# 50. percentilis (medián) számítása
histogram_quantile(0.50, rate(llm_inference_latency_seconds_bucket[5m]))

# Átlag késleltetés
rate(llm_inference_latency_seconds_sum[5m]) / rate(llm_inference_latency_seconds_count[5m])
```

---

### 4. Summary (Összegzés)

**Definíció**: Hasonló a hisztogramhoz, de kliensoldali kvantilisokat számol.

**Mikor használjuk**: Ha pontos kvantilisokra van szükség, de nincs szükség példányok közötti aggregációra.

**Megjegyzés**: Ez a projekt **Hisztogramokat** használ Összegzések helyett, mert a hisztogramok rugalmasabbak elosztott rendszerekben történő aggregációhoz.

---

## 🐍 Python Implementáció

### 1. Lépés: Függőségek Telepítése

```bash
# A backend/requirements.txt-ben
prometheus-client==0.19.0
```

### 2. Lépés: Metrikák Definiálása

**Fájl: `backend/observability/metrics.py`**

```python
import os
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

# Registry létrehozása
registry = CollectorRegistry()

# Metrikák definiálása
llm_inference_count = Counter(
    name='llm_inference_count',
    documentation='Összes LLM inferencia hívás',
    labelnames=['model'],
    registry=registry
)

llm_inference_latency_seconds = Histogram(
    name='llm_inference_latency_seconds',
    documentation='LLM inferencia hívások késleltetése másodpercben',
    labelnames=['model'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    registry=registry
)

tool_invocation_count = Counter(
    name='tool_invocation_count',
    documentation='Összes eszköz hívás',
    labelnames=['tool'],
    registry=registry
)
```

### 3. Lépés: Metrikák Rögzítése a Kódban

#### 1. Példa: LLM Hívások Rögzítése

**Fájl: `backend/observability/llm_instrumentation.py`**

```python
import time
from observability.metrics import (
    llm_inference_count,
    llm_inference_latency_seconds,
    llm_inference_token_input_total,
    llm_inference_token_output_total,
    llm_cost_total_usd
)

async def instrumented_llm_call(llm, messages, model: str):
    """Wrapper, ami automatikusan rögzíti az LLM metrikákat."""
    
    # Időzítés indítása
    start_time = time.time()
    
    try:
        # Tényleges LLM hívás
        response = await llm.ainvoke(messages)
        
        # Időtartam számítása
        duration = time.time() - start_time
        
        # Token használat kinyerése
        prompt_tokens = response.usage_metadata.get('input_tokens', 0)
        completion_tokens = response.usage_metadata.get('output_tokens', 0)
        
        # Metrikák rögzítése
        llm_inference_count.labels(model=model).inc()
        llm_inference_latency_seconds.labels(model=model).observe(duration)
        llm_inference_token_input_total.labels(model=model).inc(prompt_tokens)
        llm_inference_token_output_total.labels(model=model).inc(completion_tokens)
        
        # Költség számítása és rögzítése
        cost = calculate_cost(model, prompt_tokens, completion_tokens)
        llm_cost_total_usd.labels(model=model).inc(cost)
        
        return response
        
    except Exception as e:
        # Hiba metrikák rögzítése
        duration = time.time() - start_time
        llm_inference_latency_seconds.labels(model=model).observe(duration)
        raise
```

#### 2. Példa: Eszköz Hívások Rögzítése Context Manager-rel

**Fájl: `backend/observability/metrics.py`**

```python
import time
from contextlib import contextmanager
from observability.metrics import tool_invocation_count, agent_tool_duration_seconds

@contextmanager
def record_tool_call(tool_name: str):
    """
    Context manager eszköz hívás metrikák rögzítéséhez.
    
    Használat:
        with record_tool_call("weather"):
            result = await weather_api.get_forecast()
    """
    start_time = time.time()
    
    try:
        yield
        # Sikeres útvonal
        tool_invocation_count.labels(tool=tool_name).inc()
    except Exception as e:
        # Hiba útvonal - hívást továbbra is rögzítjük
        tool_invocation_count.labels(tool=tool_name).inc()
        raise
    finally:
        # Mindig rögzítjük az időtartamot
        duration = time.time() - start_time
        agent_tool_duration_seconds.labels(
            tool=tool_name,
            environment="dev"
        ).observe(duration)
```

**Használat a `backend/services/tools.py`-ban**:

```python
from observability.metrics import record_tool_call

class WeatherTool:
    async def execute(self, city: str):
        with record_tool_call("weather"):
            logger.info(f"Weather API hívás: {city}")
            result = await self.client.get_forecast(city=city)
            return result
```

#### 3. Példa: Node Végrehajtási Idők Rögzítése

**Fájl: `backend/observability/metrics.py`**

```python
@contextmanager
def record_node_duration(node_name: str):
    """
    Context manager LangGraph node végrehajtási idő rögzítéséhez.
    
    Használat:
        with record_node_duration("agent_decide"):
            state = await _agent_decide_node(state)
    """
    start_time = time.time()
    
    try:
        yield
    finally:
        duration = time.time() - start_time
        node_execution_latency_seconds.labels(node=node_name).observe(duration)
        agent_node_executions_total.labels(
            node=node_name,
            environment="dev"
        ).inc()
```

### 4. Lépés: Metrika Végpont Kiszolgálása

**Fájl: `backend/main.py`**

```python
from fastapi import FastAPI
from prometheus_client import make_asgi_app, generate_latest, CONTENT_TYPE_LATEST
from observability.metrics import registry, init_metrics

app = FastAPI()

# Metrikák inicializálása metaadatokkal
init_metrics(environment="dev", version="1.0.0")

# Prometheus metrika végpont csatolása a /metrics címen
metrics_app = make_asgi_app(registry=registry)
app.mount("/metrics", metrics_app)

# Vagy manuális végpont:
@app.get("/metrics")
async def metrics():
    from starlette.responses import Response
    return Response(
        content=generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST
    )
```

### 5. Lépés: Metrika Végpont Tesztelése

```bash
# Backend indítása
docker-compose up -d backend

# Teszt kérés küldése metrikák generálásához
curl -X POST http://localhost:8001/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "Milyen idő van?"}'

# Metrika végpont ellenőrzése
curl http://localhost:8001/metrics

# Kimenet:
# HELP llm_inference_count Összes LLM inferencia hívás
# TYPE llm_inference_count counter
llm_inference_count{model="gpt-4o-mini"} 1.0
# HELP tool_invocation_count Összes eszköz hívás
# TYPE tool_invocation_count counter
tool_invocation_count{tool="weather"} 1.0
```

---

## 🔗 LangGraph Integráció

### Hogyan Rögzítik a LangGraph Node-ok a Metrikákat

**Fájl: `backend/services/agent.py`**

```python
from langgraph.graph import StateGraph, END
from observability.metrics import record_node_duration
from observability.llm_instrumentation import instrumented_llm_call

class AIAgent:
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        self.graph = self._build_graph()
    
    def _build_graph(self):
        workflow = StateGraph(AgentState)
        
        # Node-ok hozzáadása metrika instrumentációval
        workflow.add_node("agent_decide", self._agent_decide_node)
        workflow.add_node("tool_execution", self._tool_execution_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Élek hozzáadása...
        return workflow.compile()
    
    async def _agent_decide_node(self, state: AgentState) -> AgentState:
        """
        LangGraph node, ami LLM döntést hoz.
        Rögzíti: node végrehajtási idő, LLM metrikák
        """
        with record_node_duration("agent_decide"):
            # Üzenetek előkészítése
            messages = self._prepare_messages(state)
            
            # LLM hívás instrumentációval
            response = await instrumented_llm_call(
                llm=self.llm,
                messages=messages,
                model="gpt-4o-mini",
                agent_execution_id=state.get("agent_execution_id")
            )
            
            # Döntés feldolgozása
            decision = self._parse_decision(response.content)
            
            return {
                **state,
                "last_decision": decision,
                "messages": state["messages"] + [response]
            }
    
    async def _tool_execution_node(self, state: AgentState) -> AgentState:
        """
        LangGraph node, ami eszközöket hajt végre.
        Rögzíti: node végrehajtási idő, eszköz hívás metrikák
        """
        with record_node_duration("tool_execution"):
            decision = state["last_decision"]
            tool_name = decision["tool_name"]
            arguments = decision["arguments"]
            
            # Eszköz keresése és végrehajtása (az eszköz már rögzíti saját metrikáit)
            tool = self.tools[tool_name]
            result = await tool.execute(**arguments)
            
            return {
                **state,
                "tool_results": state.get("tool_results", []) + [result]
            }
```

### Teljes Folyamat Példa

```python
# Felhasználó küldi: "Milyen idő van Budapesten?"

# 1. Agent graph elindítja a végrehajtást
#    → agent_execution_count.inc()
#    → Időzítő indul az agent_execution_latency_seconds-hez

# 2. Node: agent_decide
#    with record_node_duration("agent_decide"):  # ← Node időzítő indul
#        response = await instrumented_llm_call(...)  # ← LLM metrikák rögzítve
#        # Az instrumented_llm_call() belsejében:
#        #   llm_inference_count.labels(model="gpt-4o-mini").inc()
#        #   llm_inference_token_input_total.labels(model="gpt-4o-mini").inc(450)
#        #   llm_inference_token_output_total.labels(model="gpt-4o-mini").inc(85)
#        #   llm_inference_latency_seconds.labels(model="gpt-4o-mini").observe(1.2)
#        #   llm_cost_total_usd.labels(model="gpt-4o-mini").inc(0.015)
#    # Node időzítő vége:
#    #   node_execution_latency_seconds.labels(node="agent_decide").observe(1.3)

# 3. Node: tool_execution
#    with record_node_duration("tool_execution"):  # ← Node időzítő indul
#        with record_tool_call("weather"):  # ← Eszköz időzítő indul
#            result = await weather_client.get_forecast(city="Budapest")
#        # Eszköz időzítő vége:
#        #   tool_invocation_count.labels(tool="weather").inc()
#        #   agent_tool_duration_seconds.labels(tool="weather").observe(0.8)
#    # Node időzítő vége:
#    #   node_execution_latency_seconds.labels(node="tool_execution").observe(0.9)

# 4. Agent befejeződik
#    → agent_execution_latency_seconds.observe(2.5)
```

---

## 📈 Grafana Dashboard Konfiguráció

### Hogyan Jeleníthetjük Meg a Metrikákat a Grafanában

#### 1. Lépés: Adatforrás Konfigurálása

**Fájl: `observability/grafana/provisioning/datasources/prometheus.yml`**

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    jsonData:
      timeInterval: "15s"
```

#### 2. Lépés: Dashboard Panel Létrehozása

**Példa: LLM Inferencia Szám Grafikon**

```json
{
  "title": "LLM Inferencia Szám (arány)",
  "type": "timeseries",
  "datasource": {
    "type": "prometheus",
    "uid": "PBFA97CFB590B2093"
  },
  "targets": [
    {
      "expr": "rate(llm_inference_count[5m])",
      "legendFormat": "{{model}}",
      "refId": "A"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "ops",
      "custom": {
        "lineWidth": 2,
        "fillOpacity": 10
      }
    }
  }
}
```

#### 3. Lépés: Gyakori PromQL Lekérdezések Dashboardokhoz

##### LLM Dashboard Panelek

**Panel 1: LLM Inferencia Arány**
```promql
# Lekérdezés:
rate(llm_inference_count[5m])

# Jelmagyarázat: {{model}}
# Vizualizáció: Idősorozat
# Egység: ops (műveletek másodpercenként)
```

**Panel 2: Token Használat Modell Szerint**
```promql
# Bemeneti tokenek:
rate(llm_inference_token_input_total[5m])

# Kimeneti tokenek:
rate(llm_inference_token_output_total[5m])

# Jelmagyarázat: {{model}} - bemenet/kimenet
# Vizualizáció: Halmozott Területdiagram
# Egység: tokenek/mp
```

**Panel 3: LLM Késleltetés Percentilisek**
```promql
# p50 (medián):
histogram_quantile(0.50, rate(llm_inference_latency_seconds_bucket[5m]))

# p95:
histogram_quantile(0.95, rate(llm_inference_latency_seconds_bucket[5m]))

# p99:
histogram_quantile(0.99, rate(llm_inference_latency_seconds_bucket[5m]))

# Jelmagyarázat: p50, p95, p99
# Vizualizáció: Idősorozat több lekérdezéssel
# Egység: másodpercek
```

**Panel 4: Teljes Költség**
```promql
# Lekérdezés:
sum(llm_cost_total_usd)

# Vizualizáció: Stat (egyetlen szám)
# Egység: currency USD ($)
```

##### Agent Munkafolyamat Dashboard Panelek

**Panel 5: Eszköz Hívás Részletezés**
```promql
# Lekérdezés:
sum by (tool) (increase(tool_invocation_count[5m]))

# Jelmagyarázat: {{tool}}
# Vizualizáció: Oszlopdiagram vagy Kördiagram
# Egység: short (darabszám)
```

**Panel 6: Node Végrehajtási Késleltetés**
```promql
# Átlagos késleltetés node-onként:
sum by (node) (rate(node_execution_latency_seconds_sum[5m])) 
  / 
sum by (node) (rate(node_execution_latency_seconds_count[5m]))

# Jelmagyarázat: {{node}}
# Vizualizáció: Idősorozat
# Egység: másodpercek
```

**Panel 7: Agent Végrehajtás Szám**
```promql
# Lekérdezés:
increase(agent_execution_count[5m])

# Vizualizáció: Stat vagy Idősorozat
# Egység: short
```

##### Költség Dashboard Panelek

**Panel 8: Költség Modell Szerint (Utolsó Óra)**
```promql
# Lekérdezés:
sum by (model) (increase(llm_cost_total_usd[1h]))

# Jelmagyarázat: {{model}}
# Vizualizáció: Kördiagram
# Egység: currency USD ($)
```

**Panel 9: Költési Ütem (Költség Naponta)**
```promql
# Lekérdezés:
sum(increase(llm_cost_total_usd[24h]))

# Vizualizáció: Stat trenddel
# Egység: currency USD ($)
```

**Panel 10: Költség Munkafolyamatonként**
```promql
# Lekérdezés:
sum(increase(llm_cost_total_usd[5m])) 
  / 
sum(increase(agent_execution_count[5m]))

# Vizualizáció: Mérő
# Egység: currency USD ($)
```

---

## 🔬 Teljes Példák

### 1. Példa: Új Metrika Hozzáadása

**Forgatókönyv**: Követjük, hányszor állítják vissza a felhasználók a beszélgetési kontextust.

#### 1. Lépés: Metrika Definiálása

**Fájl: `backend/observability/metrics.py`**

```python
context_reset_count = Counter(
    name='context_reset_count',
    documentation='Kontextus visszaállítások teljes száma',
    labelnames=['user_id'],  # ⚠️ Óvatosan használandó - magas kardinalitást okozhat
    registry=registry
)
```

#### 2. Lépés: Metrika Rögzítése

**Fájl: `backend/services/chat_service.py`**

```python
from observability.metrics import context_reset_count

class ChatService:
    async def process_message(self, user_id: str, message: str):
        # Reset parancs észlelése
        if message.lower().strip() == "reset context":
            # Session törlése
            await self.conversation_repo.clear_session(user_id)
            
            # Metrika rögzítése
            context_reset_count.labels(user_id=user_id).inc()
            
            return "Kontextus sikeresen visszaállítva"
```

#### 3. Lépés: Grafana Panel Létrehozása

```json
{
  "title": "Kontextus Visszaállítások (Utolsó Óra)",
  "type": "stat",
  "targets": [
    {
      "expr": "sum(increase(context_reset_count[1h]))",
      "refId": "A"
    }
  ]
}
```

---

### 2. Példa: Többdimenziós Metrikák

**Forgatókönyv**: Eszköz sikeres vs. sikertelen arányok követése eszközönként.

#### 1. Lépés: Státusz Címke Hozzáadása

**Fájl: `backend/observability/metrics.py`**

```python
@contextmanager
def record_tool_call(tool_name: str):
    start_time = time.time()
    status = "success"  # Alapértelmezett
    
    try:
        yield
    except Exception as e:
        status = "error"
        raise
    finally:
        duration = time.time() - start_time
        
        # Rögzítés státusz címkével
        tool_invocation_count.labels(
            tool=tool_name,
            status=status  # ← Státusz dimenzió hozzáadva
        ).inc()
        
        agent_tool_duration_seconds.labels(
            tool=tool_name
        ).observe(duration)
```

#### 2. Lépés: Metrika Definíció Frissítése

```python
tool_invocation_count = Counter(
    name='tool_invocation_count',
    documentation='Összes eszköz hívás',
    labelnames=['tool', 'status'],  # ← Státusz címke hozzáadva
    registry=registry
)
```

#### 3. Lépés: Lekérdezés Grafanában

```promql
# Sikeres arány:
sum by (tool) (rate(tool_invocation_count{status="success"}[5m]))
  / 
sum by (tool) (rate(tool_invocation_count[5m]))

# Hiba szám:
sum by (tool) (increase(tool_invocation_count{status="error"}[5m]))
```

---

## 🎯 Legjobb Gyakorlatok

### 1. Címke Kardinalitás

**❌ ROSSZ** - Magas kardinalitás (címkekombinációk milliói):
```python
request_count = Counter(
    'request_count',
    'Összes kérés',
    labelnames=['user_id', 'session_id', 'request_id']  # ❌ Túl sok egyedi érték!
)
```

**✅ JÓ** - Alacsony kardinalitás (korlátozott egyedi értékek):
```python
request_count = Counter(
    'request_count',
    'Összes kérés',
    labelnames=['status', 'endpoint']  # ✅ Kevés egyedi érték
)
```

**Szabály**: A címkéknek címkénként **< 100 egyedi értékkel** kell rendelkezniük.

---

### 2. Hisztogram Használata Késleltetéshez

**❌ ROSSZ** - Átlag használata számlálóból:
```python
total_duration = Counter('total_duration', 'Teljes időtartam')
request_count = Counter('request_count', 'Kérések')

# Átlag = total_duration / request_count  # ❌ Elveszíti az eloszlás információt
```

**✅ JÓ** - Hisztogram használata:
```python
request_duration = Histogram(
    'request_duration_seconds',
    'Kérés időtartam',
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0]  # ✅ Percentilisek számíthatók
)
```

---

### 3. Elnevezési Konvenciók

Kövessük a Prometheus elnevezési konvenciókat:

```python
# ✅ JÓ nevek:
llm_inference_count            # Számláló - _total vagy _count végződéssel
llm_inference_latency_seconds  # Hisztogram - egységet tartalmaz (_seconds)
active_connections             # Mérő - jelenlegi állapotot ír le

# ❌ ROSSZ nevek:
LLMInferenceCount             # snake_case-t használj, ne CamelCase-t
llm_latency_ms                # Alapegységeket használj (másodperc, nem ezredmásodperc)
tool_calls_total_count        # Redundáns (_total már jelzi a count-ot)
```

---

### 4. Metrika Hatáskör

**Globálisan definiálj, lokálisan használj**:

```python
# ✅ JÓ - Egyszer definiálva a metrics.py-ban
# backend/observability/metrics.py
request_count = Counter('request_count', 'Kérések')

# Használd mindenhol
# backend/services/agent.py
from observability.metrics import request_count
request_count.inc()

# ❌ ROSSZ - Ne definiáld újra több fájlban
```

---

### 5. Hibakezelés

**Mindig rögzítsd a metrikákat, még hibák esetén is**:

```python
@contextmanager
def record_operation():
    start_time = time.time()
    status = "error"  # Alapértelmezett hiba
    
    try:
        yield
        status = "success"  # Csak siker esetén állítsd be
    finally:
        # Mindig rögzítsd, még kivétel esetén is
        duration = time.time() - start_time
        operation_count.labels(status=status).inc()
        operation_duration.observe(duration)
```

---

## � Fejlett Megfigyelhetőségi Funkciók

A projekt a standard metrikák mellett fejlett megfigyelhetőségi funkciókat is tartalmaz, amelyek mélyebb betekintést nyújtanak az agent működésébe.

### 1. Prompt Lineage (Prompt Leszármazás Követés)

**Kód Lokáció**: `backend/observability/prompt_lineage.py`

**Mi ez?**: Minden LLM híváshoz rögzíti a prompt hash-ét, verzióját és metaadatait, lehetővé téve a prompt evolúció követését és az LLM viselkedés debug-olását.

**Implementáció**:

```python
# Fájl: backend/observability/prompt_lineage.py

@dataclass
class PromptLineage:
    """Prompt leszármazási rekord LLM hívások követésére."""
    prompt_hash: str           # SHA256 hash a teljes prompt szövegről
    request_id: str            # Egyedi kérés azonosító
    agent_execution_id: str    # Egyedi agent végrehajtás azonosító
    model_name: str            # Használt LLM modell
    timestamp: str             # ISO timestamp
    prompt_version: Optional[str] = None  # Prompt template verzió
    message_count: int = 0     # Üzenetek száma
    total_chars: int = 0       # Összes karakter szám

class PromptLineageTracker:
    """Követi a prompt leszármazást LLM hívásokon keresztül."""
    
    def track_prompt(
        self,
        messages: List[BaseMessage],
        model_name: str,
        agent_execution_id: str,
        prompt_version: Optional[str] = None
    ) -> PromptLineage:
        """
        Prompt hívás követése.
        
        Rögzíti:
        - Prompt hash (SHA256)
        - Üzenetek száma
        - Karakter szám
        - Időbélyeg
        - Model név
        """
        prompt_text = self._messages_to_text(messages)
        prompt_hash = self._hash_prompt(prompt_text)
        
        lineage = PromptLineage(
            prompt_hash=prompt_hash,
            request_id=get_request_id(),
            agent_execution_id=agent_execution_id,
            model_name=model_name,
            timestamp=datetime.utcnow().isoformat(),
            message_count=len(messages),
            total_chars=len(prompt_text)
        )
        
        self._lineage_records.append(lineage)
        return lineage
```

**Használat a kódban**:

```python
# Fájl: backend/observability/llm_instrumentation.py

from observability.prompt_lineage import get_prompt_tracker

async def instrumented_llm_call(llm, messages, model, agent_execution_id):
    # Prompt lineage követés
    if agent_execution_id:
        tracker = get_prompt_tracker()
        tracker.track_prompt(
            messages=messages,
            model_name=model,
            agent_execution_id=agent_execution_id
        )
    
    # LLM hívás
    response = await llm.ainvoke(messages)
    return response
```

**Mit nyújt?**:
- ✅ Prompt verzió követés időben
- ✅ Azonos prompt ismétlődések észlelése
- ✅ LLM viselkedés debug-olás prompt alapján
- ✅ A/B tesztelés támogatás különböző prompt verziókhoz

---

### 2. Agent Decision Trace (LangGraph State Snapshots)

**Kód Lokáció**: `backend/observability/state_tracker.py`

**Mi ez?**: LangGraph állapot pillanatfelvételek rögzítése kritikus pontokon az agent végrehajtás során (végrehajtás előtt, minden node után, befejezéskor).

**Implementáció**:

```python
# Fájl: backend/observability/state_tracker.py

@dataclass
class StateSnapshot:
    """LangGraph állapot pillanatfelvétel egy adott végrehajtási ponton."""
    snapshot_id: str           # Egyedi snapshot azonosító
    agent_execution_id: str    # Agent végrehajtás azonosító
    timestamp: str             # ISO timestamp
    snapshot_type: str         # before_execution, after_node, after_completion
    node_name: Optional[str]   # Node neve (ha alkalmazható)
    state_summary: Dict[str, Any]  # Összefoglalt állapot (teljes prompt nélkül)
    metadata: Dict[str, Any]   # További metaadatok

class StateTracker:
    """LangGraph állapot pillanatfelvételek követése agent döntések nyomkövetéséhez."""
    
    def snapshot_before_execution(
        self,
        agent_execution_id: str,
        initial_state: Dict[str, Any]
    ) -> StateSnapshot:
        """Állapot rögzítése az agent végrehajtás kezdete előtt."""
        snapshot = self._create_snapshot(
            agent_execution_id=agent_execution_id,
            snapshot_type="before_execution",
            state=initial_state
        )
        logger.info(f"State snapshot (before): exec_id={agent_execution_id}")
        return snapshot
    
    def snapshot_after_node(
        self,
        agent_execution_id: str,
        node_name: str,
        state: Dict[str, Any]
    ) -> StateSnapshot:
        """Állapot rögzítése egy node végrehajtása után."""
        snapshot = self._create_snapshot(
            agent_execution_id=agent_execution_id,
            snapshot_type="after_node",
            node_name=node_name,
            state=state
        )
        logger.info(f"State snapshot (after_node): node={node_name}")
        return snapshot
    
    def snapshot_after_completion(
        self,
        agent_execution_id: str,
        final_state: Dict[str, Any]
    ) -> StateSnapshot:
        """Állapot rögzítése az agent végrehajtás befejezése után."""
        snapshot = self._create_snapshot(
            agent_execution_id=agent_execution_id,
            snapshot_type="after_completion",
            state=final_state
        )
        logger.info(f"State snapshot (completion): exec_id={agent_execution_id}")
        return snapshot
```

**Használat az agent kódban**:

```python
# Fájl: backend/services/agent.py

from observability.state_tracker import get_state_tracker

class AIAgent:
    async def run(self, user_id: str, message: str):
        agent_execution_id = f"exec_{uuid.uuid4().hex[:12]}"
        state_tracker = get_state_tracker()
        
        # Kezdeti állapot rögzítése
        initial_state = {"user_id": user_id, "message": message}
        state_tracker.snapshot_before_execution(
            agent_execution_id=agent_execution_id,
            initial_state=initial_state
        )
        
        # Graph végrehajtás - minden node után automatikus snapshot
        result = await self.graph.ainvoke(initial_state)
        
        # Végső állapot rögzítése
        state_tracker.snapshot_after_completion(
            agent_execution_id=agent_execution_id,
            final_state=result
        )
        
        return result
```

**Mit nyújt?**:
- ✅ Agent döntések teljes nyomkövetése
- ✅ Node-ok közötti állapotváltozások láthatósága
- ✅ Debug támogatás komplex multi-step folyamatokhoz
- ✅ Replay képesség - állapotok újrajátszása

---

### 3. Token-szintű Költségfigyelés

**Kód Lokáció**: `backend/observability/metrics.py` és `backend/observability/llm_instrumentation.py`

**Mi ez?**: Részletes token használat és költség követés modell szerint, bemeneti/kimeneti tokenek külön rögzítésével.

**Implementáció**:

```python
# Fájl: backend/observability/metrics.py

# Token metrikák
llm_inference_token_input_total = Counter(
    name='llm_inference_token_input_total',
    documentation='Összes bemeneti token LLM által feldolgozva',
    labelnames=['model'],
    registry=registry
)

llm_inference_token_output_total = Counter(
    name='llm_inference_token_output_total',
    documentation='Összes kimeneti token LLM által generálva',
    labelnames=['model'],
    registry=registry
)

llm_cost_total_usd = Counter(
    name='llm_cost_total_usd',
    documentation='Teljes költség USD-ben LLM inferenciára',
    labelnames=['model'],
    registry=registry
)

# Költség számítás
def _estimate_llm_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    LLM költség becslése USD-ben token használat alapján.
    
    Árképzési táblázat (USD per 1K token) - 2026. Jan:
    """
    PRICING = {
        "gpt-4o": (0.005, 0.015),           # input, output
        "gpt-4o-mini": (0.00015, 0.0006),   # $0.15/$0.60 per 1M token
        "gpt-4-turbo-preview": (0.01, 0.03),
        "gpt-3.5-turbo": (0.0015, 0.002),
    }
    
    input_price, output_price = PRICING.get(model, PRICING["gpt-4"])
    
    cost = (prompt_tokens / 1000.0 * input_price) + \
           (completion_tokens / 1000.0 * output_price)
    
    return cost
```

**Token és költség rögzítés**:

```python
# Fájl: backend/observability/llm_instrumentation.py

async def instrumented_llm_call(llm, messages, model: str):
    start_time = time.time()
    
    # LLM hívás
    response = await llm.ainvoke(messages)
    duration = time.time() - start_time
    
    # Token használat kinyerése
    prompt_tokens = response.usage_metadata.get('input_tokens', 0)
    completion_tokens = response.usage_metadata.get('output_tokens', 0)
    
    # Metrikák rögzítése
    llm_inference_count.labels(model=model).inc()
    llm_inference_token_input_total.labels(model=model).inc(prompt_tokens)
    llm_inference_token_output_total.labels(model=model).inc(completion_tokens)
    llm_inference_latency_seconds.labels(model=model).observe(duration)
    
    # Költség számítás és rögzítés
    cost = _estimate_llm_cost(model, prompt_tokens, completion_tokens)
    llm_cost_total_usd.labels(model=model).inc(cost)
    
    logger.info(
        f"LLM call completed: model={model} "
        f"tokens_in={prompt_tokens} tokens_out={completion_tokens} "
        f"cost=${cost:.4f} duration={duration:.2f}s"
    )
    
    return response
```

**Grafana lekérdezések költség követéshez**:

```promql
# Teljes költség modell szerint
sum by (model) (llm_cost_total_usd)

# Költség arány ($/óra)
rate(llm_cost_total_usd[1h]) * 3600

# Token használat arány
rate(llm_inference_token_input_total[5m])
rate(llm_inference_token_output_total[5m])

# Átlagos költség hívásonként
sum(increase(llm_cost_total_usd[5m])) / sum(increase(llm_inference_count[5m]))
```

**Mit nyújt?**:
- ✅ Valós idejű költség monitoring
- ✅ Token használat optimalizálás
- ✅ Budget riasztások beállítása
- ✅ Modell költség összehasonlítás

---

### 4. Model Fallback Path Látása

**Kód Lokáció**: `backend/observability/llm_instrumentation.py` és `backend/observability/metrics.py`

**Mi ez?**: Automatikus tartalék modell (fallback) használat követése, amikor az elsődleges modell hibázik.

**Implementáció**:

```python
# Fájl: backend/observability/metrics.py

model_fallback_count = Counter(
    name='model_fallback_count',
    documentation='Model fallback előfordulások teljes száma',
    labelnames=['from_model', 'to_model'],
    registry=registry
)

max_retries_exceeded_count = Counter(
    name='max_retries_exceeded_count',
    documentation='Maximális újrapróbálkozások túllépésének száma',
    registry=registry
)
```

**Fallback logika**:

```python
# Fájl: backend/observability/llm_instrumentation.py

async def instrumented_llm_call_with_fallback(
    primary_llm,
    fallback_llm,
    messages,
    primary_model: str,
    fallback_model: str,
    max_retries: int = 3
):
    """
    Instrumentált LLM hívás automatikus fallback-kel másodlagos modellre.
    
    Model fallback útvonalakat követ a model_fallback_count metrikán keresztül.
    """
    request_id = get_request_id()
    
    # Próbáld az elsődleges modellt először
    for attempt in range(max_retries):
        try:
            logger.info(
                f"Elsődleges modell próbálkozás [model={primary_model}, "
                f"kísérlet={attempt+1}/{max_retries}]"
            )
            response = await instrumented_llm_call(
                llm=primary_llm,
                messages=messages,
                model=primary_model
            )
            return response
            
        except Exception as e:
            logger.warning(
                f"Elsődleges modell hibázott [model={primary_model}, "
                f"kísérlet={attempt+1}/{max_retries}, hiba={type(e).__name__}]"
            )
            if attempt == max_retries - 1:
                # Túllépte az újrapróbálkozásokat, próbáld a fallback-et
                break
    
    # Fallback követése metrikával
    model_fallback_count.labels(
        from_model=primary_model,
        to_model=fallback_model
    ).inc()
    
    logger.info(
        f"Fallback másodlagos modellre [from={primary_model}, "
        f"to={fallback_model}, request_id={request_id}]"
    )
    
    # Próbáld a fallback modellt
    for attempt in range(max_retries):
        try:
            logger.info(
                f"Fallback modell próbálkozás [model={fallback_model}, "
                f"kísérlet={attempt+1}/{max_retries}]"
            )
            response = await instrumented_llm_call(
                llm=fallback_llm,
                messages=messages,
                model=fallback_model
            )
            return response
            
        except Exception as e:
            logger.error(
                f"Fallback modell is hibázott [model={fallback_model}, "
                f"kísérlet={attempt+1}/{max_retries}]"
            )
            if attempt == max_retries - 1:
                # Mindkét modell sikertelen
                max_retries_exceeded_count.inc()
                raise
```

**Használat az agent kódban**:

```python
# Fájl: backend/services/agent.py

from observability.llm_instrumentation import instrumented_llm_call_with_fallback

class AIAgent:
    def __init__(self):
        self.primary_llm = ChatOpenAI(model="gpt-4o")
        self.fallback_llm = ChatOpenAI(model="gpt-4o-mini")  # Olcsóbb fallback
    
    async def _agent_decide_node(self, state):
        messages = self._prepare_messages(state)
        
        # LLM hívás fallback támogatással
        response = await instrumented_llm_call_with_fallback(
            primary_llm=self.primary_llm,
            fallback_llm=self.fallback_llm,
            messages=messages,
            primary_model="gpt-4o",
            fallback_model="gpt-4o-mini",
            max_retries=3
        )
        
        return response
```

**Grafana lekérdezések fallback követéshez**:

```promql
# Fallback események száma
sum by (from_model, to_model) (model_fallback_count)

# Fallback arány
rate(model_fallback_count[5m])

# Max újrapróbálkozások túllépése
sum(max_retries_exceeded_count)

# Fallback % az összes híváshoz képest
(sum(model_fallback_count) / sum(llm_inference_count)) * 100
```

**Mit nyújt?**:
- ✅ Model megbízhatóság monitoring
- ✅ Fallback gyakoriság követés
- ✅ Költség optimalizálás (drága modellről olcsóbbra váltás)
- ✅ Rendszer rugalmasság növelés

---

## 📂 Fejlett Megfigyelhetőségi Fájlok Áttekintése

| Fájl | Funkció | Mit Követ |
|------|---------|-----------|
| `backend/observability/prompt_lineage.py` | Prompt követés | Prompt hash, verzió, evolúció |
| `backend/observability/state_tracker.py` | Állapot snapshots | LangGraph állapotok node-ok között |
| `backend/observability/llm_instrumentation.py` | LLM wrapper | Token, költség, fallback |
| `backend/observability/metrics.py` | Metrika definíciók | Összes Prometheus metrika |
| `backend/observability/correlation.py` | Kérés ID követés | Request ID propagáció |

---

## 📍 Metrikák Kód Szintű Lokációi

Ez a szakasz részletesen bemutatja, hogy az egyes metrika kategóriák pontosan hol rögzítődnek a kódbázisban.

### 1. 🤖 Modellhívás Metrikák

**Metrikák**: `llm_inference_count`, `llm_inference_latency_seconds`, `llm_inference_token_input_total`, `llm_inference_token_output_total`

#### Definíció Helye:
**Fájl**: `backend/observability/metrics.py`

```python
# Sorok: 232-257
llm_inference_count = Counter(
    name='llm_inference_count',
    documentation='Összes LLM inferencia hívás',
    labelnames=['model'],
    registry=registry
)

llm_inference_latency_seconds = Histogram(
    name='llm_inference_latency_seconds',
    documentation='LLM inferencia hívások késleltetése másodpercben',
    labelnames=['model'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    registry=registry
)

llm_inference_token_input_total = Counter(
    name='llm_inference_token_input_total',
    documentation='Összes bemeneti token LLM által feldolgozva',
    labelnames=['model'],
    registry=registry
)

llm_inference_token_output_total = Counter(
    name='llm_inference_token_output_total',
    documentation='Összes kimeneti token LLM által generálva',
    labelnames=['model'],
    registry=registry
)
```

#### Rögzítés Helye:
**Fájl**: `backend/observability/llm_instrumentation.py`

```python
# Funkció: instrumented_llm_call() - Sorok: 32-140
async def instrumented_llm_call(llm, messages, model: str):
    """LLM hívás automatikus metrika gyűjtéssel."""
    
    start_time = time.time()
    
    # LLM hívás
    response = await llm.ainvoke(messages)
    
    # Időtartam számítása
    duration = time.time() - start_time
    
    # Token használat kinyerése
    prompt_tokens = response.usage_metadata.get('input_tokens', 0)
    completion_tokens = response.usage_metadata.get('output_tokens', 0)
    
    # ✅ METRIKÁK RÖGZÍTÉSE ITT
    llm_inference_count.labels(model=model).inc()
    llm_inference_latency_seconds.labels(model=model).observe(duration)
    llm_inference_token_input_total.labels(model=model).inc(prompt_tokens)
    llm_inference_token_output_total.labels(model=model).inc(completion_tokens)
    
    return response
```

#### Használat az Agent Kódban:
**Fájlok**: 
- `backend/services/agent.py` (sorok: 506-513, 906-913)
- `backend/advanced_agents/routing/router.py`
- `backend/advanced_agents/planning/planner.py`

```python
# backend/services/agent.py - agent_decide node
response = await instrumented_llm_call(
    llm=self.llm,
    messages=messages,
    model="gpt-4o-mini",
    agent_execution_id=state.get("agent_execution_id")
)
# ↑ Ez automatikusan rögzíti az összes LLM metrikát
```

---

### 2. 🔄 Agent Workflow Metrikák

**Metrikák**: `agent_execution_count`, `agent_execution_latency_seconds`, `node_execution_latency_seconds`, `tool_invocation_count`

#### Definíció Helye:
**Fájl**: `backend/observability/metrics.py`

```python
# Sorok: 265-295
agent_execution_count = Counter(
    name='agent_execution_count',
    documentation='Agent végrehajtások teljes száma',
    registry=registry
)

agent_execution_latency_seconds = Histogram(
    name='agent_execution_latency_seconds',
    documentation='Agent végrehajtás késleltetése másodpercben',
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0],
    registry=registry
)

node_execution_latency_seconds = Histogram(
    name='node_execution_latency_seconds',
    documentation='Egyedi node végrehajtás késleltetése másodpercben',
    labelnames=['node'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    registry=registry
)

tool_invocation_count = Counter(
    name='tool_invocation_count',
    documentation='Eszköz hívások teljes száma',
    labelnames=['tool'],
    registry=registry
)
```

#### Rögzítés Helye - Agent Execution Count:
**Fájl**: `backend/advanced_agents/routing/router.py`

```python
# Sorok: 44, 141
from observability.metrics import record_node_duration, agent_execution_count

async def route(self, state: AdvancedAgentState):
    with record_node_duration("router"):
        # Track agent execution count első router hívásnál
        iteration_count = state.get("iteration_count", 0)
        if iteration_count == 0:
            # ✅ AGENT EXECUTION METRIKA RÖGZÍTÉSE ITT
            agent_execution_count.inc()
```

#### Rögzítés Helye - Node Execution:
**Fájl**: `backend/observability/metrics.py`

```python
# Context manager: record_node_duration() - Sorok: 657-686
@contextmanager
def record_node_duration(node_name: str):
    """Node végrehajtási idő rögzítése."""
    start_time = time.time()
    
    try:
        yield
    finally:
        duration = time.time() - start_time
        
        # ✅ NODE METRIKÁK RÖGZÍTÉSE ITT
        agent_node_executions_total.labels(
            node=node_name,
            environment=get_environment()
        ).inc()
        
        node_execution_latency_seconds.labels(node=node_name).observe(duration)
```

**Használat minden node-ban**:
```python
# backend/services/agent.py - minden node wrapper-rel
async def _agent_decide_node(self, state):
    with record_node_duration("agent_decide"):  # ✅ Node metrikák itt
        # Node logika...
        pass

async def _tool_execution_node(self, state):
    with record_node_duration("tool_execution"):  # ✅ Node metrikák itt
        # Node logika...
        pass
```

#### Rögzítés Helye - Tool Invocation:
**Fájl**: `backend/observability/metrics.py`

```python
# Context manager: record_tool_call() - Sorok: 695-732
@contextmanager
def record_tool_call(tool_name: str):
    """Eszköz hívás metrikák rögzítése."""
    start_time = time.time()
    
    try:
        yield
        # ✅ TOOL METRIKÁK RÖGZÍTÉSE ITT (sikeres)
        tool_invocation_count.labels(tool=tool_name).inc()
    except Exception as e:
        # ✅ TOOL METRIKÁK RÖGZÍTÉSE ITT (hiba)
        tool_invocation_count.labels(tool=tool_name).inc()
        raise
    finally:
        duration = time.time() - start_time
        agent_tool_duration_seconds.labels(tool=tool_name).observe(duration)
```

**Használat az eszköz kódban**:
**Fájl**: `backend/services/tools.py`

```python
# Sorok: 15, 46, 97
from observability.metrics import record_tool_call

class WeatherTool:
    async def execute(self, city: str):
        with record_tool_call("weather"):  # ✅ Eszköz metrikák itt
            result = await self.client.get_forecast(city=city)
            return result

class GeocodeTool:
    async def execute(self, address: str):
        with record_tool_call("geocode"):  # ✅ Eszköz metrikák itt
            result = await self.client.geocode(address=address)
            return result
```

---

### 3. ⚠️ Hiba és Fallback Metrikák

**Metrikák**: `agent_errors_total`, `model_fallback_count`, `max_retries_exceeded_count`

#### Definíció Helye:
**Fájl**: `backend/observability/metrics.py`

```python
# Sorok: 166-175
agent_errors_total = Counter(
    name='agent_errors_total',
    documentation='Agent végrehajtás hibák teljes száma',
    labelnames=['error_type', 'node', 'environment'],
    registry=registry
)

# Sorok: 300-309
model_fallback_count = Counter(
    name='model_fallback_count',
    documentation='Model fallback előfordulások teljes száma',
    labelnames=['from_model', 'to_model'],
    registry=registry
)

max_retries_exceeded_count = Counter(
    name='max_retries_exceeded_count',
    documentation='Maximális újrapróbálkozások túllépésének száma',
    registry=registry
)
```

#### Rögzítés Helye - Hiba Metrikák:
**Fájl**: `backend/observability/metrics.py`

```python
# Funkció: record_error() - Sorok: 742-768
def record_error(error_type: str, node: str = "unknown"):
    """
    Hiba előfordulás rögzítése.
    
    Hiba típusok:
        - llm_error: LLM API hibák, rate limit, stb.
        - tool_error: Külső eszköz/API hibák
        - validation_error: Bemenet validációs hibák
        - rag_error: RAG lekérési hibák
        - unknown: Nem osztályozott hibák
    """
    # ✅ HIBA METRIKA RÖGZÍTÉSE ITT
    agent_errors_total.labels(
        error_type=error_type,
        node=node,
        environment=get_environment()
    ).inc()
```

**Használat az agent kódban**:
**Fájl**: `backend/services/agent.py`

```python
# Sorok: 20, 512, 912
from observability.metrics import record_node_duration, record_error

async def _agent_decide_node(self, state):
    try:
        response = await instrumented_llm_call(...)
    except Exception as e:
        logger.error(f"LLM hívás sikertelen: {e}")
        # ✅ HIBA METRIKA RÖGZÍTÉSE ITT
        record_error(error_type="llm_error", node="agent_decide")
        raise
```

**Fájl**: `backend/observability/llm_instrumentation.py`

```python
# Sorok: 22, 134, 199
from observability.metrics import record_error

async def instrumented_llm_call(llm, messages, model):
    try:
        response = await llm.ainvoke(messages)
    except Exception as e:
        # ✅ HIBA METRIKA RÖGZÍTÉSE ITT
        record_error(error_type="llm_error", node="llm_call")
        raise
```

#### Rögzítés Helye - Fallback Metrikák:
**Fájl**: `backend/observability/llm_instrumentation.py`

```python
# Funkció: instrumented_llm_call_with_fallback() - Sorok: 250-351
async def instrumented_llm_call_with_fallback(
    primary_llm, fallback_llm, messages,
    primary_model: str, fallback_model: str, max_retries: int = 3
):
    # Elsődleges modell próbálkozások
    for attempt in range(max_retries):
        try:
            return await instrumented_llm_call(primary_llm, messages, primary_model)
        except Exception as e:
            if attempt == max_retries - 1:
                break
    
    # ✅ FALLBACK METRIKA RÖGZÍTÉSE ITT
    model_fallback_count.labels(
        from_model=primary_model,
        to_model=fallback_model
    ).inc()
    
    # Fallback modell próbálkozások
    for attempt in range(max_retries):
        try:
            return await instrumented_llm_call(fallback_llm, messages, fallback_model)
        except Exception as e:
            if attempt == max_retries - 1:
                # ✅ MAX RETRIES METRIKA RÖGZÍTÉSE ITT
                max_retries_exceeded_count.inc()
                raise
```

---

### 4. 💰 Költség Metrikák

**Metrikák**: `llm_cost_total_usd`, `agent_llm_cost_usd_total`

#### Definíció Helye:
**Fájl**: `backend/observability/metrics.py`

```python
# Sorok: 256-262
llm_cost_total_usd = Counter(
    name='llm_cost_total_usd',
    documentation='Teljes költség USD-ben LLM inferenciára',
    labelnames=['model'],
    registry=registry
)

# Sorok: 93-101 (részletes változat)
agent_llm_cost_usd_total = Counter(
    name='agent_llm_cost_usd_total',
    documentation='Becsült LLM költségek USD-ben',
    labelnames=['model', 'tenant', 'environment'],
    registry=registry
)
```

#### Költség Számítás Helye:
**Fájl**: `backend/observability/metrics.py`

```python
# Funkció: _estimate_llm_cost() - Sorok: 576-603
def _estimate_llm_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    LLM költség becslése USD-ben token használat alapján.
    
    Árképzési táblázat (USD per 1K token) - 2026. Jan:
    """
    PRICING = {
        "gpt-4-turbo-preview": (0.01, 0.03),  # bemenet, kimenet
        "gpt-4": (0.03, 0.06),
        "gpt-4.1": (0.03, 0.06),
        "gpt-3.5-turbo": (0.0015, 0.002),
        "gpt-4o": (0.005, 0.015),
        "gpt-4o-mini": (0.00015, 0.0006),  # $0.15/$0.60 per 1M token
    }
    
    input_price, output_price = PRICING.get(model, PRICING["gpt-4"])
    
    # ✅ KÖLTSÉG SZÁMÍTÁSA ITT
    cost = (prompt_tokens / 1000.0 * input_price) + \
           (completion_tokens / 1000.0 * output_price)
    
    return cost
```

#### Rögzítés Helye:
**Fájl**: `backend/observability/metrics.py`

```python
# Funkció: record_llm_usage() - Sorok: 500-574
def record_llm_usage(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    duration_seconds: float
):
    """LLM használat metrikák rögzítése tokenekkel és becsült költséggel."""
    
    # Token metrikák rögzítése
    agent_llm_tokens_total.labels(model=model, direction="prompt").inc(prompt_tokens)
    agent_llm_tokens_total.labels(model=model, direction="completion").inc(completion_tokens)
    
    # Költség számítása
    cost_usd = _estimate_llm_cost(model, prompt_tokens, completion_tokens)
    
    # ✅ KÖLTSÉG METRIKÁK RÖGZÍTÉSE ITT
    agent_llm_cost_usd_total.labels(model=model).inc(cost_usd)
    llm_cost_total_usd.labels(model=model).inc(cost_usd)
```

**Használat az LLM wrapper-ben**:
**Fájl**: `backend/observability/llm_instrumentation.py`

```python
# Sorok: 95-120
async def instrumented_llm_call(llm, messages, model):
    start_time = time.time()
    response = await llm.ainvoke(messages)
    duration = time.time() - start_time
    
    # Token használat kinyerése
    prompt_tokens = response.usage_metadata.get('input_tokens', 0)
    completion_tokens = response.usage_metadata.get('output_tokens', 0)
    
    # ✅ KÖLTSÉG METRIKÁK RÖGZÍTÉSE ITT (record_llm_usage-en keresztül)
    record_llm_usage(
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        duration_seconds=duration
    )
```

---

### 5. 🔍 RAG (Retrieval-Augmented Generation) Metrikák

**Metrikák**: `rag_chunk_retrieval_count`, `rag_retrieved_chunk_relevance_score_avg`, `vector_db_query_latency_seconds`, `embedding_generation_count`

#### Definíció Helye:
**Fájl**: `backend/observability/metrics.py`

```python
# Sorok: 177-215
agent_rag_retrievals_total = Counter(
    name='agent_rag_retrievals_total',
    documentation='RAG lekérések teljes száma',
    labelnames=['status', 'environment'],
    registry=registry
)

agent_rag_chunks_retrieved = Histogram(
    name='agent_rag_chunks_retrieved',
    documentation='Lekért chunk-ok száma RAG lekérdezésenként',
    labelnames=['environment'],
    buckets=[0, 1, 2, 5, 10, 20, 50],
    registry=registry
)

agent_rag_duration_seconds = Histogram(
    name='agent_rag_duration_seconds',
    documentation='RAG lekérési késleltetés másodpercben',
    labelnames=['environment'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0],
    registry=registry
)

# Sorok: 314-335 (spec-kompatibilis változatok)
rag_chunk_retrieval_count = Counter(
    name='rag_chunk_retrieval_count',
    documentation='RAG chunk lekérések teljes száma',
    registry=registry
)

rag_retrieved_chunk_relevance_score_avg = Gauge(
    name='rag_retrieved_chunk_relevance_score_avg',
    documentation='Lekért chunk-ok átlagos relevancia pontszáma',
    registry=registry
)

vector_db_query_latency_seconds = Histogram(
    name='vector_db_query_latency_seconds',
    documentation='Vektor adatbázis lekérdezések késleltetése másodpercben',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry
)

embedding_generation_count = Counter(
    name='embedding_generation_count',
    documentation='Embedding generálások teljes száma',
    registry=registry
)
```

#### Rögzítés Helye:
**Fájl**: `backend/observability/metrics.py`

```python
# Context manager: record_rag_retrieval() - Sorok: 772-849
@contextmanager
def record_rag_retrieval(num_chunks: int = 0, relevance_scores: Optional[List[float]] = None):
    """
    RAG lekérési metrikák rögzítése.
    
    Használat:
        with record_rag_retrieval(num_chunks=5, relevance_scores=[0.9, 0.85, 0.8]):
            chunks = await vector_db.search(query)
    """
    start_time = time.time()
    status = "success"
    
    try:
        yield
    except Exception as e:
        status = "error"
        raise
    finally:
        duration = time.time() - start_time
        
        # ✅ RAG METRIKÁK RÖGZÍTÉSE ITT
        agent_rag_retrievals_total.labels(
            status=status,
            environment=get_environment()
        ).inc()
        
        rag_chunk_retrieval_count.inc()
        
        agent_rag_chunks_retrieved.labels(
            environment=get_environment()
        ).observe(num_chunks)
        
        agent_rag_duration_seconds.labels(
            environment=get_environment()
        ).observe(duration)
        
        vector_db_query_latency_seconds.observe(duration)
        
        # Relevancia pontszám átlag
        if relevance_scores:
            avg_score = sum(relevance_scores) / len(relevance_scores)
            rag_retrieved_chunk_relevance_score_avg.set(avg_score)
```

**Potenciális használat RAG szolgáltatásban**:
```python
# Példa: backend/services/rag_service.py (ha létezik)
from observability.metrics import record_rag_retrieval, embedding_generation_count

class RAGService:
    async def retrieve_chunks(self, query: str, top_k: int = 5):
        # Embedding generálás
        embedding_generation_count.inc()
        query_embedding = await self.embedding_model.encode(query)
        
        # Vektor DB lekérdezés metrika rögzítéssel
        with record_rag_retrieval():
            results = await self.vector_db.search(
                query_embedding,
                top_k=top_k
            )
            
            # Relevancia pontszámok kinyerése
            relevance_scores = [r['score'] for r in results]
            
        # Metrikák frissítése relevancia pontokkal
        with record_rag_retrieval(
            num_chunks=len(results),
            relevance_scores=relevance_scores
        ):
            pass  # Már lekértük, csak rögzítjük a metrikákat
        
        return results
```

---

## 📊 Metrika Kategóriák Összefoglalása

| Kategória | Fő Definíció | Fő Rögzítés | Használat |
|-----------|--------------|-------------|-----------|
| **Modellhívás** | `metrics.py` (232-257) | `llm_instrumentation.py` (95-120) | `agent.py`, `router.py`, `planner.py` |
| **Agent Workflow** | `metrics.py` (265-295) | `metrics.py` (657-732), `router.py` (141) | Minden agent node |
| **Hiba/Fallback** | `metrics.py` (166-175, 300-309) | `metrics.py` (742-768), `llm_instrumentation.py` (250-351) | `agent.py`, hibakezelő blokkok |
| **Költség** | `metrics.py` (256-262, 93-101) | `metrics.py` (500-603), `llm_instrumentation.py` (110-115) | `llm_instrumentation.py` |
| **RAG** | `metrics.py` (177-215, 314-335) | `metrics.py` (772-849) | RAG szolgáltatások |

---

## �📚 Összefoglalás

### Python → Prometheus → Grafana Folyamat

1. **Python Kód**: Használd a `prometheus_client`-et metrikák definiálásához és rögzítéséhez
2. **Végpont Kiszolgálása**: FastAPI szolgáltatja a metrikákat a `/metrics` címen
3. **Prometheus Gyűjtés**: 15 másodpercenként a Prometheus lekéri és tárolja a metrikákat
4. **Grafana Lekérdezés**: Dashboardok lekérdezik a Prometheus-t PromQL-lel
5. **Vizualizáció**: A felhasználók valós idejű diagramokat és statisztikákat látnak

### Kulcsfontosságú Metrikák ebben a Projektben

| Metrika | Típus | Cél | LangGraph Integráció |
|---------|-------|-----|----------------------|
| `llm_inference_count` | Counter | LLM hívások számolása | `instrumented_llm_call()` wrapperben rögzítve |
| `llm_inference_latency_seconds` | Histogram | LLM válaszidő mérése | Időzítéssel rögzítve a wrapperben |
| `tool_invocation_count` | Counter | Eszköz hívások számolása | `record_tool_call()` context managerben rögzítve |
| `node_execution_latency_seconds` | Histogram | Node végrehajtási idő mérése | `record_node_duration()` minden LangGraph node körül |
| `agent_execution_count` | Counter | Agent futások számolása | agent.run() hívásonként egyszer rögzítve |
| `llm_cost_total_usd` | Counter | Kumulatív költség követése | Token használatból számítva az LLM wrapperben |

### Fontos Fájlok

| Fájl | Cél |
|------|-----|
| `backend/observability/metrics.py` | Metrika definíciók |
| `backend/observability/llm_instrumentation.py` | LLM hívás wrapper metrikákkal |
| `backend/services/agent.py` | LangGraph node-ok `record_node_duration()`-nel |
| `backend/services/tools.py` | Eszköz wrapperek `record_tool_call()`-lal |
| `backend/main.py` | FastAPI `/metrics` végpont beállítás |
| `observability/prometheus.yml` | Prometheus gyűjtési konfiguráció |
| `observability/grafana/dashboards/*.json` | Előre elkészített Grafana dashboardok |

---

**Útmutató Vége**

További információkért:
- [DOCKER_ARCHITECTURE.md](DOCKER_ARCHITECTURE.md) - Konténer beállítás
- [MONITORING_TEST_PROMPTS.md](MONITORING_TEST_PROMPTS.md) - Teszt promptok metrikák generálásához
- [docs/09_MONITORING_PROMPT.md](docs/09_MONITORING_PROMPT.md) - Eredeti monitoring specifikáció
