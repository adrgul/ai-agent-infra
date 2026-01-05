# Agent Loop - Magyar Dokumentáció

Ez a dokumentum részletesen bemutatja, hogy hol és hogyan működik az agent loop ebben az AI Agent alkalmazásban.

---

## Tartalomjegyzék
1. [Mi az Agent Loop?](#mi-az-agent-loop)
2. [Loop Helye a Kódban](#loop-helye-a-kódban)
3. [Loop Működése](#loop-működése)
4. [Loop Megállítása](#loop-megállítása)
5. [Példa Futás](#példa-futás)
6. [Debugging](#debugging)

---

## Mi az Agent Loop?

Az **Agent Loop** egy olyan mechanizmus, amely lehetővé teszi, hogy az AI agent többször is visszatérjen a döntéshozatali folyamathoz, mielőtt végleges választ adna.

**Miért szükséges?**
- ✅ **Többlépéses feladatok:** User kérhet több dolgot egyszerre ("időjárás + árfolyam")
- ✅ **Sorozatos tool hívások:** Egy feladat több tool kombinációját igényelheti
- ✅ **Függő műveletek:** Egy tool eredménye lehet input egy másik tool-nak

**Példa loop nélkül vs. loop-pal:**

**Loop NÉLKÜL:**
```
User: "Mi az időjárás Budapesten és mennyibe kerül 500 EUR?"
Agent: "Sajnálom, csak egy dolgot tudok egyszerre csinálni."
```

**Loop-PAL:**
```
User: "Mi az időjárás Budapesten és mennyibe kerül 500 EUR?"

Iteration 1: weather(city=Budapest) → "15°C, napos"
Iteration 2: fx_rates(base=EUR, target=HUF) → "395.5"
Final: "Budapest időjárása 15°C, napos. 500 EUR = 197,750 HUF."
```

---

## Loop Helye a Kódban

### 1. **Loop Definíció: backend/services/agent.py, lines 115-120**

```python
# Add edges from tools back to agent_decide (for multi-step reasoning)
for tool_name in self.tools.keys():
    workflow.add_edge(f"tool_{tool_name}", "agent_decide")
```

**Ez a kód:**
- Végigmegy minden tool-on (`weather`, `geocode`, `fx_rates`, `crypto_price`, `create_file`, `search_history`, `ip_geolocation`)
- Minden tool-hoz hozzáad egy **edge-et** (élt), amely visszavezet az `agent_decide` node-ba
- Ez teszi lehetővé a loop-ot: `tool → agent_decide → tool → agent_decide → ...`

**LangGraph szintaxis:**
```python
workflow.add_edge(SOURCE_NODE, TARGET_NODE)
```
- `SOURCE_NODE`: `tool_weather`, `tool_geocode`, stb.
- `TARGET_NODE`: `agent_decide` (mindig ugyanaz)

**Eredmény:** 7 darab edge a loop-hoz (7 tool × 1 edge)

---

### 2. **Loop Entry Point: backend/services/agent.py, line 103**

```python
# Set entry point
workflow.set_entry_point("agent_decide")
```

**Ez a kód:**
- Beállítja, hogy a workflow MINDIG az `agent_decide` node-dal induljon
- Az első iteráció is az `agent_decide`-ban kezdődik

---

### 3. **Loop Exit Condition: backend/services/agent.py, lines 106-113**

```python
# Add conditional edges from agent_decide
workflow.add_conditional_edges(
    "agent_decide",
    self._route_decision,
    {
        "final_answer": "agent_finalize",
        **{f"tool_{name}": f"tool_{name}" for name in self.tools.keys()}
    }
)
```

**Ez a kód:**
- Az `agent_decide` után eldönti, hogy folytatjuk-e a loop-ot vagy kilépünk
- `_route_decision()` függvény dönti el a következő lépést:
  - Ha `"final_answer"` → kilépés a loop-ból, ugrás `agent_finalize`-ra
  - Ha `"tool_weather"` → folytatás a loop-ban, ugrás `tool_weather`-re

---

### 4. **Loop Iteration Counter: backend/services/agent.py, lines 216-218**

```python
# Store decision for tool execution
if decision.get("action") == "call_tool":
    state["tool_decision"] = decision
    # Increment iteration count when calling a tool
    state["iteration_count"] = state.get("iteration_count", 0) + 1
```

**Ez a kód:**
- Minden tool hívás előtt növeli az `iteration_count` értékét
- Ez a számláló követi, hogy hányszor futott le a loop
- Használva van a loop megállítási mechanizmusban

---

### 5. **Loop Termination Logic: backend/services/agent.py, lines 231-235**

```python
def _route_decision(self, state: AgentState) -> str:
    """Route to next node based on agent decision."""
    # Check iteration limit to prevent infinite loops
    if state.get("iteration_count", 0) >= MAX_ITERATIONS:
        logger.warning(f"Max iterations ({MAX_ITERATIONS}) reached, forcing finalize")
        return "final_answer"
```

**Ez a kód:**
- Ellenőrzi, hogy elértük-e a maximális iterációs limitet (`MAX_ITERATIONS = 10`)
- Ha igen, KÉNYSZERÍTETTEN kilép a loop-ból, függetlenül az LLM döntésétől
- Visszatér `"final_answer"`-rel → ugrás `agent_finalize`-ra → END

---

## Loop Működése

### Teljes Loop Ciklus

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  1. agent_decide (LLM döntés)                   │
│     ↓                                            │
│     Döntés: "call_tool" VAGY "final_answer"     │
│     ↓                                            │
│  ┌──┴────────────────┐                          │
│  │                   │                          │
│  ▼                   ▼                          │
│  tool_*           agent_finalize → END          │
│  (execute)           (kilépés)                  │
│  ↓                                               │
│  └───────────────────┘                          │
│  (vissza agent_decide-ra - LOOP)                │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Lépésről Lépésre

**Iteration 1:**
```
1. agent_decide
   ├─ Input: state["messages"] = [HumanMessage("időjárás + árfolyam")]
   ├─ LLM döntés: {"action": "call_tool", "tool_name": "weather", "arguments": {"city": "Budapest"}}
   ├─ Update: state["iteration_count"] = 1
   └─ Route: "tool_weather"

2. tool_weather
   ├─ Execute: WeatherTool(city="Budapest")
   ├─ Result: {"temp": 15, "condition": "Sunny"}
   ├─ Update: state["tools_called"].append(ToolCall(...))
   └─ Route: "agent_decide" (AUTOMATIC - loop edge)
```

**Iteration 2:**
```
3. agent_decide
   ├─ Input: state["tools_called"] = [ToolCall(tool_name="weather", ...)]
   ├─ LLM döntés: {"action": "call_tool", "tool_name": "fx_rates", "arguments": {"base": "EUR", "target": "HUF"}}
   ├─ Update: state["iteration_count"] = 2
   └─ Route: "tool_fx_rates"

4. tool_fx_rates
   ├─ Execute: FXRatesTool(base="EUR", target="HUF")
   ├─ Result: {"rate": 395.5}
   ├─ Update: state["tools_called"].append(ToolCall(...))
   └─ Route: "agent_decide" (AUTOMATIC - loop edge)
```

**Iteration 3 (Finalize):**
```
5. agent_decide
   ├─ Input: state["tools_called"] = [ToolCall(weather), ToolCall(fx_rates)]
   ├─ LLM döntés: {"action": "final_answer", "reasoning": "all tasks completed"}
   └─ Route: "final_answer" (KILÉPÉS a loop-ból)

6. agent_finalize
   ├─ Generate response: "Budapest időjárása 15°C, napos. 500 EUR = 197,750 HUF."
   ├─ Update: state["messages"].append(AIMessage(...))
   └─ Route: END (workflow vége)
```

---

## Loop Megállítása

A loop **4 módon** állhat meg:

### 1. **LLM Döntés: final_answer**
```python
# agent_decide node
decision = {"action": "final_answer", "reasoning": "all tasks completed"}
state["next_action"] = "final_answer"

# _route_decision()
if action == "final_answer":
    return "final_answer"  # → agent_finalize
```

**Mikor történik:**
- Minden feladat teljesítve
- User kérése lehetetlen (pl. historical weather)
- LLM úgy dönt, hogy elég információ gyűlt össze

---

### 2. **MAX_ITERATIONS Elérése**
```python
MAX_ITERATIONS = 10  # line 27

def _route_decision(self, state: AgentState) -> str:
    if state.get("iteration_count", 0) >= MAX_ITERATIONS:
        logger.warning(f"Max iterations ({MAX_ITERATIONS}) reached, forcing finalize")
        return "final_answer"
```

**Mikor történik:**
- 10 tool hívás után automatikusan
- Végtelen loop védelem
- LLM döntésétől független

**Log üzenet:**
```
WARNING - Max iterations (10) reached, forcing finalize
```

---

### 3. **recursion_limit Elérése**
```python
# run() method, line 410
final_state = await self.workflow.ainvoke(
    initial_state,
    {"recursion_limit": 50}
)
```

**Mikor történik:**
- 50 node hívás után (agent_decide + tools + finalize összesen)
- LangGraph szintű védelem
- Exception: `RecursionError`

**Különbség MAX_ITERATIONS-tól:**
| | MAX_ITERATIONS | recursion_limit |
|---|---|---|
| **Szint** | Alkalmazás logika | LangGraph framework |
| **Számít** | Tool hívások | Összes node hívás |
| **Limit** | 10 | 50 |
| **Kezelés** | Graceful (final_answer) | Exception |

---

### 4. **Tool Deduplication**
```python
# Decision prompt-ban
tools_called_info = [f"{tc.tool_name}({tc.arguments})" for tc in state["tools_called"]]

# Prompt rule
"""
CRITICAL RULES:
1. NEVER call the same tool with the same arguments twice
"""
```

**Mikor történik:**
- LLM észreveszi, hogy egy tool már hívva volt ugyanazzal az argumentummal
- Dönt `final_answer` mellett, hogy ne ismételje
- Soft limit (nem kikényszerített, LLM döntés)

---

## Példa Futás

### User Input
```
"What's the weather in Budapest, and how much is 500 EUR in HUF?"
```

### Loop Trace

**ITERATION 1:**
```
[agent_decide]
  └─ LLM döntés: call_tool → weather(city=Budapest)
  └─ iteration_count: 0 → 1
  └─ Route: tool_weather

[tool_weather]
  └─ API hívás: OpenMeteo Budapest
  └─ Result: 15°C, Sunny
  └─ tools_called: [weather(city=Budapest)]
  └─ Route: agent_decide (LOOP)
```

**ITERATION 2:**
```
[agent_decide]
  └─ tools_called látható: [weather(city=Budapest)]
  └─ LLM döntés: call_tool → fx_rates(base=EUR, target=HUF)
  └─ iteration_count: 1 → 2
  └─ Route: tool_fx_rates

[tool_fx_rates]
  └─ API hívás: Frankfurter EUR→HUF
  └─ Result: 395.5
  └─ tools_called: [weather(...), fx_rates(...)]
  └─ Route: agent_decide (LOOP)
```

**ITERATION 3:**
```
[agent_decide]
  └─ tools_called látható: [weather(...), fx_rates(...)]
  └─ LLM döntés: final_answer (all tasks done)
  └─ Route: final_answer (KILÉPÉS)

[agent_finalize]
  └─ Generate response: "Budapest: 15°C, sunny. 500 EUR = 197,750 HUF."
  └─ Route: END
```

**Összesen:**
- **Loop futások:** 2× (iteration 1, 2)
- **Tool hívások:** 2× (weather, fx_rates)
- **Node hívások:** 6× (3× agent_decide, 2× tool, 1× agent_finalize)

---

## Debugging

### Hogyan követhesd a loop-ot?

**1. Backend Logs:**
```bash
docker-compose logs backend --tail=100 | grep -E "(Agent decision|iteration_count|Tool executed|Route)"
```

**Kimenet példa:**
```
INFO - Agent decision node executing
INFO - Agent decision: {'action': 'call_tool', 'tool_name': 'weather', ...}
INFO - Executing tool: weather
INFO - Tool weather completed: True
INFO - Agent decision node executing
INFO - Agent decision: {'action': 'final_answer', ...}
INFO - Agent finalize node executing
```

---

**2. Iteration Count Tracking:**
```python
# agent.py-ban adj hozzá log-ot
logger.info(f"Current iteration: {state.get('iteration_count', 0)}/{MAX_ITERATIONS}")
```

---

**3. Tools Called History:**
```python
# Nézd meg state["tools_called"]
for tc in state["tools_called"]:
    print(f"{tc.tool_name}({tc.arguments}) → {tc.result}")
```

**Kimenet példa:**
```
weather(city=Budapest) → {'temp': 15, 'condition': 'Sunny'}
fx_rates(base=EUR, target=HUF) → {'rate': 395.5}
```

---

**4. Frontend Debug Panel:**
A frontend "Tools Used" paneljában látható az összes végrehajtott tool:
```
✓ weather
✓ fx_rates
```

---

## Összefoglalás

### Loop Lokációk a Kódban

| Funkció | Fájl | Sorok | Kód |
|---------|------|-------|-----|
| **Loop edge** | `agent.py` | 115-120 | `workflow.add_edge(f"tool_{tool_name}", "agent_decide")` |
| **Entry point** | `agent.py` | 103 | `workflow.set_entry_point("agent_decide")` |
| **Conditional exit** | `agent.py` | 106-113 | `workflow.add_conditional_edges(...)` |
| **Iteration counter** | `agent.py` | 216-218 | `state["iteration_count"] += 1` |
| **MAX_ITERATIONS check** | `agent.py` | 231-235 | `if iteration_count >= MAX_ITERATIONS` |
| **recursion_limit** | `agent.py` | 410 | `workflow.ainvoke(..., recursion_limit=50)` |

### Loop Folyamat Összefoglalva

```
START
  ↓
agent_decide (döntés)
  ↓
  ├─ final_answer → agent_finalize → END (KILÉPÉS)
  └─ call_tool → tool_* → agent_decide (LOOP)
                    ↑___________↓
                    LOOP EDGE
```

### Loop Megállítási Feltételek

1. ✅ LLM dönt: `{"action": "final_answer"}`
2. ✅ `iteration_count >= 10` (MAX_ITERATIONS)
3. ✅ Total node calls >= 50 (recursion_limit)
4. ✅ LLM felismeri: ugyanaz a tool már hívva volt (deduplication)

### Kulcsfontosságú Design Döntések

- **Automatikus loop:** Tool után MINDIG vissza az agent_decide-ra
- **LLM kontroll:** Az agent dönti el, mikor lép ki
- **Safety nets:** MAX_ITERATIONS és recursion_limit védenek a végtelen loop ellen
- **State persistence:** Minden loop után a state megőrzi az eddigi tool hívásokat

### Kapcsolódó Dokumentumok

- **LangGraph használat:** `docs/LANGGRAPH_USAGE_HU.md`
- **Node típusok:** `docs/LANGGRAPH_NODES_HU.md`
- **Prompt stratégia:** `docs/PROMPTS.md`
- **Architektúra:** `docs/ARCHITECTURE.md`
