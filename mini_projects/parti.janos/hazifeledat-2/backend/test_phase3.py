import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph.workflow import build_graph

async def main():
    graph = build_graph()
    
    # Questions relating to our dummy documents + one unknown
    test_inputs = [
        "Hány nappal előre kell beadni a szabadságot?",           # HR (Matches hr_policy.md)
        "Mit tegyek ha nem megy a VPN?",                          # IT (Matches it_vpn_guide.md)
        "Mennyi a cafeteria keret?",                              # HR (Unknown - not in dummy docs)
        "Hogyan kell utalni?",                                    # Finance (Unknown domain for now)
    ]
    
    print("--- Starting Phase 3 RAG Test ---")
    
    for text in test_inputs:
        print(f"\nUser Input: {text}")
        result = await graph.ainvoke({"input": text, "chat_history": []})
        
        domain = result.get("domain")
        docs = result.get("retrieved_docs", [])
        response = result.get("final_response")
        
        print(f"-> Domain: {domain}")
        print(f"-> Docs found: {len(docs)}")
        print(f"-> Response: {response}")
        
    print("\n--- Test Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
