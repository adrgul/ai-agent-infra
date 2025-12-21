import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph.workflow import build_graph

async def main():
    graph = build_graph()
    
    test_inputs = [
        "Szeretnék szabadságot kivenni jövő héten.",     # Should be HR
        "Nem működik a VPN, mit tegyek?",               # Should be IT
        "Hogyan kell benyújtani a számlát?",            # Should be Finance
        "Mi a cég GDPR szabályzata?",                   # Should be Legal
        "Hol találom a marketing brand guide-ot?",      # Should be Marketing
        "Jó reggelt!",                                  # Should be General
    ]
    
    print("--- Starting Phase 2 Router Test ---")
    
    for text in test_inputs:
        print(f"\nUser Input: {text}")
        result = await graph.ainvoke({"input": text, "chat_history": []})
        domain = result.get("domain")
        response = result.get("final_response")
        print(f"-> Domain: {domain}")
        print(f"-> Response: {response}")
        
    print("\n--- Test Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
