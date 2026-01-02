import os
import sys

# Hozzáadjuk a src mappát az útvonalhoz, hogy működjön az import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.document_store import KnowledgeBase

def main():
    # Útvonal beállítása a data mappához
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, 'data', 'knowledge_base.json')

    # Osztály példányosítása
    kb = KnowledgeBase(json_path)

    print("\n🔍 --- Knowledge Router: Dokumentum Kereső ---")
    print("Írj be egy témát (pl. 'vpn', 'szabadság', 'számla'). Kilépés: 'exit'")

    while True:
        user_input = input("\nKeresés: ").strip()
        
        if user_input.lower() == 'exit':
            print("👋 Viszlát!")
            break
            
        if not user_input:
            continue

        # Keresés futtatása
        results = kb.search(user_input)

        if results:
            print(f"\n✅ Találatok ({len(results)} db):")
            for doc in results:
                print(f"   📂 [{doc.category}] {doc.title}")
                print(f"      📄 {doc.content[:100]}...") # Csak az első 100 karakter
        else:
            print("❌ Nincs találat a tudásbázisban.")

if __name__ == "__main__":
    main()