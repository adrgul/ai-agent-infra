import json
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Document:
    """Adatmodell egyetlen dokumentum reprezentálására."""
    id: int
    title: str
    content: str
    category: str
    tags: List[str]

class KnowledgeBase:
    """
    Kezeli a dokumentumok betöltését és a keresést.
    Szimulálja egy Vector Store működését egyszerű kulcsszavas kereséssel.
    """

    def __init__(self, db_path: str):
        """
        Inicializálja a tudásbázist.
        
        Args:
            db_path (str): A JSON adatbázis fájl elérési útja.
        """
        self.db_path = db_path
        self.documents: List[Document] = []
        self._load_data()

    def _load_data(self) -> None:
        """Betölti az adatokat a JSON fájlból a memóriába."""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    # Átalakítjuk a nyers dict-et Document objektummá
                    doc = Document(
                        id=item['id'],
                        title=item['title'],
                        content=item['content'],
                        category=item['category'],
                        tags=item['tags']
                    )
                    self.documents.append(doc)
            print(f"✅ Tudásbázis betöltve: {len(self.documents)} dokumentum.")
        except FileNotFoundError:
            print(f"❌ Hiba: A fájl nem található: {self.db_path}")
            self.documents = []

    def search(self, query: str) -> List[Document]:
        """
        Egyszerű keresést hajt végre a címben, tartalomban és a tagekben.
        
        Args:
            query (str): A keresett kifejezés.
            
        Returns:
            List[Document]: A találatok listája.
        """
        query = query.lower()
        results = []

        for doc in self.documents:
            # Keresés a címben, tartalomban és a címkék között
            if (query in doc.title.lower() or 
                query in doc.content.lower() or 
                any(query in tag.lower() for tag in doc.tags)):
                results.append(doc)
        
        return results

    def get_by_category(self, category: str) -> List[Document]:
        """Visszaadja egy adott kategória összes dokumentumát (Routing előkészítés)."""
        return [doc for doc in self.documents if doc.category.lower() == category.lower()]