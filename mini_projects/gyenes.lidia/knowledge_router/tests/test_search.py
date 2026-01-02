import pytest
import os
from src.document_store import KnowledgeBase, Document

# Mock (kamu) adatbázis fájl létrehozása teszteléshez
TEST_DB_PATH = "test_db.json"

@pytest.fixture
def kb_setup():
    """Létrehoz egy ideiglenes adatbázist a tesztek előtt, majd törli utána."""
    import json
    test_data = [
        {"id": 1, "title": "Test HR Doc", "content": "Vacation info", "category": "HR", "tags": ["holiday"]},
        {"id": 2, "title": "Test IT Doc", "content": "Server error", "category": "IT", "tags": ["server"]}
    ]
    with open(TEST_DB_PATH, 'w') as f:
        json.dump(test_data, f)
    
    # Példányosítjuk a KnowledgeBase-t
    kb = KnowledgeBase(TEST_DB_PATH)
    yield kb # Itt fut le a teszt
    
    # Takarítás (Tear down)
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_load_documents(kb_setup):
    """Teszteli, hogy helyesen betöltődnek-e a dokumentumok."""
    assert len(kb_setup.documents) == 2
    assert kb_setup.documents[0].title == "Test HR Doc"

def test_search_functionality(kb_setup):
    """Teszteli a keresési logikát."""
    # Keresés tartalom alapján
    results = kb_setup.search("Vacation")
    assert len(results) == 1
    assert results[0].category == "HR"

    # Keresés, ami nem ad találatot
    results_empty = kb_setup.search("Banana")
    assert len(results_empty) == 0

def test_category_filter(kb_setup):
    """Teszteli a kategória szerinti szűrést."""
    it_docs = kb_setup.get_by_category("IT")
    assert len(it_docs) == 1
    assert it_docs[0].title == "Test IT Doc"