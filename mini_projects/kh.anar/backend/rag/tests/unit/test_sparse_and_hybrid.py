from rag.retrieval.sparse import SparseRetriever
from rag.retrieval.hybrid import HybridRetriever
from rag.embeddings.embedder import HashEmbedder
from rag.retrieval.dense import DenseRetriever
from rag.config import default_config


def test_sparse_basic():
    s = SparseRetriever()
    chunks = [{"id": "d1:0", "text": "the quick brown fox"}, {"id": "d2:0", "text": "slow green turtle"}]
    s.add_chunks(chunks)
    res = s.query("quick fox", k=1)
    assert res[0]["id"] == "d1:0"


class DummyDense:
    def __init__(self):
        self.calls = []

    def query(self, embedding, k=5, filters=None):
        # return deterministic scores
        return [{"id": "d1:0", "score_vector": 0.9, "document": "the quick brown fox"}, {"id": "d2:0", "score_vector": 0.2, "document": "slow green turtle"}]


def test_hybrid_merge():
    dense = DummyDense()
    sparse = SparseRetriever()
    sparse.add_chunks([{"id": "d1:0", "text": "the quick brown fox"}, {"id": "d2:0", "text": "slow green turtle"}])
    hr = HybridRetriever(dense, sparse, default_config)
    emb = HashEmbedder().embed_text("quick fox")
    out = hr.retrieve(emb, "quick fox", k=2)
    assert out["decision"] == "hit"
    assert len(out["topk"]) >= 1
    # top should be d1:0
    assert out["topk"][0]["id"] == "d1:0"
