# LangGraph Node-ok és Külső API Hívások

Ez a dokumentum részletezi, hogy az AI Agent alkalmazásban mely LangGraph node-ok hívnak külső API-kat, és melyek dolgoznak lokálisan.

## 📊 Node Típusok Áttekintése

### 1. **Döntési Node-ok** (Nem hívnak külső API-t)

#### `agent_decide` Node
- **Fájl**: `backend/services/agent.py` → `_agent_decide_node()` (127-208. sor)
- **Funkció**: GPT-4 LLM használata a felhasználói kérés elemzésére és következő lépés meghatározására
- **API hívás**: **Igen** - OpenAI GPT-4 API (LangChain-en keresztül)
- **Kód**:
```python
async def _agent_decide_node(self, state: AgentState) -> AgentState:
    """Agent decision node: Analyzes user request and decides next action."""
    logger.info("Agent decision node executing")
    
    # Build context for LLM
    system_prompt = self._build_system_prompt(state["memory"])
    
    # Get last user message
    last_user_msg = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break
    
    # Build conversation context for decision
    recent_history = state["memory"].chat_history[-5:] if state["memory"].chat_history else []
    history_context = "\n".join([f"{msg.role}: {msg.content[:100]}" for msg in recent_history])
    
    # Create decision prompt
    decision_prompt = f"""
    ... (GPT-4-nek küldött prompt) ...
    """
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=decision_prompt)
    ]
    
    # OpenAI API hívás itt történik
    response = await self.llm.ainvoke(messages)
    
    # Parse JSON decision
    decision = json.loads(response.content)
    state["next_action"] = decision.get("action", "final_answer")
    
    if decision.get("action") == "call_tool":
        state["tool_decision"] = decision
        state["iteration_count"] = state.get("iteration_count", 0) + 1
    
    return state
```

**Külső API**: OpenAI GPT-4 (`gpt-4-turbo-preview`)

---

#### `agent_finalize` Node
- **Fájl**: `backend/services/agent.py` → `_agent_finalize_node()` (271-312. sor)
- **Funkció**: Végső válasz generálása az összes tool eredmény alapján
- **API hívás**: **Igen** - OpenAI GPT-4 API
- **Kód**:
```python
async def _agent_finalize_node(self, state: AgentState) -> AgentState:
    """Generate final response incorporating all tool results."""
    logger.info("Agent finalize node executing")
    
    # Build final prompt with memory and tool results
    system_prompt = self._build_system_prompt(state["memory"])
    
    # Get conversation context
    conversation_history = "\n".join([
        f"{msg.__class__.__name__}: {msg.content}"
        for msg in state["messages"][-10:]  # Last 10 messages
    ])
    
    final_prompt = f"""
    Generate a natural language response to the user based on the conversation history and any tool results.
    
    Conversation:
    {conversation_history}
    
    Important:
    - Respond in {state['memory'].preferences.get('language', 'hu')} language
    - Be helpful and conversational
    - Use information from tool results if available
    - Keep the response concise but complete
    """
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=final_prompt)
    ]
    
    # OpenAI API hívás itt történik
    response = await self.llm.ainvoke(messages)
    
    # Add assistant message
    state["messages"].append(AIMessage(content=response.content))
    
    return state
```

**Külső API**: OpenAI GPT-4

---

#### `_route_decision` Routing Function
- **Fájl**: `backend/services/agent.py` → `_route_decision()` (219-233. sor)
- **Funkció**: Eldönti, melyik node-ra irányítson tovább (tool vagy finalize)
- **API hívás**: **Nem** - Csak logikai döntés
- **Kód**:
```python
def _route_decision(self, state: AgentState) -> str:
    """Route to next node based on agent decision."""
    # Check iteration limit to prevent infinite loops
    if state.get("iteration_count", 0) >= MAX_ITERATIONS:
        logger.warning(f"Max iterations ({MAX_ITERATIONS}) reached, forcing finalize")
        return "final_answer"
    
    action = state.get("next_action", "final_answer")
    
    if action == "call_tool" and "tool_decision" in state:
        tool_name = state["tool_decision"].get("tool_name")
        if tool_name in self.tools:
            return f"tool_{tool_name}"
    
    return "final_answer"
```

**Külső API**: Nincs

---

### 2. **Tool Node-ok** (Külső API-t hívnak)

