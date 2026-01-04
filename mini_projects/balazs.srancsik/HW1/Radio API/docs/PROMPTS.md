# AI Agent Prompts Documentation

This document describes the various prompts used throughout the AI Agent application and their purposes.

---

## Table of Contents
1. [System Prompt](#system-prompt)
2. [Decision Prompt](#decision-prompt)
3. [Final Response Prompt](#final-response-prompt)
4. [Name Detection Patterns](#name-detection-patterns)

---

## System Prompt

**Location:** `backend/services/agent.py` → `_build_system_prompt()`

**Purpose:** Establishes the AI assistant's identity, loads user preferences, and provides conversation context.

**Structure:**
```python
"""You are a helpful AI assistant with access to various tools.

User preferences:
- Name: {user_name}
- Language: {language}
- Default city: {city}
- {other_preferences}

Recent conversation history:
{last_10_messages}

Current workflow: {workflow_flow} (step {step}/{total})

Address the user by their name ({name}) when appropriate.
"""
```

**Key Features:**
- **Personalization:** Loads user name, language preference, default city
- **Context Awareness:** Includes last 10 messages from conversation history (truncated to 150 chars each)
- **Workflow Tracking:** Shows current workflow step if active
- **Dynamic Preferences:** Automatically includes any additional user preferences

**Usage:** This prompt is sent with EVERY LLM call to maintain consistency and personalization.

---

## Decision Prompt

**Location:** `backend/services/agent.py` → `_agent_decide_node()`

**Purpose:** Instructs the LLM to analyze the user's request and decide which tool to call next, or whether to provide a final answer.

**Structure:**
```python
"""
You must analyze the user's request and respond with ONLY a valid JSON object, nothing else.

Recent conversation context:
{last_5_messages}

Available tools:
- weather: Get weather forecast (params: city OR lat/lon) - ONLY provides current + 2 day future forecast, NO historical data
- geocode: Convert address to coordinates or reverse (params: address OR lat/lon)
- ip_geolocation: Get location from IP address (params: ip_address)
- fx_rates: Get currency exchange rates (params: base, target, optional date)
- crypto_price: Get cryptocurrency prices (params: symbol, fiat)
- create_file: Save text to a file (params: filename, content)
- search_history: Search past conversations (params: query)

User's original request: {user_message}

Tools already called with their arguments: {tools_called_list}

CRITICAL RULES:
1. NEVER call the same tool with the same arguments twice
2. If a tool was called and couldn't provide the data (e.g., historical weather), do NOT retry - move to final_answer
3. If the user asks for something a tool cannot do (like past weather data), explain the limitation in final_answer
4. If the user requested multiple DIFFERENT tasks, execute them ONE AT A TIME
5. Only use "final_answer" when ALL requested tasks are complete OR a task is impossible

Respond with ONLY this JSON structure (no other text, no markdown):
{
  "action": "call_tool",
  "tool_name": "TOOL_NAME_HERE",
  "arguments": {...},
  "reasoning": "brief explanation"
}

Examples:
- Weather: {"action": "call_tool", "tool_name": "weather", "arguments": {"city": "Budapest"}, "reasoning": "get weather forecast"}
- Create file: {"action": "call_tool", "tool_name": "create_file", "arguments": {"filename": "summary.txt", "content": "..."}, "reasoning": "save summary"}
- Final answer: {"action": "final_answer", "reasoning": "all tasks completed"}

IMPORTANT: The "action" field must ALWAYS be either "call_tool" or "final_answer" - NEVER use a tool name as the action!
"""
```

**Key Features:**
- **Strict JSON Output:** Enforces structured response format
- **Tool Deduplication:** Shows `tools_called` with full arguments to prevent duplicate calls
- **Tool Limitations:** Explicitly states what each tool CAN'T do (e.g., no historical weather)
- **Multi-step Guidance:** Instructs to handle one task at a time
- **Examples:** Provides concrete examples to prevent format errors
- **Safety Rules:** Prevents infinite loops and wasteful API calls

**Output Format:**
```json
{
  "action": "call_tool" | "final_answer",
  "tool_name": "weather" | "geocode" | "ip_geolocation" | "fx_rates" | "crypto_price" | "create_file" | "search_history",
  "arguments": {
    // Tool-specific parameters
  },
  "reasoning": "explanation of why this action was chosen"
}
```

**Usage:** Called in the `agent_decide` node before each tool execution to determine next action.

---

## Final Response Prompt

**Location:** `backend/services/agent.py` → `_agent_finalize_node()`

**Purpose:** Generates a natural language response to the user based on conversation history and tool results.

**Structure:**
```python
"""
Generate a natural language response to the user based on the conversation history and any tool results.

Conversation:
{last_10_messages_with_system_messages}

Important:
- Respond in {language} language
- Be helpful and conversational
- Use information from tool results if available
- Keep the response concise but complete
"""
```

**Key Features:**
- **Language Awareness:** Uses user's preferred language (from memory.preferences)
- **Full Context:** Includes last 10 messages (HumanMessage, AIMessage, SystemMessage)
- **Tool Results:** System messages contain tool execution results
- **Natural Output:** No JSON structure - pure conversational response

**Usage:** Called in the `agent_finalize` node after all tool executions are complete.

---

## Name Detection Patterns

**Location:** `backend/services/chat_service.py` → `_check_profile_updates()`

**Purpose:** Automatically extract user names from messages to update user profiles.

**Patterns:**
```python
name_patterns = [
    r"(?:my name is|call me|i am|i'm)\s+([A-Z][a-záéíóöőúüű][a-záéíóöőúüű]+)",  # English
    r"(?:a nevem|hívnak|vagyok|én vagyok)\s+([A-Z][a-záéíóöőúüű][a-záéíóöőúüű]+)",  # Hungarian
    r"([A-Z][a-záéíóöőúüű]+)\s+vagyok",  # "[Name] vagyok"
    r"(?:szia|hello|hi|helló)\s+([A-Z][a-záéíóöőúüű][a-záéíóöőúüű]+)",  # "Szia [Name]"
    r"^([A-Z][a-záéíóöőúüű][a-záéíóöőúüű]+)\s+(?:here|itt|speaking)",  # "[Name] here/itt"
]
```

**Examples Matched:**
- ✅ "My name is Maria" → extracts "Maria"
- ✅ "A nevem János" → extracts "János"
- ✅ "Péter vagyok" → extracts "Péter"
- ✅ "Szia Maria" → extracts "Maria"
- ✅ "Anna itt" → extracts "Anna"

**Exclusion List:**
```python
excluded_words = [
    'szia', 'hello', 'helló', 'hi', 'hey', 'hola', 
    'budapest', 'hogyan', 'segíthetek'
]
```

**Key Features:**
- **Bilingual:** Supports English and Hungarian patterns
- **Case Sensitivity:** Requires proper noun capitalization
- **Character Support:** Handles Hungarian accented characters (áéíóöőúüű)
- **Filtering:** Excludes common words that aren't names

**Usage:** Called after every user message to automatically update user profile with detected names.

---

## Prompt Engineering Best Practices Used

### 1. **Strict Output Format**
- Decision prompt enforces JSON-only output
- Includes explicit examples to guide LLM
- Warns against common formatting mistakes

### 2. **Context Management**
- System prompt includes last 10 messages (150 char truncated)
- Decision prompt includes last 5 messages (100 char truncated)
- Balances context richness with token efficiency

### 3. **Deduplication Logic**
- Shows full tool history with arguments: `weather(city=Budapest)`
- Prevents infinite loops by tracking what's been called
- Explicit instruction: "NEVER call the same tool with the same arguments twice"

### 4. **Tool Limitations**
- Explicitly states what tools CAN'T do
- Example: "weather - ONLY provides current + 2 day future forecast, NO historical data"
- Prevents wasted API calls and user frustration

### 5. **Multi-step Guidance**
- Clear instruction to handle one task at a time
- Shows which tasks are already complete via tools_called
- Defines when to use final_answer vs. call_tool

### 6. **Safety Mechanisms**
- MAX_ITERATIONS = 10 to prevent infinite loops
- recursion_limit = 50 in workflow execution
- Forces final_answer when iteration limit reached

### 7. **Personalization**
- User name, language, city loaded from memory
- Recent conversation history provides context continuity
- "Address the user by their name when appropriate"

---

## Prompt Flow Diagram

```
User Input
    ↓
System Prompt (identity + preferences + history)
    ↓
Decision Prompt (tools + rules + JSON format)
    ↓
Tool Execution (if action == "call_tool")
    ↓
[Loop back to Decision Prompt if more tasks]
    ↓
Final Response Prompt (conversation + tool results)
    ↓
Natural Language Response to User
```

---

## Related Files

- **Agent Logic:** `backend/services/agent.py`
- **Chat Service:** `backend/services/chat_service.py`
- **Domain Models:** `backend/domain/models.py` (Memory, Message, ToolCall)
- **Architecture:** `docs/ARCHITECTURE.md`
- **LangGraph Nodes:** `docs/LANGGRAPH_NODES_HU.md`

---

## Summary

The application uses **4 main prompt types**:

1. **System Prompt** - Identity, preferences, conversation context (used in ALL LLM calls)
2. **Decision Prompt** - Structured JSON decision making for tool selection
3. **Final Response Prompt** - Natural language generation based on tool results
4. **Name Detection Patterns** - Regex patterns for automatic profile updates

All prompts are designed with:
- Clear instructions and examples
- Deduplication logic to prevent waste
- Multi-language support (English/Hungarian)
- Safety mechanisms (iteration limits, tool limitations)
- Context awareness (conversation history, user preferences)
