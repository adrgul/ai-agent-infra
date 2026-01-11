from rag.retrieval.hybrid import HybridRetriever


class DummyDenseLow:
    def query(self, embedding, k=5, filters=None):
        return [{"id": "d1:0", "score_vector": 0.05, "document": "doc low"}]


class DummySparseLow:
    def __init__(self):
        pass

    def query(self, query, k=5, filter_ids=None):
        return [{"id": "d1:0", "score_sparse": 0.02, "document": "doc low"}]


def test_hybrid_no_hit_due_threshold():
    dense = DummyDenseLow()
    sparse = DummySparseLow()

    class Cfg:
        k = 5
        threshold = 0.5
        w_dense = 0.7
        w_sparse = 0.3

    hr = HybridRetriever(dense, sparse, Cfg())
    out = hr.retrieve([], "something")
    assert out["decision"] == "no_hit"
    assert out["topk"]
