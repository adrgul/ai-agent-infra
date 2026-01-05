"""
Unified Chat Workflow - Agent-based routing with loop support.

Combines RAG, direct chat, document listing, and future long-term memory 
into a single LangGraph workflow with intelligent routing.

Architecture:
START → validate_input → build_full_context → agent_decide
  ├─ CHAT → execute_direct_chat → agent_decide (loop)
  ├─ RAG → execute_rag_search → agent_decide (loop)
  ├─ LIST → execute_list_docs → agent_decide (loop)
  └─ FINAL_ANSWER → agent_finalize → END

Future extensions:
  ├─ MEMORY → execute_ltm_search → agent_decide (loop)
"""

import logging
import time
from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from services.embedding_service import EmbeddingService
from services.qdrant_service import QdrantService
from services.config_service import get_config_service
from services.cache_service import get_context_cache
from database.document_chunk_repository import DocumentChunkRepository
from database.pg_init import (
    get_tenant_by_id, 
    get_user_by_id_pg,
    get_latest_cached_prompt,
    save_cached_prompt,
    get_session_messages_pg
)
from config.prompts import build_system_prompt, APPLICATION_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Safety: Maximum agent iterations to prevent infinite loops
MAX_ITERATIONS = 10


# ===== STATE DEFINITIONS =====

class UserContext(TypedDict):
    """User context for unified workflow."""
    tenant_id: int
    user_id: int
    tenant_prompt: Optional[str]
    user_prompt: Optional[str]
    user_language: str  # 'hu' | 'en'
    firstname: Optional[str]
    lastname: Optional[str]
    email: Optional[str]
    role: Optional[str]


class DocumentChunk(TypedDict):
    """Retrieved document chunk with metadata."""
    chunk_id: int
    document_id: int
    content: str
    metadata: Dict[str, Any]
    similarity_score: float


class ChatState(TypedDict):
    """State object for unified chat workflow (agent-based)."""
    # Input
    query: str
    session_id: str
    user_context: UserContext
    
    # Context building (node 2)
    chat_history: List[Dict[str, str]]  # [{role, content}]
    system_prompt: Optional[str]
    system_prompt_cached: bool
    cache_source: Optional[str]  # "memory" | "database" | "llm_generated"
    
    # Agent loop control
    next_action: Optional[str]  # "CHAT" | "RAG" | "LIST" | "EXPLICIT_MEMORY" | "FINAL_ANSWER"
    iteration_count: int
    actions_taken: List[str]  # Audit trail: ["RAG", "CHAT", "EXPLICIT_MEMORY"]
    
    # Branch-specific data
    retrieved_chunks: List[DocumentChunk]  # RAG branch
    listed_documents: List[Dict]  # LIST branch
    ltm_results: Optional[List[Dict]]  # MEMORY branch (future)
    explicit_fact: Optional[str]  # EXPLICIT_MEMORY branch (extracted fact)
    
    # Intermediate results (multi-step)
    intermediate_results: List[str]
    
    # Output
    final_answer: Optional[str]
    sources: List[Dict[str, Any]]  # [{"id": document_id, "title": document_title}]
    error: Optional[str]


# ===== UNIFIED CHAT WORKFLOW =====

