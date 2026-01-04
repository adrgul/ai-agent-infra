# LangGraph + LangChain minta (ai_agent_complex)

## Áttekintés
Az `ai_agent_complex` projekt egy fejlett AI agent architektúrát valósít meg, amely a LangGraph és LangChain könyvtárakat használja Pythonban. A rendszer célja, hogy rugalmas, bővíthető, több lépéses AI workflow-kat valósítson meg, ahol az agent döntéseket hoz, eszközöket (toolokat) hív, memóriát kezel, és többféle külső API-t integrál.

## Főbb jellemzők
- **LangGraph-alapú orchestration**: Az agent működése egy irányított gráf (StateGraph) mentén történik, ahol minden node egy-egy döntési vagy eszköz-végrehajtási lépést jelent.
- **Több eszköz integráció**: Időjárás, geokódolás, IP geolokáció, devizaárfolyam, kriptovaluta ár, fájlkezelés, keresés.
- **Memóriakezelés**: Felhasználói preferenciák, előzmények, workflow állapot.
- **Ciklikus, feltételes routing**: Az agent többször is visszatérhet döntési ponthoz, több eszközt is meghívhat egymás után.
- **Állapotkezelés**: Minden node hozzáfér a teljes agent state-hez (TypedDict).
- **Bővíthetőség**: Új node-ok, eszközök könnyen hozzáadhatók.

## Architektúra
```
User üzenet
   |
   v
+-------------------+
|  agent_decide     | <--- LLM döntés, hogy kell-e tool
+-------------------+
   |         |
   |         +-------------------+
   |---------------->| tool_*    | (pl. weather, geocode, stb.)
   |         +-------------------+
   |                |
   |<---------------+
   v
+-------------------+
| agent_finalize    | <--- LLM válasz generálás
+-------------------+
   |
   v
  END
```
- **agent_decide**: LLM reasoning, eldönti, hogy kell-e tool, ha igen, melyik.
- **tool_***: Külső vagy belső eszközök végrehajtása (API hívás, fájl, stb.).
- **agent_finalize**: Végső válasz generálása.
- **Loop**: Több tool hívás is lehetséges, minden tool után visszatér a döntési ponthoz.

## Példakód (gráf építés)
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
    workflow = StateGraph(AgentState)
    workflow.add_node("agent_decide", self._agent_decide_node)
    workflow.add_node("agent_finalize", self._agent_finalize_node)
    for tool_name in ["weather", "geocode", "fx_rates", "crypto_price", "create_file"]:
        workflow.add_node(f"tool_{tool_name}", self._create_tool_node(tool_name))
    workflow.set_entry_point("agent_decide")
    workflow.add_conditional_edges(
        "agent_decide",
        self._route_decision,
        {"final_answer": "agent_finalize", **{f"tool_{name}": f"tool_{name}" for name in self.tools.keys()}}
    )
    for tool_name in self.tools.keys():
        workflow.add_edge(f"tool_{tool_name}", "agent_decide")
    workflow.add_edge("agent_finalize", END)
    return workflow.compile()
```

## Előnyök
- **Többlépéses reasoning**: Az agent többször is dönthet, több toolt is hívhat, amíg el nem jut a végső válaszig.
- **Állapotkezelés**: Minden node-ban elérhető a teljes workflow state.
- **Feltételes routing**: Az agent döntése alapján dinamikusan változik a workflow.
- **Ciklikus gráf**: Tool → agent_decide → tool ... (loopolás támogatott).
- **Egyszerű bővíthetőség**: Új tool vagy node hozzáadása minimális kóddal.
- **Biztonság**: Recursion limit, hibakezelés minden node-ban.

## Dokumentáció
- [docs/LANGGRAPH_USAGE_HU.md](../ai_agent_complex/docs/LANGGRAPH_USAGE_HU.md): Részletes magyar leírás, példakódokkal, architektúra ábrákkal.
- [docs/LANGGRAPH_NODES_HU.md](../ai_agent_complex/docs/LANGGRAPH_NODES_HU.md): Node típusok, API integrációk.
- [docs/ARCHITECTURE.md](../ai_agent_complex/docs/ARCHITECTURE.md): Teljes rendszer architektúra.

---

Ez a minta jól mutatja, hogyan lehet a LangGraph segítségével komplex, több lépéses, bővíthető AI agent workflow-t építeni, ahol az LLM nem csak egyszer dönt, hanem akár többször is, és minden lépésben explicit állapotkezelés és routing történik.