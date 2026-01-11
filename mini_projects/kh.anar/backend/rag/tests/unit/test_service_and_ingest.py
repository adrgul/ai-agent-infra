from rag.ingestion.ingester import Ingester, Document
from rag.embeddings.embedder import HashEmbedder
from rag.retrieval.sparse import SparseRetriever
from rag.retrieval.hybrid import HybridRetriever


class FakeDense:
    def __init__(self):
        self.storage = {}

    def add_chunks(self, chunks):
        for c in chunks:
            self.storage[c["id"]] = c

    def query(self, embedding, k=5, filters=None):
        # simple similarity: pick ids we have
        results = []
        for _id, c in self.storage.items():
            results.append({"id": _id, "score_vector": 0.8 if "CANARY_TOKEN" in c["text"] else 0.1, "document": c.get("text"), "metadata": c.get("metadata")})
        results.sort(key=lambda x: x["score_vector"], reverse=True)
        return results[:k]


def test_ingest_and_canary_retrieval():
    dense = FakeDense()
    sparse = SparseRetriever()
    embedder = HashEmbedder()
    ing = Ingester(dense, sparse, embedder, None)
    doc = Document(doc_id="doc-canary", title="Canary Doc", source="tests", doc_type="note", version="1", text="This doc contains CANARY_TOKEN which should be retrieved.")
    ingested = ing.ingest(doc)
    assert any("CANARY_TOKEN" in c["text"] for c in ingested)

    hr = HybridRetriever(dense, sparse, embedder=None)  # config will be injected in next test
    # we need a config-like object with k, threshold, w_dense, w_sparse
    class Cfg: k = 5; threshold = 0.2; w_dense = 0.7; w_sparse = 0.3
    cfg = Cfg()
    hr = HybridRetriever(dense, sparse, cfg)
    emb = HashEmbedder().embed_text("canary token")
    out = hr.retrieve(emb, "canary token")
    assert out["decision"] == "hit"
    assert any("doc-canary" in h["id"] for h in out["topk"]) or any(h.get("metadata", {}).get("doc_id") == "doc-canary" for h in out["topk"])