#### `tool_weather` Node
- **Tool Wrapper**: `backend/services/tools.py` → `WeatherTool` (19-67. sor)
- **API Client**: `backend/infrastructure/tool_clients.py` → `OpenMeteoWeatherClient` (20-87. sor)
- **Külső API**: [Open-Meteo](https://open-meteo.com/)
- **Endpoint**: `https://api.open-meteo.com/v1/forecast`
- **Paraméterek**: `latitude`, `longitude`, `current`, `hourly`, `timezone`
- **Válasz**: Aktuális hőmérséklet + 48 órás előrejelzés
- **Példa**:
```python
async def get_forecast(self, city: str = None, lat: float = None, lon: float = None):
    # Geocoding if city provided
    if city:
        # Convert city to coordinates
    
    # API hívás
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m",
        "hourly": "temperature_2m",
        "timezone": "auto"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(self.BASE_URL, params=params)
        data = response.json()
    
    return formatted_result
```

---

#### `tool_geocode` Node
- **Tool Wrapper**: `backend/services/tools.py` → `GeocodeTool` (70-111. sor)
- **API Client**: `backend/infrastructure/tool_clients.py` → `NominatimGeocodeClient` (90-158. sor)
- **Külső API**: [Nominatim (OpenStreetMap)](https://nominatim.openstreetmap.org/)
- **Endpoint**: 
  - `https://nominatim.openstreetmap.org/search` (cím → koordináták)
  - `https://nominatim.openstreetmap.org/reverse` (koordináták → cím)
- **Paraméterek**: `q` (címkeresés) vagy `lat`/`lon` (reverse)
- **Válasz**: Koordináták vagy cím részletei
- **Példa**:
```python
async def geocode(self, address: str):
    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{self.BASE_URL}/search", params=params)
        results = response.json()
    
    if results:
        return {
            "latitude": float(results[0]["lat"]),
            "longitude": float(results[0]["lon"]),
            "display_name": results[0]["display_name"]
        }
```

---

#### `tool_ip_geolocation` Node
- **Tool Wrapper**: `backend/services/tools.py` → `IPGeolocationTool` (114-144. sor)
- **API Client**: `backend/infrastructure/tool_clients.py` → `IPAPIGeolocationClient` (161-196. sor)
- **Külső API**: [ipapi.co](https://ipapi.co/)
- **Endpoint**: `https://ipapi.co/{ip}/json/`
- **Paraméterek**: `ip` (opcionális, default: caller IP)
- **Válasz**: Ország, város, régió, koordináták, ISP
- **Példa**:
```python
async def get_location(self, ip_address: str = ""):
    url = f"{self.BASE_URL}/{ip_address}/json/" if ip_address else f"{self.BASE_URL}/json/"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
    
    return {
        "ip": data.get("ip"),
        "city": data.get("city"),
        "region": data.get("region"),
        "country": data.get("country_name"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude")
    }
```

---

#### `tool_fx_rates` Node
- **Tool Wrapper**: `backend/services/tools.py` → `FXRatesTool` (147-178. sor)
- **API Client**: `backend/infrastructure/tool_clients.py` → `ExchangeRateHostClient` (199-240. sor)
- **Külső API**: [Frankfurter.app](https://www.frankfurter.app/)
- **Endpoint**: 
  - `https://api.frankfurter.app/latest` (aktuális)
  - `https://api.frankfurter.app/{date}` (történeti)
- **Paraméterek**: `base`, `symbols`, `date` (opcionális)
- **Válasz**: Árfolyamok a bázis valutához képest
- **Megjegyzés**: Ingyenes, nem kell API kulcs! (Korábban ExchangeRate.host volt)
- **Példa**:
```python
async def get_rate(self, base: str, target: str, date: str = None):
    endpoint = f"{self.BASE_URL}/{date}" if date else f"{self.BASE_URL}/latest"
    params = {
        "from": base.upper(),
        "to": target.upper()
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(endpoint, params=params)
        data = response.json()
    
    rate = data["rates"].get(target.upper())
    return {"base": base, "target": target, "rate": rate, "date": data["date"]}
```

---

#### `tool_crypto_price` Node
- **Tool Wrapper**: `backend/services/tools.py` → `CryptoPriceTool` (181-211. sor)
- **API Client**: `backend/infrastructure/tool_clients.py` → `CoinGeckoCryptoClient` (243-280. sor)
- **Külső API**: [CoinGecko](https://api.coingecko.com/)
- **Endpoint**: `https://api.coingecko.com/api/v3/simple/price`
- **Paraméterek**: `ids` (kriptovaluta), `vs_currencies` (fiat valuta)
- **Válasz**: Aktuális ár, 24h változás
- **Példa**:
```python
async def get_price(self, symbol: str, fiat: str = "usd"):
    # Map common symbols to CoinGecko IDs
    symbol_map = {
        "btc": "bitcoin",
        "eth": "ethereum",
        "ada": "cardano",
        "sol": "solana"
    }
    
    coin_id = symbol_map.get(symbol.lower(), symbol.lower())
    
    params = {
        "ids": coin_id,
        "vs_currencies": fiat.lower(),
        "include_24hr_change": "true"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(self.BASE_URL, params=params)
        data = response.json()
    
    return {
        "symbol": symbol.upper(),
        "price": data[coin_id][fiat.lower()],
        "change_24h": data[coin_id].get(f"{fiat.lower()}_24h_change")
    }
```

---

#### `tool_daily_advice` Node
- **Fájl**: `backend/services/tools.py` → `DailyAdviceTool`
- **Funkció**: Napi tanács lekérése egy külső API-ról.
- **API hívás**: **Igen** - [Advice Slip API](https://api.adviceslip.com/advice)
- **Kód**:
```python
class DailyAdviceTool:
    """Daily advice tool."""

    def __init__(self):
        self.name = "daily_advice"
        self.description = "Fetch a daily advice from an external API. Useful for motivational or general advice queries."

    async def execute(self) -> Dict[str, Any]:
        """Fetch daily advice."""
        import aiohttp
        url = "https://api.adviceslip.com/advice"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    advice = data.get("slip", {}).get("advice", "No advice available.")
                    return {
                        "success": True,
                        "advice": advice,
                        "system_message": f"Fetched daily advice: {advice}"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to fetch advice. HTTP status: {response.status}",
                        "system_message": "Failed to fetch daily advice."
                    }
```

---

## 💾 Lokális (Nem API) Tool Node-ok

### 6. `tool_create_file` - Fájl Létrehozás
- **Tool Wrapper**: `backend/services/tools.py` → `FileCreationTool` (214-244. sor)
- **API Client**: **Nincs** - Lokális fájlrendszer művelet
- **Művelet**: Fájl írása `backend/data/files/user_{user_id}/` mappába
- **Paraméterek**: `user_id`, `filename`, `content`
- **Példa**:
```python
async def execute(self, user_id: str, filename: str, content: str):
    # Create user directory
    user_dir = Path(f"data/files/user_{user_id}")
    user_dir.mkdir(parents=True, exist_ok=True)
    
    # Write file
    file_path = user_dir / filename
    file_path.write_text(content, encoding="utf-8")
    
    return {
        "success": True,
        "data": {"path": str(file_path), "filename": filename},
        "system_message": f"File saved: {filename}"
    }
```

**Külső API**: **Nincs** - Csak lokális I/O

---

### 7. `tool_search_history` - Beszélgetés Történet Keresés
- **Tool Wrapper**: `backend/services/tools.py` → `HistorySearchTool` (247-264. sor)
- **Repository**: `backend/infrastructure/repositories.py` → `FileConversationRepository.search_messages()` (123-155. sor)
- **API Client**: **Nincs** - Lokális JSON fájl keresés
- **Művelet**: Keresés a `backend/data/sessions/*.json` fájlokban
- **Paraméterek**: `query` (keresési kulcsszó)
- **Példa**:
```python
async def execute(self, query: str):
    results = await self.repository.search_messages(query)
    
    formatted_results = [
        {
            "session": r.session_id,
            "snippet": r.snippet,
            "timestamp": r.timestamp.isoformat(),
            "role": r.role
        }
        for r in results[:10]  # Limit to 10 results
    ]
    
    return {
        "success": True,
        "data": {"results": formatted_results, "count": len(results)},
        "system_message": f"Found {len(results)} messages matching '{query}'"
    }
```

**Külső API**: **Nincs** - Csak lokális fájlkeresés

---

## 🔄 LangGraph Workflow Folyamat

### Graph Struktúra
```
Entry → agent_decide → routing → [tools] → agent_decide (loop) → agent_finalize → END
                                     ↓
                         ┌───────────┴───────────┐
                         ↓                       ↓
                    Külső API Tools        Lokális Tools
                    ---------------        -------------
                    - weather              - create_file
                    - geocode              - search_history
                    - ip_geolocation
                    - fx_rates
                    - crypto_price
                    - daily_advice
```

### Node Hozzáadás a Graph-hoz
**Fájl**: `backend/services/agent.py` → `_build_graph()` (81-122. sor)

```python
def _build_graph(self) -> StateGraph:
    """Build the LangGraph workflow graph."""
    workflow = StateGraph(AgentState)
    
    # Add decision nodes
    workflow.add_node("agent_decide", self._agent_decide_node)
    workflow.add_node("agent_finalize", self._agent_finalize_node)
    
    # Add tool nodes - DINAMIKUS LÉTREHOZÁS
    for tool_name in self.tools.keys():
        workflow.add_node(f"tool_{tool_name}", self._create_tool_node(tool_name))
    
    # Set entry point
    workflow.set_entry_point("agent_decide")
    
    # Add conditional edges from agent_decide
    workflow.add_conditional_edges(
        "agent_decide",
        self._route_decision,
        {
            "final_answer": "agent_finalize",
            **{f"tool_{name}": f"tool_{name}" for name in self.tools.keys()}
        }
    )
    
    # Add edges from tools back to agent_decide (multi-step loop)
    for tool_name in self.tools.keys():
        workflow.add_edge(f"tool_{tool_name}", "agent_decide")
    
    # Add edge from finalize to end
    workflow.add_edge("agent_finalize", END)
    
    # Compile the workflow
    return workflow.compile()
```

---

## 📊 Összefoglaló Táblázat

| Node Neve | Típus | Külső API | API Provider | HTTP Könyvtár |
|-----------|-------|-----------|--------------|---------------|
| `agent_decide` | Döntési | ✅ Igen | OpenAI GPT-4 | LangChain |
| `agent_finalize` | Döntési | ✅ Igen | OpenAI GPT-4 | LangChain |
| `_route_decision` | Routing | ❌ Nem | - | - |
| `tool_weather` | Tool | ✅ Igen | Open-Meteo | httpx |
| `tool_geocode` | Tool | ✅ Igen | Nominatim (OSM) | httpx |
| `tool_ip_geolocation` | Tool | ✅ Igen | ipapi.co | httpx |
| `tool_fx_rates` | Tool | ✅ Igen | Frankfurter.app | httpx |
| `tool_crypto_price` | Tool | ✅ Igen | CoinGecko | httpx |
| `tool_daily_advice` | Tool | ✅ Igen | Advice Slip API | aiohttp |
| `tool_create_file` | Tool | ❌ Nem | Lokális fájlrendszer | Python Path |
| `tool_search_history` | Tool | ❌ Nem | Lokális JSON fájlok | Python json |

---

## 🔒 Biztonsági Mechanizmusok

### Iteration Limit
- **Konstans**: `MAX_ITERATIONS = 10` (`agent.py` 27. sor)
- **Funkció**: Végtelen ciklusok megelőzése multi-step workflow-ban
- **Implementáció**: `_route_decision()` ellenőrzi az `iteration_count`-ot

### Recursion Limit
- **Beállítás**: `{"recursion_limit": 50}` az `ainvoke()` hívásban
- **Funkció**: LangGraph maximum állapot átmenetek limitálása
- **Implementáció**: `agent.run()` metódusban (377. sor)

```python
# Run workflow with increased recursion limit for multi-step workflows
final_state = await self.workflow.ainvoke(
    initial_state,
    {"recursion_limit": 50}
)
```

---

## 🛠️ Fejlesztési Jegyzetek

### Új Tool Hozzáadása

1. **Tool Wrapper létrehozása** (`services/tools.py`):
```python
class NewTool:
    def __init__(self, client: INewClient):
        self.client = client
        self.name = "new_tool"
        self.description = "Tool description"
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        result = await self.client.call_api(**kwargs)
        return {
            "success": True,
            "data": result,
            "system_message": "Tool executed successfully"
        }
```

2. **API Client létrehozása** (ha külső API-t hív):
```python
# infrastructure/tool_clients.py
class NewAPIClient:
    BASE_URL = "https://api.example.com"
    
    async def call_api(self, param: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/endpoint", params={"q": param})
            return response.json()
```

3. **Tool regisztrálása** (`services/agent.py` `__init__`):
```python
self.tools = {
    # ... existing tools ...
    "new_tool": new_tool
}
```

4. **Graph automatikusan létrehozza a node-ot** - nincs további teendő!

---

**Utolsó frissítés**: 2025. december 9.  
**Verzió**: 1.0  
**Státusz**: Teljes LangGraph node dokumentáció külső API hívásokkal