class UnifiedChatWorkflow:
    """
    LangGraph-based unified chat workflow with agent loop.
    
    Graph structure:
    START → validate_input → build_full_context → agent_decide
      ├─ execute_direct_chat → agent_decide (loop)
      ├─ execute_rag_search → agent_decide (loop)
      ├─ execute_list_docs → agent_decide (loop)
      └─ agent_finalize → END
    """
    
    def __init__(self, openai_api_key: str):
        self.config = get_config_service()
        
        # Initialize services
        self.embedding_service = EmbeddingService()
        self.qdrant_service = QdrantService()
        self.chunk_repo = DocumentChunkRepository()
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.config.get_chat_model(),
            temperature=self.config.get_temperature(),
            max_tokens=self.config.get_max_tokens(),
            api_key=openai_api_key
        )
        
        # Build workflow graph
        self.graph = self._build_graph()
        
        # Store LLM messages per session for prompt inspection (outside state to avoid validation errors)
        self._llm_messages_by_session = {}
        
        # WebSocket state broadcasting (optional, enabled per session)
        self._enable_ws_broadcast = {}  # session_id -> bool
        
        logger.info("UnifiedChatWorkflow initialized with agent loop support")
    
    def _build_graph(self) -> Any:
        """Build the LangGraph workflow with agent loop."""
        workflow = StateGraph(ChatState)
        
        # Add nodes
        workflow.add_node("validate_input", self._validate_input_node)
        workflow.add_node("build_full_context", self._build_full_context_node)
        workflow.add_node("agent_decide", self._agent_decide_node)
        workflow.add_node("execute_direct_chat", self._execute_direct_chat_node)
        workflow.add_node("execute_rag_search", self._execute_rag_search_node)
        workflow.add_node("execute_list_docs", self._execute_list_docs_node)
        workflow.add_node("execute_explicit_memory", self._execute_explicit_memory_node)  # NEW
        workflow.add_node("agent_finalize", self._agent_finalize_node)
        
        # Define edges
        workflow.set_entry_point("validate_input")
        workflow.add_edge("validate_input", "build_full_context")
        workflow.add_edge("build_full_context", "agent_decide")
        
        # Conditional routing from agent_decide
        workflow.add_conditional_edges(
            "agent_decide",
            self._route_from_agent_decide,
            {
                "execute_direct_chat": "execute_direct_chat",
                "execute_rag_search": "execute_rag_search",
                "execute_list_docs": "execute_list_docs",
                "execute_explicit_memory": "execute_explicit_memory",  # NEW
                "agent_finalize": "agent_finalize"
            }
        )
        
        # Tool nodes loop back to agent_decide (multi-step reasoning)
        workflow.add_edge("execute_direct_chat", "agent_decide")
        workflow.add_edge("execute_rag_search", "agent_decide")
        workflow.add_edge("execute_list_docs", "agent_decide")
        workflow.add_edge("execute_explicit_memory", "agent_decide")  # NEW
        
        # Finalize ends workflow
        workflow.add_edge("agent_finalize", END)
        
        return workflow.compile()
    
    async def _broadcast_state(self, node_name: str, state: ChatState):
        """
        Broadcast workflow state to WebSocket clients if enabled for this session.
        
        Args:
            node_name: Current node name
            state: Current workflow state
        """
        session_id = state.get("session_id")
        if not session_id or not self._enable_ws_broadcast.get(session_id, False):
            return
        
        try:
            from services.websocket_manager import websocket_manager
            
            # Serialize state (exclude non-serializable fields)
            state_snapshot = {
                "query": state.get("query"),
                "session_id": session_id,
                "next_action": state.get("next_action"),
                "iteration_count": state.get("iteration_count"),
                "actions_taken": state.get("actions_taken", []),
                "retrieved_chunks_count": len(state.get("retrieved_chunks", [])),
                "listed_documents_count": len(state.get("listed_documents", [])),
                "intermediate_results_count": len(state.get("intermediate_results", [])),
                "system_prompt_cached": state.get("system_prompt_cached", False),
                "cache_source": state.get("cache_source"),
                "error": state.get("error")
            }
            
            await websocket_manager.broadcast_state(session_id, node_name, state_snapshot)
        
        except Exception as e:
            logger.error(f"Failed to broadcast state: {e}")
    
    # ===== NODE IMPLEMENTATIONS =====
    
    def _validate_input_node(self, state: ChatState) -> ChatState:
        """
        Node 1: Validate input parameters.
        
        Checks:
        - query not empty
        - session_id present
        - tenant_id and user_id present
        """
        logger.info("[NODE 1: validate_input] Validating input")
        
        try:
            query = state.get("query", "").strip()
            session_id = state.get("session_id", "").strip()
            user_ctx = state.get("user_context", {})
            
            if not query:
                raise ValueError("Query cannot be empty")
            
            if not session_id:
                raise ValueError("session_id is required")
            
            if not user_ctx.get("tenant_id"):
                raise ValueError("tenant_id is required")
            
            if not user_ctx.get("user_id"):
                raise ValueError("user_id is required")
            
            logger.info(f"[NODE 1] Validation passed: query_len={len(query)}, session={session_id}, tenant={user_ctx['tenant_id']}, user={user_ctx['user_id']}")
            
            return state
        
        except Exception as e:
            logger.error(f"[NODE 1] Validation failed: {e}")
            return {
                **state,
                "error": str(e),
                "final_answer": f"Validation error: {str(e)}",
                "sources": []
            }
    
    def _build_full_context_node(self, state: ChatState) -> ChatState:
        """
        Node 2: Build full context with 3-tier cached system prompt.
        
        Steps:
        1. Fetch user/tenant data (cache 5 min)
        2. Fetch chat history (last 30 messages)
        3. Check system_prompt cache (memory → DB → LLM)
        4. Build final context
        """
        start_time = time.time()
        logger.info("[NODE 2: build_full_context] Building full context")
        
        try:
            user_ctx = state["user_context"]
            session_id = state["session_id"]
            cache = get_context_cache()
            
            # === STEP 1: Fetch tenant (cache 5 min) ===
            tenant_cache_key = f"tenant:{user_ctx['tenant_id']}"
            tenant_start = time.time()
            tenant = cache.get(tenant_cache_key)
            
            if tenant is None:
                logger.info(f"🔴 Cache MISS: {tenant_cache_key}")
                tenant = get_tenant_by_id(user_ctx["tenant_id"])
                if tenant:
                    cache.set(tenant_cache_key, tenant, ttl_seconds=300)
                logger.info(f"⏱️ Tenant DB query: {time.time() - tenant_start:.2f}s")
            else:
                logger.info(f"🟢 Cache HIT: {tenant_cache_key} ({time.time() - tenant_start:.3f}s)")
            
            tenant_prompt = tenant.get("system_prompt") if tenant else None
            
            # === STEP 2: Fetch user (cache 5 min) ===
            user_cache_key = f"user:{user_ctx['user_id']}"
            user_start = time.time()
            user = cache.get(user_cache_key)
            
            if user is None:
                logger.info(f"🔴 Cache MISS: {user_cache_key}")
                user = get_user_by_id_pg(user_ctx["user_id"])
                if user:
                    cache.set(user_cache_key, user, ttl_seconds=300)
                logger.info(f"⏱️ User DB query: {time.time() - user_start:.2f}s")
            else:
                logger.info(f"🟢 Cache HIT: {user_cache_key} ({time.time() - user_start:.3f}s)")
            
            user_prompt = user.get("system_prompt") if user else None
            user_language = user.get("default_lang", "en") if user else "en"
            
            # Update user_context with full data
            updated_user_ctx: UserContext = {
                **user_ctx,
                "tenant_prompt": tenant_prompt,
                "user_prompt": user_prompt,
                "user_language": user_language,
                "firstname": user.get("firstname") if user else None,
                "lastname": user.get("lastname") if user else None,
                "email": user.get("email") if user else None,
                "role": user.get("role") if user else None
            }
            
            # === STEP 3: Fetch chat history (configurable short-term memory) ===
            config_service = get_config_service()
            short_term_limit = config_service.get_int('memory', 'SHORT_TERM_MEMORY_MESSAGES', default=30)
            short_term_scope = config_service.get('memory', 'SHORT_TERM_MEMORY_SCOPE', default='session').lower()
            
            history_start = time.time()
            if short_term_scope == 'user':
                # Fetch last N messages across ALL user sessions
                from database.pg_init import get_last_messages_for_user_pg
                messages = get_last_messages_for_user_pg(user_ctx["user_id"], limit=short_term_limit)
                logger.info(f"📚 Short-term memory scope: USER (across all sessions)")
            else:
                # Fetch last N messages from CURRENT session only (default)
                messages = get_session_messages_pg(session_id, limit=short_term_limit)
                logger.info(f"📚 Short-term memory scope: SESSION (current session only)")
            
            # Convert to simple format: [{role, content}]
            chat_history = [
                {"role": msg.get("role", "user"), "content": msg.get("content", "")}
                for msg in messages
            ]
            
            logger.info(f"⏱️ Chat history: {len(chat_history)} messages in {time.time() - history_start:.2f}s")
            
            # === STEP 4: Get cached system prompt (3-tier cache) ===
            system_prompt, cached, source = self._get_or_build_system_prompt(
                user_id=user_ctx["user_id"],
                user=user,
                tenant_prompt=tenant_prompt,
                user_prompt=user_prompt
            )
            
            total_time = time.time() - start_time
            logger.info(f"✅ [NODE 2: build_full_context] Completed in {total_time:.2f}s (cache_source={source})")
            
            return {
                **state,
                "user_context": updated_user_ctx,
                "chat_history": chat_history,
                "system_prompt": system_prompt,
                "system_prompt_cached": cached,
                "cache_source": source
            }
        
        except Exception as e:
            logger.error(f"[NODE 2] Context building failed: {e}", exc_info=True)
            return {
                **state,
                "error": f"Context building error: {str(e)}",
                "final_answer": "Failed to build context",
                "sources": []
            }
    
    def _get_or_build_system_prompt(
        self,
        user_id: int,
        user: Optional[Dict],
        tenant_prompt: Optional[str],
        user_prompt: Optional[str]
    ) -> tuple[str, bool, str]:
        """
        Get system prompt with 3-tier cache.
        
        Returns:
            (prompt, is_cached, cache_source)
        """
        cache = get_context_cache()
        
        # === TIER 1: Memory cache (1 hour TTL) ===
        cache_key = f"system_prompt:{user_id}"
        cached_prompt = cache.get(cache_key)
        
        if cached_prompt:
            logger.info(f"🟢 MEMORY HIT: {cache_key}")
            return (cached_prompt, True, "memory")
        
        logger.info(f"🔴 MEMORY MISS: {cache_key}")
        
        # === TIER 2: PostgreSQL cache (persistent) ===
        db_cached_prompt = get_latest_cached_prompt(user_id)
        
        if db_cached_prompt:
            logger.info(f"🟡 DB HIT: user_id={user_id}")
            # Store in memory for future requests
            cache.set(cache_key, db_cached_prompt, ttl_seconds=3600)
            return (db_cached_prompt, True, "database")
        
        logger.info(f"🔴 DB MISS: user_id={user_id}")
        
        # === TIER 3: Build from scratch (no optimization yet) ===
        # TODO: LLM optimization in Phase 3
        logger.info(f"🔵 BUILD: user_id={user_id}")
        
        raw_prompt = build_system_prompt(
            user_context=user,
            tenant_prompt=tenant_prompt,
            user_prompt=user_prompt
        )
        
        # Save to PostgreSQL (persistent)
        save_cached_prompt(user_id, raw_prompt)
        
        # Save to memory cache
        cache.set(cache_key, raw_prompt, ttl_seconds=3600)
        
        return (raw_prompt, False, "built")
    
    def _agent_decide_node(self, state: ChatState) -> ChatState:
        """
        Node 3: Agent decision - decides next action.
        
        Can loop multiple times:
        - First call: Analyze query → decide initial action
        - Subsequent calls: Analyze results → decide if done or continue
        """
        iteration = state.get("iteration_count", 0)
        
        logger.info(f"[NODE 3: agent_decide] Iteration {iteration}")
        
        if iteration >= MAX_ITERATIONS:
            logger.warning(f"Max iterations ({MAX_ITERATIONS}) reached, forcing finalize")
            return {**state, "next_action": "FINAL_ANSWER"}
        
        # Build decision prompt
        if iteration == 0:
            # First iteration - analyze query
            decision = self._make_initial_decision(state)
        else:
            # Subsequent iterations - analyze progress
            decision = self._make_continuation_decision(state)
        
        logger.info(f"[NODE 3] Decision: {decision} (iteration={iteration})")
        
        return {
            **state,
            "next_action": decision,
            "iteration_count": iteration + 1
        }
    
    def _make_initial_decision(self, state: ChatState) -> str:
        """
        Make initial routing decision based on query using LLM.
        
        Returns: "CHAT" | "RAG" | "LIST"
        """
        query = state["query"]
        user_ctx = state["user_context"]
        user_lang = user_ctx.get("user_language", "en")
        query_lower = query.lower()
        
        # Fast-path: Simple greetings (no LLM needed)
        simple_greetings_hu = ["szia", "hello", "heló", "helló", "üdv", "csá", "sziasztok"]
        simple_greetings_en = ["hi", "hello", "hey", "greetings"]
        greetings = simple_greetings_hu if user_lang == "hu" else simple_greetings_en
        
        query_words = query_lower.strip().split()
        if len(query_words) <= 2 and any(greeting in query_lower for greeting in greetings):
            logger.info(f"[DECISION] Simple greeting detected (fast-path) → CHAT")
            return "CHAT"
        
        # LLM-based decision
        logger.info(f"[DECISION] Asking LLM for routing decision")
        
        user_firstname = user_ctx.get("firstname", "User")
        user_lastname = user_ctx.get("lastname", "")
        user_email = user_ctx.get("email", "")
        user_role = user_ctx.get("role", "")
        
        decision_prompts = {
            "hu": """Döntsd el, hogy a felhasználó kérdése milyen típusú választ igényel.

KÉRDÉS: "{query}"

FONTOS INFORMÁCIÓK:
- A felhasználó neve: {user_firstname} {user_lastname}
- Email címe: {user_email}
- Szerepköre: {user_role}

LEHETSÉGES VÁLASZOK:
1. **MEMORY** - Ha a felhasználó KIFEJEZETTEN kéri valaminek a megjegyzését/eltárolását
   - Példák: "jegyezd meg hogy nem bírom a macskákat", "emlékezz rá hogy vegetáriánus vagyok"
   - Példák: "remember that I like pizza", "note that my birthday is May 5th"
   - CSAK akkor használd, ha EXPLICIT memória kérés van ("jegyezd meg", "emlékezz", "remember", "note that")!

2. **CHAT** - Ha SZEMÉLYES ADATOKAT kérdez (név, email, szerepkör) VAGY általános beszélgetés
   - Példák: "mi a nevem?", "tudod a nevem?", "ki vagyok?", "mi az email címem?", "mi a szerepköröm?"
   - Példák: "köszönöm", "hogy vagy?", "mi újság?", "szia"
   
3. **LIST** - Ha dokumentumok listázását kéri
   - Példák: "milyen dokumentumok vannak?", "listázd a doksijaimat", "mutasd meg a feltöltött fájlokat"
   
4. **SEARCH** - Ha DOKUMENTUMOKBAN lévő specifikus információt keres vagy dokumentumok tartalmáról kérdez
   - Példák: "keress rá az elfekre", "mi van a fantasy dokumentumban?", "találd meg Elenar kapitányt"
   - Példák: "mit írnak a dokumentumokban?", "kik szerepelnek a doksiban?", "milyen nevek vannak említve?"
   - Példák: "az emberekről mit írnak?", "az orkokról van infó?", "ki az a Lady Miriel?"
   - HASZNÁLD akkor is, ha a kérdés dokumentumok tartalmára, szereplőkre, nevekre, eseményekre vonatkozik!
   - NE használd személyes adatokra (név, email, szerepkör)!

PRIORITÁS: 
1. Explicit memória kérés ("jegyezd meg", "remember") → MINDIG MEMORY!
2. Személyes adatok (név, email, szerepkör) → MINDIG CHAT, SOHA SEARCH!
3. Dokumentumok tartalma, szereplők, nevek, események → MINDIG SEARCH!

Válaszolj CSAK egy szóval: MEMORY, LIST, SEARCH, vagy CHAT

Válasz:""",
            "en": """Decide what type of response the user's query requires.

QUERY: "{query}"

IMPORTANT INFORMATION:
- User's name: {user_firstname} {user_lastname}
- Email: {user_email}
- Role: {user_role}

POSSIBLE ANSWERS:
1. **MEMORY** - If user EXPLICITLY asks to remember/note/store something
   - Examples: "remember that I don't like cats", "note that I'm vegetarian"
   - Examples: "jegyezd meg hogy allergias vagyok", "emlékezz rá hogy május 5-én van a szülinapom"
   - ONLY use if there's an EXPLICIT memory request ("remember", "note that", "jegyezd meg", "emlékezz")!

2. **CHAT** - If asking about PERSONAL DATA (name, email, role) OR general conversation
   - Examples: "what's my name?", "do you know my name?", "who am I?", "what's my email?", "what's my role?"
   - Examples: "thanks", "how are you?", "what's up?", "hi"
   
3. **LIST** - If user wants to list/show documents
   - Examples: "what documents do I have?", "list my files", "show all documents"
   
4. **SEARCH** - If searching for SPECIFIC INFORMATION IN DOCUMENTS or asking about document content
   - Examples: "search for elves", "what's in the fantasy document?", "find Captain Elenar"
   - Examples: "what do the documents say?", "who is mentioned in the docs?", "what names are mentioned?"
   - Examples: "what about humans?", "is there info about orcs?", "who is Lady Miriel?"
   - USE this even if the question is about document content, characters, names, events!
   - DO NOT use for personal data (name, email, role)!

PRIORITY: 
1. Explicit memory request ("remember", "jegyezd meg") → ALWAYS MEMORY!
2. Personal data (name, email, role) → ALWAYS CHAT, NEVER SEARCH!
3. Document content, characters, names, events → ALWAYS SEARCH!

Answer with ONLY one word: MEMORY, LIST, SEARCH, or CHAT

Answer:"""
        }
        
        decision_prompt = decision_prompts.get(user_lang, decision_prompts["en"])
        user_message = decision_prompt.format(
            query=query,
            user_firstname=user_firstname,
            user_lastname=user_lastname,
            user_email=user_email,
            user_role=user_role
        )
        
        # Call LLM
        messages = [
            SystemMessage(content="You are a routing assistant. Answer with exactly one word: MEMORY, LIST, SEARCH, or CHAT."),
            HumanMessage(content=user_message)
        ]
        
        try:
            response = self.llm.invoke(messages)
            decision_text = response.content.strip().upper()
            
            logger.info(f"[DECISION] LLM response: '{decision_text}'")
            
            # Parse decision
            if "MEMORY" in decision_text:
                return "EXPLICIT_MEMORY"
            elif "LIST" in decision_text:
                return "LIST"
            elif "SEARCH" in decision_text:
                return "RAG"
            else:  # CHAT
                return "CHAT"
        
        except Exception as e:
            logger.error(f"[DECISION] LLM call failed: {e}", exc_info=True)
            # Default: CHAT (safest fallback)
            return "CHAT"
    
    def _make_continuation_decision(self, state: ChatState) -> str:
        """
        Decide if more actions needed or ready to finalize.
        
        For now: always finalize after first action (TODO: multi-step in Phase 3)
        """
        # Phase 2: Single-pass only
        return "FINAL_ANSWER"
    
    def _route_from_agent_decide(self, state: ChatState) -> str:
        """
        Route based on agent decision.
        """
        action = state.get("next_action", "FINAL_ANSWER")
        
        routing = {
            "CHAT": "execute_direct_chat",
            "RAG": "execute_rag_search",
            "LIST": "execute_list_docs",
            "EXPLICIT_MEMORY": "execute_explicit_memory",  # NEW
            "FINAL_ANSWER": "agent_finalize"
        }
        
        route = routing.get(action, "agent_finalize")
        logger.info(f"[ROUTING] action={action} -> {route}")
        
        return route
    
    def _execute_direct_chat_node(self, state: ChatState) -> ChatState:
        """
        Node 4a: Execute direct chat (greeting, personal data, general conversation).
        """
        logger.info("[NODE 4a: execute_direct_chat] Executing")
        
        try:
            query = state["query"]
            system_prompt = state.get("system_prompt") or APPLICATION_SYSTEM_PROMPT
            user_lang = state["user_context"].get("user_language", "en")
            chat_history = state.get("chat_history", [])
            
            # DEBUG: Log system prompt length and chat history
            logger.info(f"🔍 [NODE 4a] system_prompt length: {len(system_prompt) if system_prompt else 0} chars")
            logger.info(f"🔍 [NODE 4a] chat_history count: {len(chat_history)} messages")
            if chat_history:
                logger.info(f"🔍 [NODE 4a] chat_history preview: {chat_history[:2]}")
            
            # Add completion instruction
            completion_rules = {
                "hu": "\n\n**VÁLASZADÁSI SZABÁLY:** Mindig fejezd be az utolsó mondatodat! Ne hagyj félbe gondolatot. Ha nincs elég hely, fogalmazz tömören.",
                "en": "\n\n**RESPONSE RULE:** Always finish your last sentence! Don't leave thoughts incomplete. If space is limited, be concise."
            }
            enhanced_prompt = system_prompt + completion_rules.get(user_lang, completion_rules["en"])
            
            # Build message history (if exists)
            messages = [SystemMessage(content=enhanced_prompt)]
            
            # Add ALL chat history for full context (not just last 5!)
            for msg in chat_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
            
            # Add current query
            messages.append(HumanMessage(content=query))
            
            # Store actual messages by session_id for prompt inspection
            session_id = state.get("session_id")
            if session_id:
                self._llm_messages_by_session[session_id] = messages
            
            # Call LLM
            response = self.llm.invoke(messages)
            answer = response.content
            
            logger.info(f"[NODE 4a] CHAT answer generated: {len(answer)} chars")
            
            # Track action
            actions = state.get("actions_taken", [])
            actions.append("CHAT")
            
            # Store result
            intermediate = state.get("intermediate_results", [])
            intermediate.append(answer)
            
            return {
                **state,
                "actions_taken": actions,
                "intermediate_results": intermediate
            }
        
        except Exception as e:
            logger.error(f"[NODE 4a] CHAT execution failed: {e}", exc_info=True)
            
            # Fallback answer
            answer = "Sorry, I encountered an error generating the response."
            
            actions = state.get("actions_taken", [])
            actions.append("CHAT_ERROR")
            
            intermediate = state.get("intermediate_results", [])
            intermediate.append(answer)
            
            return {
                **state,
                "actions_taken": actions,
                "intermediate_results": intermediate,
                "error": str(e)
            }
    
    def _execute_rag_search_node(self, state: ChatState) -> ChatState:
        """
        Node 4b: Execute RAG document search.
        
        Pipeline:
        1. Generate query embedding
        2. Search Qdrant with tenant filter
        3. Enrich with PostgreSQL chunk data
        4. Generate answer from context
        """
        logger.info("[NODE 4b: execute_rag_search] Executing")
        
        try:
            query = state["query"]
            tenant_id = state["user_context"]["tenant_id"]
            user_id = state["user_context"]["user_id"]
            system_prompt = state.get("system_prompt") or APPLICATION_SYSTEM_PROMPT
            user_lang = state["user_context"].get("user_language", "en")
            
            # Step 1: Generate embedding
            query_vector = self.embedding_service.generate_embedding(query)
            logger.info(f"[NODE 4b] Query embedding: {len(query_vector)} dimensions")
            
            # Step 2: Search Qdrant (with access control)
            search_results = self.qdrant_service.search_document_chunks(
                query_vector=query_vector,
                tenant_id=tenant_id,
                user_id=user_id,  # For private document access control
                limit=None,  # Uses system.ini TOP_K_DOCUMENTS
                score_threshold=None  # Uses system.ini MIN_SCORE_THRESHOLD
            )
            logger.info(f"[NODE 4b] Qdrant search: {len(search_results)} results")
            
            # Step 3: Enrich with PostgreSQL data
            chunk_start = time.time()
            chunk_ids = [result["chunk_id"] for result in search_results]
            chunks_data = self.chunk_repo.get_chunks_by_ids(chunk_ids)
            logger.info(f"[NODE 4b] Batch chunk retrieval: {len(chunks_data)} chunks in {time.time() - chunk_start:.2f}s")
            
            enriched_chunks: List[DocumentChunk] = []
            for result in search_results:
                chunk_id = result["chunk_id"]
                chunk_data = chunks_data.get(chunk_id)
                
                if chunk_data:
                    enriched_chunks.append({
                        "chunk_id": chunk_id,
                        "document_id": result["document_id"],
                        "content": chunk_data["content"],
                        "similarity_score": result["score"],
                        "metadata": {
                            "source_title": chunk_data.get("source_title", "Unknown"),
                            "chunk_index": chunk_data.get("chunk_index", 0)
                        }
                    })
            
            # Step 4: Generate answer if chunks found
            if enriched_chunks:
                answer = self._generate_answer_from_chunks(
                    query=query,
                    chunks=enriched_chunks,
                    system_prompt=system_prompt,
                    user_lang=user_lang
                )
                logger.info(f"[NODE 4b] RAG answer generated: {len(answer)} chars from {len(enriched_chunks)} chunks")
            else:
                # No chunks found - generate fallback
                answer = self._generate_no_documents_fallback(query, system_prompt, user_lang)
                logger.info(f"[NODE 4b] No chunks found - fallback answer generated")
            
            # Track action
            actions = state.get("actions_taken", [])
            actions.append("RAG")
            
            # Store result
            intermediate = state.get("intermediate_results", [])
            intermediate.append(answer)
            
            return {
                **state,
                "actions_taken": actions,
                "intermediate_results": intermediate,
                "retrieved_chunks": enriched_chunks
            }
        
        except Exception as e:
            logger.error(f"[NODE 4b] RAG execution failed: {e}", exc_info=True)
            
            # Error fallback
            answer = "Sorry, I encountered an error searching the documents."
            
            actions = state.get("actions_taken", [])
            actions.append("RAG_ERROR")
            
            intermediate = state.get("intermediate_results", [])
            intermediate.append(answer)
            
            return {
                **state,
                "actions_taken": actions,
                "intermediate_results": intermediate,
                "retrieved_chunks": [],
                "error": str(e)
            }
    
    def _execute_list_docs_node(self, state: ChatState) -> ChatState:
        """
        Node 4c: Execute document listing.
        """
        logger.info("[NODE 4c: execute_list_docs] Executing")
        
        try:
            user_ctx = state["user_context"]
            tenant_id = user_ctx["tenant_id"]
            user_id = user_ctx["user_id"]
            user_lang = user_ctx.get("user_language", "en")
            
            # Import here to avoid circular dependency
            from database.pg_init import get_documents_for_user
            
            # Fetch documents
            documents = get_documents_for_user(user_id=user_id, tenant_id=tenant_id)
            
            logger.info(f"[NODE 4c] Found {len(documents)} documents")
            
            if not documents:
                answer = "Jelenleg nincsenek feltöltött dokumentumok." if user_lang == "hu" else "No documents available."
            else:
                # Build formatted response
                if user_lang == "hu":
                    answer_lines = [f"**{len(documents)} feltöltött dokumentum:**\\n"]
                    for idx, doc in enumerate(documents, 1):
                        visibility_label = "Privát" if doc['visibility'] == 'private' else "Tenant"
                        created = doc['created_at'].strftime("%Y-%m-%d %H:%M") if hasattr(doc['created_at'], 'strftime') else str(doc['created_at'])
                        answer_lines.append(f"{idx}. **{doc['title']}**")
                        answer_lines.append(f"   - ID: {doc['id']}")
                        answer_lines.append(f"   - Láthatóság: {visibility_label}")
                        answer_lines.append(f"   - Feltöltve: {created}\\n")
                else:
                    answer_lines = [f"**{len(documents)} uploaded documents:**\\n"]
                    for idx, doc in enumerate(documents, 1):
                        visibility_label = "Private" if doc['visibility'] == 'private' else "Tenant-wide"
                        created = doc['created_at'].strftime("%Y-%m-%d %H:%M") if hasattr(doc['created_at'], 'strftime') else str(doc['created_at'])
                        answer_lines.append(f"{idx}. **{doc['title']}**")
                        answer_lines.append(f"   - ID: {doc['id']}")
                        answer_lines.append(f"   - Visibility: {visibility_label}")
                        answer_lines.append(f"   - Uploaded: {created}\\n")
                
                answer = "\\n".join(answer_lines)
            
            logger.info(f"[NODE 4c] LIST answer generated: {len(answer)} chars")
            
            # Track action
            actions = state.get("actions_taken", [])
            actions.append("LIST")
            
            # Store result
            intermediate = state.get("intermediate_results", [])
            intermediate.append(answer)
            
            return {
                **state,
                "actions_taken": actions,
                "intermediate_results": intermediate,
                "listed_documents": documents
            }
        
        except Exception as e:
            logger.error(f"[NODE 4c] LIST execution failed: {e}", exc_info=True)
            
            # Error fallback
            answer = "Sorry, I encountered an error listing the documents."
            
            actions = state.get("actions_taken", [])
            actions.append("LIST_ERROR")
            
            intermediate = state.get("intermediate_results", [])
            intermediate.append(answer)
            
            return {
                **state,
                "actions_taken": actions,
                "intermediate_results": intermediate,
                "listed_documents": [],
                "error": str(e)
            }
    
    def _execute_explicit_memory_node(self, state: ChatState) -> ChatState:
        """
        Node 4d: Store explicit memory request (LLM-based extraction + storage).
        
        Flow:
        1. LLM extracts the fact from query (e.g., "jegyezd meg hogy vegetáriánus vagyok" → "vegetáriánus vagyok")
        2. Generate embedding
        3. Store in PostgreSQL (memory_type='explicit_fact')
        4. Store in Qdrant (with ltm_id reference)
        5. Generate acknowledgment
        """
        logger.info("[NODE 4d: execute_explicit_memory] Storing explicit memory")
        
        try:
            from database.pg_init import insert_long_term_memory, update_long_term_memory_embedding
            
            query = state["query"]
            user_ctx = state["user_context"]
            user_lang = user_ctx.get("user_language", "hu")
            
            # Step 1: Extract fact using LLM
            logger.info(f"[NODE 4d] Extracting fact from query: '{query[:50]}...'")
            
            extraction_prompts = {
                "hu": """A felhasználó kéri, hogy jegyezd meg valamit. Extrald ki a TÉNYT, amit meg kell jegyezni.

FELHASZNÁLÓ KÉRÉSE: "{query}"

PÉLDÁK:
- "jegyezd meg hogy nem bírom a macskákat" → "nem bírom a macskákat"
- "emlékezz rá hogy vegetáriánus vagyok" → "vegetáriánus vagyok"
- "remember that I like pizza" → "I like pizza"
- "note that my birthday is May 5th" → "my birthday is May 5th"

Add vissza CSAK A TÉNYT, semmi mást (ne add vissza a "jegyezd meg" részt):""",
                "en": """The user is asking you to remember something. Extract the FACT that needs to be remembered.

USER REQUEST: "{query}"

EXAMPLES:
- "remember that I don't like cats" → "I don't like cats"
- "note that I'm vegetarian" → "I'm vegetarian"
- "jegyezd meg hogy allergias vagyok" → "allergias vagyok"
- "emlékezz rá hogy május 5-én van a szülinapom" → "május 5-én van a szülinapom"

Return ONLY THE FACT, nothing else (don't return the "remember" part):"""
            }
            
            extraction_prompt = extraction_prompts.get(user_lang, extraction_prompts["hu"])
            messages = [
                SystemMessage(content="You extract facts from user requests. Return only the extracted fact, no extra text."),
                HumanMessage(content=extraction_prompt.format(query=query))
            ]
            
            response = self.llm.invoke(messages)
            fact_raw = response.content.strip()
            
            logger.info(f"[NODE 4d] Extracted fact (raw): '{fact_raw}'")
            
            # Step 1.5: Spell-check and grammar correction
            correction_prompts = {
                "hu": """Javítsd ki a gépelési és helyesírási hibákat ebben a szövegben. 
Hiányzó szóközöket pótold. Ha nincs hiba, add vissza változatlanul.

Eredeti: "{text}"

FONTOS: Add vissza CSAK a javított szöveget, semmi mást (se kommentárt, se magyarázatot).

Javított:""",
                "en": """Fix typos and spelling errors in this text.
Add missing spaces. If there are no errors, return it unchanged.

Original: "{text}"

IMPORTANT: Return ONLY the corrected text, nothing else (no comments, no explanation).

Corrected:"""
            }
            
            correction_prompt = correction_prompts.get(user_lang, correction_prompts["hu"])
            correction_messages = [
                SystemMessage(content="You fix typos and grammar. Return only the corrected text, no extra words."),
                HumanMessage(content=correction_prompt.format(text=fact_raw))
            ]
            
            correction_response = self.llm.invoke(correction_messages)
            fact = correction_response.content.strip()
            
            if fact != fact_raw:
                logger.info(f"[NODE 4d] Spell-corrected: '{fact_raw}' → '{fact}'")
            else:
                logger.info(f"[NODE 4d] No corrections needed: '{fact}'")
            
            # Step 2: Generate embedding
            embedding = self.embedding_service.generate_embedding(fact)
            logger.info(f"[NODE 4d] Generated embedding: dim={len(embedding)}")
            
            # Step 3: Store in PostgreSQL (get ltm_id)
            ltm_id = insert_long_term_memory(
                tenant_id=user_ctx["tenant_id"],
                user_id=user_ctx["user_id"],
                session_id=state["session_id"],
                content=fact,
                memory_type="explicit_fact",
                qdrant_point_id=None
            )
            logger.info(f"[NODE 4d] Stored in PostgreSQL: ltm_id={ltm_id}")
            
            # Step 4: Store in Qdrant (with ltm_id reference)
            point_id = self.qdrant_service.upsert_long_term_memory(
                tenant_id=user_ctx["tenant_id"],
                user_id=user_ctx["user_id"],
                session_id=state["session_id"],
                memory_type="explicit_fact",
                ltm_id=ltm_id,
                content_full=fact,
                embedding_vector=embedding
            )
            logger.info(f"[NODE 4d] Stored in Qdrant: point_id={point_id}")
            
            # Step 5: Update PostgreSQL with qdrant_point_id
            update_long_term_memory_embedding(ltm_id, point_id)
            
            # Step 6: Generate acknowledgment (simple template, no LLM)
            if user_lang == "hu":
                answer = f"✓ Rendben, megjegyeztem: {fact}"
            else:
                answer = f"✓ Got it, I'll remember: {fact}"
            
            logger.info(f"[NODE 4d] ✓ Explicit memory stored successfully")
            
            # Track action
            actions = state.get("actions_taken", [])
            actions.append("EXPLICIT_MEMORY")
            
            # Store result
            intermediate = state.get("intermediate_results", [])
            intermediate.append(answer)
            
            # Add LTM source indicator
            ltm_source = {
                "type": "long_term_memory",
                "memory_type": "explicit_fact",
                "content": fact,
                "ltm_id": ltm_id
            }
            
            return {
                **state,
                "actions_taken": actions,
                "intermediate_results": intermediate,
                "explicit_fact": fact,
                "sources": [ltm_source]  # Indicate LTM source in response
            }
        
        except Exception as e:
            logger.error(f"[NODE 4d] ✗ Explicit memory storage failed: {e}", exc_info=True)
            
            # Error fallback
            user_lang = state["user_context"].get("user_language", "hu")
            if user_lang == "hu":
                answer = "Sajnálom, nem sikerült eltárolnom ezt az információt."
            else:
                answer = "Sorry, I couldn't store that information."
            
            actions = state.get("actions_taken", [])
            actions.append("EXPLICIT_MEMORY_ERROR")
            
            intermediate = state.get("intermediate_results", [])
            intermediate.append(answer)
            
            return {
                **state,
                "actions_taken": actions,
                "intermediate_results": intermediate,
                "sources": [],  # No sources on error
                "error": str(e)
            }
    
    def _agent_finalize_node(self, state: ChatState) -> ChatState:
        """
        Node 5: Finalize response - combines intermediate results.
        """
        logger.info("[NODE 5: agent_finalize] Finalizing response")
        
        intermediate = state.get("intermediate_results", [])
        
        if not intermediate:
            # No actions taken - should not happen
            final = "No response generated"
        elif len(intermediate) == 1:
            # Single action - use directly
            final = intermediate[0]
        else:
            # Multiple actions - combine (TODO: LLM combination in Phase 3)
            final = "\n\n".join(intermediate)
        
        # Extract sources
        sources = self._extract_sources(state)
        
        logger.info(f"[NODE 5] Final answer: {len(final)} chars, sources: {sources}")
        
        return {
            **state,
            "final_answer": final,
            "sources": sources
        }
    
    def _extract_sources(self, state: ChatState) -> List[Dict[str, Any]]:
        """
        Extract sources from state.
        
        Combines:
        - Existing sources (e.g., long-term memory)
        - Document sources from retrieved chunks
        """
        all_sources = []
        
        # 1. Preserve existing sources (e.g., LTM from execute_explicit_memory)
        existing = state.get("sources", [])
        if existing:
            all_sources.extend(existing)
        
        # 2. Add document sources from RAG retrieval
        chunks = state.get("retrieved_chunks", [])
        if chunks:
            # Create unique document sources with titles
            sources_map = {}
            for chunk in chunks:
                doc_id = chunk["document_id"]
                if doc_id not in sources_map:
                    title = chunk.get("metadata", {}).get("source_title", "Unknown Document")
                    sources_map[doc_id] = {"type": "document", "id": doc_id, "title": title}
            
            all_sources.extend(sources_map.values())
        
        return all_sources
    
    # ===== HELPER FUNCTIONS =====
    
    def _generate_answer_from_chunks(
        self,
        query: str,
        chunks: List[DocumentChunk],
        system_prompt: str,
        user_lang: str
    ) -> str:
        """
        Generate answer from retrieved document chunks using LLM.
        """
        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source_title = chunk["metadata"].get("source_title", "Unknown")
            score = chunk["similarity_score"]
            context_parts.append(
                f"[Document {i}: {source_title} (relevance: {score:.2f})]\\n{chunk['content']}"
            )
        
        context_text = "\\n\\n".join(context_parts)
        
        # Build user message (language-aware)
        prompt_templates = {
            "hu": """Az alábbi dokumentumok alapján válaszolj a kérdésre.

DOKUMENTUMOK:
{context}

KÉRDÉS: {query}

FONTOS VÁLASZADÁSI SZABÁLYOK:
- Adj világos és pontos választ a dokumentumok alapján
- Ha a válaszod hosszabb lesz, fogalmazz tömören és lényegre törően
- **MINDIG fejezd be az utolsó mondatodat!** Ne hagyj félbe gondolatot
- Ha nincs elég hely részletesebb kifejtésre, összegezd a lényeget
- Inkább egy teljes, rövidebb válasz, mint egy befejezetlen hosszabb

Ha valami nem világos vagy nincs elég információ, jelezd.""",
            "en": """Based on the following documents, answer the question.

DOCUMENTS:
{context}

QUESTION: {query}

IMPORTANT RESPONSE RULES:
- Provide a clear and concise answer based on the documents above
- If your answer will be long, be concise and to the point
- **ALWAYS finish your last sentence!** Don't leave thoughts incomplete
- If there's not enough space for details, summarize the key points
- Better a complete short answer than an incomplete long one

If something is unclear or there's not enough information, indicate that."""
        }
        
        template = prompt_templates.get(user_lang, prompt_templates["en"])
        user_message = template.format(context=context_text, query=query)
        
        # Call LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    def _generate_no_documents_fallback(
        self,
        query: str,
        system_prompt: str,
        user_lang: str
    ) -> str:
        """
        Generate fallback response when no documents found.
        """
        fallback_instruction = {
            "hu": """Nem találtam releváns dokumentumot a kérdéshez.

KÉRDÉS: {query}

Ha a felhasználó csak köszön, beszélget, vagy általános kérdést tesz fel (ami nem igényel specifikus dokumentum tartalmat), akkor válaszolj természetesen és barátságosan.

Ha viszont a kérdés konkrét információt kér (ami dokumentumban lenne), akkor mondd el, hogy nem találtál releváns dokumentumot, és javasolj más kulcsszavakat vagy dokumentum feltöltést.""",
            "en": """No relevant documents found for the query.

QUERY: {query}

If the user is just greeting, chatting, or asking a general question (that doesn't require specific document content), respond naturally and friendly.

However, if the question asks for specific information (that would be in documents), explain that you didn't find relevant documents and suggest trying different keywords or uploading more documents."""
        }
        
        instruction = fallback_instruction.get(user_lang, fallback_instruction["en"])
        user_message = instruction.format(query=query)
        
        # Call LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    # ===== PUBLIC INTERFACE =====
    
    def enable_websocket_broadcast(self, session_id: str, enabled: bool = True):
        """
        Enable/disable WebSocket broadcasting for a specific session.
        
        Args:
            session_id: Session to control
            enabled: Whether to broadcast state updates
        """
        self._enable_ws_broadcast[session_id] = enabled
        logger.info(f"WebSocket broadcast {'enabled' if enabled else 'disabled'} for session {session_id}")
    
    def execute(self, query: str, session_id: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute unified chat workflow.
        
        Args:
            query: User question
            session_id: Chat session ID
            user_context: Dict with tenant_id, user_id
        
        Returns:
            Dict with final_answer, sources, error (if any)
        """
        logger.info(f"[WORKFLOW] Starting unified execution: query='{query[:50]}...', session={session_id}, tenant={user_context.get('tenant_id')}")
        
        # Initialize state
        initial_state: ChatState = {
            "query": query,
            "session_id": session_id,
            "user_context": {
                "tenant_id": user_context["tenant_id"],
                "user_id": user_context["user_id"],
                "tenant_prompt": None,
                "user_prompt": None,
                "user_language": "en",
                "firstname": None,
                "lastname": None,
                "email": None,
                "role": None
            },
            "chat_history": [],
            "system_prompt": None,
            "system_prompt_cached": False,
            "cache_source": None,
            "next_action": None,
            "iteration_count": 0,
            "actions_taken": [],
            "retrieved_chunks": [],
            "listed_documents": [],
            "ltm_results": None,
            "intermediate_results": [],
            "final_answer": None,
            "sources": [],
            "error": None
        }
        
        # Execute workflow
        try:
            # Use stream mode to capture intermediate states for WebSocket broadcast
            final_state = None
            
            for event in self.graph.stream(initial_state):
                # event is a dict: {node_name: state_update}
                for node_name, state_update in event.items():
                    # Broadcast state if enabled for this session
                    if self._enable_ws_broadcast.get(session_id, False):
                        import asyncio
                        try:
                            asyncio.create_task(self._broadcast_state(node_name, state_update))
                        except RuntimeError:
                            # No event loop running (sync context), skip broadcast
                            pass
                    
                    final_state = state_update
            
            if not final_state:
                # Fallback to invoke if stream didn't work
                final_state = self.graph.invoke(initial_state)
            
            logger.info(f"[WORKFLOW] Execution complete: answer_len={len(final_state.get('final_answer', ''))}, sources={final_state.get('sources', [])}, actions={final_state.get('actions_taken', [])}")
            
            # Build prompt_details for frontend "Prompt" button
            prompt_details = None
            if final_state.get("system_prompt"):
                user_ctx = final_state.get("user_context", {})
                chat_history = final_state.get("chat_history", [])
                session_id = initial_state.get("session_id")
                actual_messages = self._llm_messages_by_session.get(session_id, [])
                
                # Get memory config
                config_service = get_config_service()
                short_term_limit = config_service.get_int('memory', 'SHORT_TERM_MEMORY_MESSAGES', default=30)
                short_term_scope = config_service.get('memory', 'SHORT_TERM_MEMORY_SCOPE', default='session')
                
                # Convert actual LLM messages to EXACT format for frontend prompt inspection
                # This is EXACTLY what was sent to the LLM - character by character
                actual_messages_formatted = []
                for msg in actual_messages:
                    msg_type = type(msg).__name__  # SystemMessage, HumanMessage, AIMessage
                    # CRITICAL: Use msg.content to get the exact string sent to LLM
                    actual_messages_formatted.append({
                        "type": msg_type,
                        "content": str(msg.content)  # Explicit string conversion for safety
                    })
                
                prompt_details = {
                    "system_prompt": final_state.get("system_prompt"),
                    "chat_history": chat_history,  # Show ALL messages that were fetched from DB
                    "current_query": initial_state.get("query"),
                    "system_prompt_cached": final_state.get("system_prompt_cached", False),
                    "cache_source": final_state.get("cache_source"),
                    "user_firstname": user_ctx.get("firstname"),
                    "user_lastname": user_ctx.get("lastname"),
                    "user_email": user_ctx.get("email"),
                    "user_role": user_ctx.get("role"),
                    "user_language": user_ctx.get("user_language"),
                    "chat_history_count": len(chat_history),
                    "actions_taken": final_state.get("actions_taken", []),
                    "short_term_memory_messages": short_term_limit,
                    "short_term_memory_scope": short_term_scope,
                    "actual_llm_messages": actual_messages_formatted  # ACTUAL messages sent to LLM!
                }
            
            # Get RAG parameters from config
            config = get_config_service()
            top_k = config.get("rag", "TOP_K_DOCUMENTS", 5)
            min_score = config.get("rag", "MIN_SCORE_THRESHOLD", 0.1)
            
            # Include RAG params if there are sources
            sources = final_state.get("sources", [])
            
            return {
                "final_answer": final_state.get("final_answer", ""),
                "sources": sources,
                "actions_taken": final_state.get("actions_taken", []),
                "prompt_details": prompt_details,
                "error": final_state.get("error"),
                "rag_params": {
                    "top_k": int(top_k),
                    "min_score_threshold": float(min_score)
                } if sources else None
            }
        
        except Exception as e:
            logger.error(f"[WORKFLOW] Execution failed: {e}", exc_info=True)
            return {
                "final_answer": f"Workflow execution error: {str(e)}",
                "sources": [],
                "actions_taken": [],
                "error": str(e)
            }
