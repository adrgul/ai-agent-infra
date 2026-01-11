import json
from pathlib import Path
from rag.embeddings.embedder import HashEmbedder
from rag.retrieval.sparse import SparseRetriever
from rag.retrieval.hybrid import HybridRetriever
from rag.ingestion.ingester import Ingester, Document


def test_snapshot_topk_matches_fixture(tmp_path):
    dense = type("FakeDense", (), {"storage": {}, "add_chunks": lambda self, chunks: [self.storage.__setitem__(c['id'], c) for c in chunks], "query": lambda self, emb, k=5, filters=None: [{"id": _id, "score_vector": (0.9 if i < 3 else 0.1), "document": c['text'], "metadata": c['metadata']} for i, (_id, c) in enumerate(self.storage.items())]})()
    sparse = SparseRetriever()
    embedder = HashEmbedder()
    ing = Ingester(dense, sparse, embedder, None)

    for i in range(5):
        doc = Document(doc_id=f"doc{i}", title=f"Doc {i}", source="tests", doc_type="note", version="1", text=f"Text for doc {i}")
        ing.ingest(doc)

    class Cfg: k = 5; threshold = 0.2; w_dense = 0.7; w_sparse = 0.3
    hr = HybridRetriever(dense, sparse, Cfg())
    emb = embedder.embed_text("doc")
    out = hr.retrieve(emb, "doc", k=5)
    top_ids = [h["id"] for h in out["topk"]][:3]

    fixture_path = Path(__file__).parent / "../fixtures/snapshots/golden_topk.json"
    expected = json.loads(fixture_path.read_text())
    assert top_ids == expected
