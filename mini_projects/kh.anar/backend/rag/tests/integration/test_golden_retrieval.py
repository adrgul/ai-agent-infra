from rag.embeddings.embedder import HashEmbedder
from rag.retrieval.sparse import SparseRetriever
from rag.retrieval.hybrid import HybridRetriever
from rag.ingestion.ingester import Ingester, Document


def test_golden_retrieval_20_canaries():
    dense = type("FakeDense", (), {"storage": {}, "add_chunks": lambda self, chunks: [self.storage.__setitem__(c['id'], c) for c in chunks], "query": lambda self, emb, k=5, filters=None: [{"id": _id, "score_vector": (0.99 if "CANARY_" in c['text'] else 0.1), "document": c['text'], "metadata": c['metadata']} for _id, c in self.storage.items()]})()
    sparse = SparseRetriever()
    embedder = HashEmbedder()
    ing = Ingester(dense, sparse, embedder, None)

    # create 20 canary docs
    for i in range(20):
        token = f"CANARY_{i}"
        doc = Document(doc_id=f"doc{i}", title=f"Doc {i}", source="tests", doc_type="note", version="1", text=f"This document contains {token} for retrieval testing.")
        ing.ingest(doc)

    class Cfg: k = 5; threshold = 0.2; w_dense = 0.7; w_sparse = 0.3
    hr = HybridRetriever(dense, sparse, Cfg())

    # test each token is retrieved in top-k
    failures = []
    for i in range(20):
        q = f"which doc has CANARY_{i}"
        emb = embedder.embed_text(q)
        out = hr.retrieve(emb, q, k=5)
        hit_ids = [h["id"] for h in out["topk"]]
        if not any(str(i) in hid for hid in hit_ids):
            failures.append((i, hit_ids))

    assert not failures, f"Some canaries not retrieved: {failures}"
