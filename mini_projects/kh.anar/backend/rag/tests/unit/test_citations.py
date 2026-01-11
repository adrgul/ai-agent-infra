from rag.citations import map_citations


def test_map_citations_simple():
    hits = [{"id": "d1:0", "document": "This is a part of document mentioning X.", "metadata": {"doc_id": "d1", "title": "Doc1"}}, {"id": "d2:0", "document": "Other content.", "metadata": {"doc_id": "d2", "title": "Doc2"}}]
    answer = "As seen in Doc1: This is a part of document mentioning X."
    cited = map_citations(answer, hits)
    assert any(c["id"] == "d1:0" for c in cited)
