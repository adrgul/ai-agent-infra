import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph.workflow import build_graph

async def main():
    graph = build_graph()
    
    test_inputs = [
        "Hány nap szabadságom maradt?",                               # Intent: Action, Tool: check_vacation_balance
        "A VPN nem működik, kérek egy jegyet.",                      # Intent: Action, Tool: create_jira_ticket
        "Szeretnék IT segítséget kérni, nem megy a monitorom.",       # Intent: Action, Tool: create_jira_ticket
        "Hány nappal előre kell beadni a szabadságot?",              # Intent: Query, Domain: HR (Should be RAG)
    ]
    
    print("--- Starting Phase 4 Tool Automation Test ---")
    
    for text in test_inputs:
        print(f"\nUser Input: {text}")
        result = await graph.ainvoke({"input": text, "chat_history": []})
        
        domain = result.get("domain")
        intent = result.get("intent")
        tool = result.get("tool_name")
        response = result.get("final_response")
        
        print(f"-> Domain: {domain}")
        print(f"-> Intent: {intent}")
        if tool and tool != "none":
            print(f"-> Tool: {tool}")
        print(f"-> Response: {response}")
        
    print("\n--- Test Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
