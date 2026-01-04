# LangGraph Használat - Magyar Dokumentáció

Ez a dokumentum bemutatja, hogyan épül fel és működik a LangGraph workflow ebben az AI Agent alkalmazásban.

---

## Tartalomjegyzék
1. [LangGraph Alapok](#langgraph-alapok)
2. [AgentState - Állapotkezelés](#agentstate---állapotkezelés)
3. [Graph Építése](#graph-építése)
4. [Node Típusok](#node-típusok)
5. [Routing Logika](#routing-logika)
6. [Workflow Végrehajtás](#workflow-végrehajtás)
7. [Biztonsági Mechanizmusok](#biztonsági-mechanizmusok)
8. [Példakód](#példakód)

---

## LangGraph Alapok

**Mi a LangGraph?**
A LangGraph egy Python könyvtár, amely lehetővé teszi komplex, többlépéses AI workflow-k építését irányított gráfok (directed graphs) segítségével.

**Miért LangGraph?**
- ✅ **Többlépéses reasoning:** Az agent többször is dönthet, mielőtt végleges választ ad
- ✅ **Állapotkezelés:** Minden node-ban hozzáférünk a teljes állapothoz (state)
- ✅ **Feltételes routing:** Döntési logika alapján irányíthatjuk a workflow-t
- ✅ **Ciklikus graph:** Node-ok között loop-olhatunk (tool → decide → tool → ...)
- ✅ **Type-safe:** TypedDict alapú állapotkezelés

**Fő komponensek:**
- **StateGraph:** A workflow gráf konténere
- **Node:** Egy feldolgozási lépés (függvény)
- **Edge:** Kapcsolat két node között
- **Conditional Edge:** Feltételes elágazás (routing függvény alapján)

---

## AgentState - Állapotkezelés

Az `AgentState` egy TypedDict, amely a teljes workflow állapotát tárolja. Minden node megkapja ezt az állapotot bemenetként, és módosított állapotot ad vissza.

**Definíció:**
```python
from typing_extensions import TypedDict
from typing import Sequence, List, Dict, Any
from langchain_core.messages import BaseMessage
from domain.models import Memory, ToolCall

class AgentState(TypedDict, total=False):
    """LangGraph agent állapot objektuma."""
    messages: Sequence[BaseMessage]        # LangChain üzenetek (HumanMessage, AIMessage, SystemMessage)
    memory: Memory                         # Felhasználói memória (preferences, history, workflow)
    tools_called: List[ToolCall]           # Már végrehajtott tool hívások listája
    current_user_id: str                   # Aktuális felhasználó azonosítója
    next_action: str                       # Következő akció ("call_tool" vagy "final_answer")
    tool_decision: Dict[str, Any]          # LLM döntése a következő tool hívásról
    iteration_count: int                   # Iterációk száma (végtelen loop elleni védelem)
```

**Állapot mezők részletesen:**

| Mező | Típus | Leírás | Használat |
|------|-------|--------|-----------|
| `messages` | `Sequence[BaseMessage]` | LangChain üzenetek szekvenciája | Conversation history, LLM context |
| `memory` | `Memory` | Felhasználói memória objektum | Preferences (név, nyelv, város), chat history |
| `tools_called` | `List[ToolCall]` | Végrehajtott tool hívások | Deduplication, history tracking |
| `current_user_id` | `str` | User ID | File creation, profile updates |
| `next_action` | `str` | Következő lépés | Routing logika (`"call_tool"` vagy `"final_answer"`) |
| `tool_decision` | `Dict[str, Any]` | LLM döntés JSON-je | Tool name, arguments, reasoning |
| `iteration_count` | `int` | Loop számláló | MAX_ITERATIONS elérése esetén force finalize |

---

## Graph Építése

A workflow graph építése a `_build_graph()` metódusban történik.

**Építési lépések:**

### 1. StateGraph Inicializálás
```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(AgentState)
```

### 2. Node-ok Hozzáadása
```python
# Döntési node (LLM reasoning)
workflow.add_node("agent_decide", self._agent_decide_node)

# Véglegesítő node (final response generation)
workflow.add_node("agent_finalize", self._agent_finalize_node)

# Tool node-ok (minden tool külön node)
for tool_name in self.tools.keys():
    workflow.add_node(f"tool_{tool_name}", self._create_tool_node(tool_name))
```

**Eredmény:** 9 node összesen
- 1× `agent_decide`
- 7× `tool_*` (weather, geocode, ip_geolocation, fx_rates, crypto_price, create_file, search_history)
- 1× `agent_finalize`

### 3. Entry Point Beállítása
```python
workflow.set_entry_point("agent_decide")
```
**Jelentés:** A workflow MINDIG az `agent_decide` node-dal indul.

### 4. Conditional Edge - agent_decide → tools/finalize
```python
workflow.add_conditional_edges(
    "agent_decide",                    # Honnan
    self._route_decision,              # Routing függvény
    {
        "final_answer": "agent_finalize",  # Ha "final_answer" → finalize node
        **{f"tool_{name}": f"tool_{name}" for name in self.tools.keys()}  # Ha "tool_weather" → tool_weather node
    }
)
```

**Működés:**
1. `agent_decide` node lefut
2. `_route_decision()` függvény megkapja a state-et
3. Visszaad egy string-et (`"final_answer"` vagy `"tool_weather"`)
4. A graph az adott node-ra ugrál

### 5. Edge - tools → agent_decide (loop)
```python
for tool_name in self.tools.keys():
    workflow.add_edge(f"tool_{tool_name}", "agent_decide")
```

**Jelentés:** MINDEN tool node után visszamegyünk az `agent_decide` node-ba. Ez teszi lehetővé a többlépéses reasoning-et.

### 6. Edge - agent_finalize → END
```python
workflow.add_edge("agent_finalize", END)
```

**Jelentés:** A `agent_finalize` node után a workflow befejeződik.

### 7. Graph Compile
```python
return workflow.compile()
```

**Eredmény:** Futtatható workflow objektum.

---

## Node Típusok

### 1. **agent_decide** - Döntési Node

**Cél:** Az LLM elemzi a user kérését és eldönti, melyik tool-t hívja meg, vagy végleges választ ad.

**Bemenet:** `AgentState`
**Kimenet:** `AgentState` (módosított `next_action`, `tool_decision`, `iteration_count`)

**Folyamat:**
```python
async def _agent_decide_node(self, state: AgentState) -> AgentState:
    # 1. System prompt építése (preferences, history)
    system_prompt = self._build_system_prompt(state["memory"])
    
    # 2. User utolsó üzenetének kinyerése
    last_user_msg = # ... (HumanMessage keresése messages-ben)
    
    # 3. Recent history építése (utolsó 5 üzenet)
    recent_history = state["memory"].chat_history[-5:]
    
    # 4. Tools called lista építése (tool_name(arguments) formátum)
    tools_called_info = [f"{tc.tool_name}({tc.arguments})" for tc in state["tools_called"]]
    
    # 5. Decision prompt összeállítása
    decision_prompt = f"""
    Available tools: weather, geocode, fx_rates, ...
    User request: {last_user_msg}
    Tools already called: {tools_called_info}
    
    Respond ONLY with JSON:
    {{"action": "call_tool", "tool_name": "weather", "arguments": {{"city": "Budapest"}}, "reasoning": "..."}}
    """
    
    # 6. LLM hívás
    response = await self.llm.ainvoke([SystemMessage(system_prompt), HumanMessage(decision_prompt)])
    
    # 7. JSON parsing
    decision = json.loads(response.content)
    
    # 8. State update
    state["next_action"] = decision["action"]
    state["tool_decision"] = decision
    state["iteration_count"] += 1
    
    return state
```

**Példa döntés:**
```json
{
  "action": "call_tool",
  "tool_name": "weather",
  "arguments": {"city": "Budapest"},
  "reasoning": "get weather forecast for Budapest"
}
```

---

### 2. **tool_*** - Tool Végrehajtó Node-ok

**Cél:** Egy konkrét tool végrehajtása (weather API, geocode API, stb.)

**Bemenet:** `AgentState`
**Kimenet:** `AgentState` (módosított `messages`, `tools_called`)

**Folyamat:**
```python
def _create_tool_node(self, tool_name: str):
    """Factory függvény tool node létrehozására."""
    
    async def tool_node(state: AgentState) -> AgentState:
        # 1. Tool lekérése
        tool = self.tools[tool_name]
        
        # 2. Argumentumok kinyerése state-ből
        decision = state["tool_decision"]
        arguments = decision["arguments"]
        
        # 3. User ID hozzáadása (file creation tool-hoz)
        if tool_name == "create_file":
            arguments["user_id"] = state["current_user_id"]
        
        # 4. Tool végrehajtás
        result = await tool.execute(**arguments)
        
        # 5. ToolCall objektum létrehozása
        tool_call = ToolCall(
            tool_name=tool_name,
            arguments=arguments,
            result=result.get("data") if result.get("success") else None,
            error=result.get("error") if not result.get("success") else None
        )
        
        # 6. State update
        state["tools_called"].append(tool_call)
        state["messages"].append(SystemMessage(content=result["system_message"]))
        
        return state
    
    return tool_node
```

**Példa tool hívás eredmény:**
```python
{
    "success": True,
    "data": {"temperature": 15, "condition": "Sunny"},
    "system_message": "Weather: Budapest - 15°C, Sunny"
}
```

---

### 3. **agent_finalize** - Véglegesítő Node

**Cél:** Természetes nyelvű válasz generálása a user számára az összegyűjtött tool eredmények alapján.

**Bemenet:** `AgentState`
**Kimenet:** `AgentState` (módosított `messages` - AIMessage hozzáadva)

**Folyamat:**
```python
async def _agent_finalize_node(self, state: AgentState) -> AgentState:
    # 1. System prompt építése
    system_prompt = self._build_system_prompt(state["memory"])
    
    # 2. Conversation history összegyűjtése (utolsó 10 üzenet)
    conversation_history = "\n".join([
        f"{msg.__class__.__name__}: {msg.content}"
        for msg in state["messages"][-10:]
    ])
    
    # 3. Final prompt összeállítása
    final_prompt = f"""
    Generate a natural language response to the user.
    
    Conversation: {conversation_history}
    
    Important:
    - Respond in {state['memory'].preferences.get('language', 'hu')} language
    - Be helpful and conversational
    - Use information from tool results (SystemMessage-ek)
    """
    
    # 4. LLM hívás
    response = await self.llm.ainvoke([SystemMessage(system_prompt), HumanMessage(final_prompt)])
    
    # 5. AIMessage hozzáadása state-hez
    state["messages"].append(AIMessage(content=response.content))
    
    return state
```

**Példa végleges válasz:**
```
"Budapest időjárása jelenleg napos, 15°C. Holnap kissé hűvösebb lesz, 12°C körül várható."
```

---

## Routing Logika

A `_route_decision()` függvény dönti el, hogy az `agent_decide` node után melyik node-ra ugorjon a workflow.

**Kód:**
```python
def _route_decision(self, state: AgentState) -> str:
    """Route to next node based on agent decision."""
    
    # 1. Iteration limit ellenőrzése
    if state.get("iteration_count", 0) >= MAX_ITERATIONS:
        logger.warning(f"Max iterations ({MAX_ITERATIONS}) reached, forcing finalize")
        return "final_answer"
    
    # 2. Next action kiolvasása
    action = state.get("next_action", "final_answer")
    
    # 3. Ha tool hívás, routing tool node-ra
    if action == "call_tool" and "tool_decision" in state:
        tool_name = state["tool_decision"].get("tool_name")
        if tool_name in self.tools:
            return f"tool_{tool_name}"
    
    # 4. Alapértelmezett: final_answer
    return "final_answer"
```

**Lehetséges return értékek:**
- `"final_answer"` → `agent_finalize` node
- `"tool_weather"` → `tool_weather` node
- `"tool_geocode"` → `tool_geocode` node
- `"tool_fx_rates"` → `tool_fx_rates` node
- ... (stb. minden tool-ra)

**Döntési fa:**
```
1. iteration_count >= MAX_ITERATIONS?
   ├─ IGEN → "final_answer"
   └─ NEM → 2.

2. next_action == "call_tool" ÉS tool_decision létezik?
   ├─ IGEN → "tool_{tool_name}"
   └─ NEM → "final_answer"
```

---

## Workflow Végrehajtás

A workflow-t a `run()` metódus indítja el.

**Kód:**
```python
async def run(self, user_message: str, memory: Memory, user_id: str) -> Dict[str, Any]:
    # 1. Initial state létrehozása
    initial_state: AgentState = {
        "messages": [HumanMessage(content=user_message)],
        "memory": memory,
        "tools_called": [],
        "current_user_id": user_id,
        "next_action": "",
        "iteration_count": 0
    }
    
    # 2. Workflow végrehajtás
    final_state = await self.workflow.ainvoke(
        initial_state,
        {"recursion_limit": 50}  # Maximum 50 node hívás
    )
    
    # 3. Final answer kinyerése (utolsó AIMessage)
    final_answer = ""
    for msg in reversed(final_state["messages"]):
        if isinstance(msg, AIMessage):
            final_answer = msg.content
            break
    
    # 4. Eredmény visszaadása
    return {
        "final_answer": final_answer,
        "tools_called": final_state["tools_called"],
        "messages": final_state["messages"],
        "memory": final_state["memory"]
    }
```

**Végrehajtási folyamat példa:**

**User üzenet:** "Mi az időjárás Budapesten és mennyibe kerül 500 EUR HUF-ban?"

**Workflow futás:**
```
1. agent_decide
   ├─ Decision: {"action": "call_tool", "tool_name": "weather", "arguments": {"city": "Budapest"}}
   └─ Route: "tool_weather"

2. tool_weather
   ├─ Execute: WeatherTool(city="Budapest")
   ├─ Result: {"temp": 15, "condition": "Sunny"}
   ├─ Update state: tools_called += ToolCall(...)
   └─ Route: "agent_decide" (automatic edge)

3. agent_decide
   ├─ Decision: {"action": "call_tool", "tool_name": "fx_rates", "arguments": {"base": "EUR", "target": "HUF"}}
   └─ Route: "tool_fx_rates"

4. tool_fx_rates
   ├─ Execute: FXRatesTool(base="EUR", target="HUF")
   ├─ Result: {"rate": 395.5}
   ├─ Update state: tools_called += ToolCall(...)
   └─ Route: "agent_decide" (automatic edge)

5. agent_decide
   ├─ Decision: {"action": "final_answer", "reasoning": "all tasks completed"}
   └─ Route: "final_answer"

6. agent_finalize
   ├─ Generate response: "Budapest időjárása napos, 15°C. 500 EUR = 197,750 HUF."
   ├─ Update state: messages += AIMessage(...)
   └─ Route: END (automatic edge)

WORKFLOW VÉGE
```

---

## Biztonsági Mechanizmusok

### 1. **MAX_ITERATIONS Limit**
```python
MAX_ITERATIONS = 10
```

**Cél:** Végtelen loop megakadályozása

**Működés:**
- Minden tool hívás után `iteration_count` növekszik
- Ha `iteration_count >= 10`, a routing automatikusan `"final_answer"`-re vált
- Az LLM többé nem hívhat tool-okat

**Log üzenet:**
```
WARNING - Max iterations (10) reached, forcing finalize
```

### 2. **recursion_limit**
```python
final_state = await self.workflow.ainvoke(initial_state, {"recursion_limit": 50})
```

**Cél:** Graph végrehajtási mélység korlátozása

**Működés:**
- LangGraph maximum 50 node-t futtathat le
- Ha túllépjük, exception: `RecursionError`

**Különbség MAX_ITERATIONS-tól:**
- `MAX_ITERATIONS`: Tool hívások száma
- `recursion_limit`: Összes node hívás száma (agent_decide + tools + finalize)

### 3. **Tool Deduplication**
```python
tools_called_info = [f"{tc.tool_name}({tc.arguments})" for tc in state["tools_called"]]
```

**Cél:** Ugyanazon tool ugyanazon argumentumokkal való többszöri hívás megakadályozása

**Működés:**
- Decision prompt tartalmazza a már hívott tool-okat argumentumokkal
- LLM látja: `["weather(city=Budapest)", "fx_rates(base=EUR, target=HUF)"]`
- Prompt rule: "NEVER call the same tool with the same arguments twice"

### 4. **Tool Capability Checks**
```python
# Decision prompt-ban
"""
- weather: ONLY provides current + 2 day future forecast, NO historical data
"""
```

**Cél:** Lehetetlen kérések felismerése

**Működés:**
- Prompt explicit módon leírja, mit NEM tud egy tool
- LLM ha lehetetlent kér user (pl. múltbéli időjárás), `final_answer`-rel magyarázatot ad

---

## Példakód

### Teljes Graph Építés
```python
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict

class AgentState(TypedDict, total=False):
    messages: Sequence[BaseMessage]
    memory: Memory
    tools_called: List[ToolCall]
    current_user_id: str
    next_action: str
    tool_decision: Dict[str, Any]
    iteration_count: int

def _build_graph(self) -> StateGraph:
    """LangGraph workflow építése."""
    workflow = StateGraph(AgentState)
    
    # Node-ok hozzáadása
    workflow.add_node("agent_decide", self._agent_decide_node)
    workflow.add_node("agent_finalize", self._agent_finalize_node)
    
    for tool_name in ["weather", "geocode", "fx_rates", "crypto_price", "create_file"]:
        workflow.add_node(f"tool_{tool_name}", self._create_tool_node(tool_name))
    
    # Entry point
    workflow.set_entry_point("agent_decide")
    
    # Conditional edges: agent_decide → tools/finalize
    workflow.add_conditional_edges(
        "agent_decide",
        self._route_decision,
        {
            "final_answer": "agent_finalize",
            "tool_weather": "tool_weather",
            "tool_geocode": "tool_geocode",
            "tool_fx_rates": "tool_fx_rates",
            "tool_crypto_price": "tool_crypto_price",
            "tool_create_file": "tool_create_file"
        }
    )
    
    # Edges: tools → agent_decide (loop)
    for tool_name in ["weather", "geocode", "fx_rates", "crypto_price", "create_file"]:
        workflow.add_edge(f"tool_{tool_name}", "agent_decide")
    
    # Edge: agent_finalize → END
    workflow.add_edge("agent_finalize", END)
    
    # Compile
    return workflow.compile()
```

### Graph Vizualizáció (ASCII)
```
                    ┌──────────────┐
                    │ agent_decide │ ◄─────┐
                    └──────┬───────┘        │
                           │                │
              ┌────────────┴────────────┐   │
              │                         │   │
              ▼                         ▼   │
     ┌────────────────┐        ┌────────────────┐
     │  tool_weather  │        │  tool_geocode  │
     └────────┬───────┘        └────────┬───────┘
              │                         │
              └─────────────┬───────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │agent_finalize│
                    └──────┬───────┘
                           │
                           ▼
                         [END]
```

---

## Összefoglalás

### LangGraph használat lépései ebben az appban:

1. **AgentState definiálása** - TypedDict az állapotkezeléshez
2. **StateGraph létrehozása** - `StateGraph(AgentState)`
3. **Node-ok hozzáadása** - `add_node(name, function)`
4. **Entry point beállítása** - `set_entry_point("agent_decide")`
5. **Conditional edges** - `add_conditional_edges()` routing függvénnyel
6. **Loop edges** - `add_edge()` tool → agent_decide
7. **END edge** - `add_edge("agent_finalize", END)`
8. **Compile** - `workflow.compile()`
9. **Végrehajtás** - `await workflow.ainvoke(initial_state, {"recursion_limit": 50})`

### Kulcsfontosságú design döntések:

✅ **Ciklikus graph** - tool-ok után visszaugrunk decision-re (multi-step reasoning)  
✅ **Conditional routing** - LLM döntés alapján választjuk ki a következő node-ot  
✅ **State-based** - minden node megkapja és módosítja a teljes állapotot  
✅ **Safety limits** - MAX_ITERATIONS és recursion_limit végtelen loop ellen  
✅ **Deduplication** - tools_called lista megakadályozza a duplikált hívásokat  

### Kapcsolódó fájlok:

- **Agent kód:** `backend/services/agent.py`
- **Domain modellek:** `backend/domain/models.py`
- **Tool implementációk:** `backend/services/tools.py`
- **Node dokumentáció:** `docs/LANGGRAPH_NODES_HU.md`
- **Prompt dokumentáció:** `docs/PROMPTS.md`
