from typing import Literal, Optional, Dict, Any
import json
from langchain_core.prompts import ChatPromptTemplate
from services.llm import get_llm

# Defined domains
DOMAINS = Literal["hr", "it", "finance", "legal", "marketing", "general"]

class RouterService:
    def __init__(self):
        self.llm = get_llm(model="gpt-4o", temperature=0)
        self.system_prompt = """You are an intelligent organizational router. 
Your job is to analyze the user's query and determine:
1. **Domain**: (hr, it, finance, legal, marketing, general)
2. **Intent**: 
    - `query`: The user is asking for information (e.g., "How to...", "What is...").
    - `action`: The user wants to perform an action (e.g., "Open a ticket", "Check my balance", "Book vacation").
3. **Tool**: If intent is `action`, select the appropriate tool:
    - `create_jira_ticket`: For IT issues, bug reports, access requests.
    - `check_vacation_balance`: For checking remaining holiday days.
    - `get_country_info`: If the user asks for information *about* a country (e.g., "Tell me about Hungary", "What is the capital of France?").
    - `none`: If no specific tool matches or if intent is `query` for which no tool is listed.

Output a JSON object ONLY:
{{
  "domain": "...",
  "intent": "query" | "action",
  "tool": "..." | "none",
  "tool_args": {{ ... }} // Extract arguments if action (e.g. summary for ticket)
}}
"""

    async def route_query(self, query: str) -> Dict[str, Any]:
        """
        Classifies the query into domain and intent.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", "{query}")
        ])
        
        chain = prompt | self.llm
        
        response = await chain.ainvoke({"query": query})
        content = response.content.strip()
        
        # Clean up markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            print(f"Error decoding JSON from router: {content}")
            return {"domain": "general", "intent": "query", "tool": "none"}

