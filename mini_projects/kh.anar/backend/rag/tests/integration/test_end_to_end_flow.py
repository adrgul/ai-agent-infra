from rag.embeddings.embedder import HashEmbedder
from rag.retrieval.sparse import SparseRetriever
from rag.retrieval.hybrid import HybridRetriever
from rag.ingestion.ingester import Ingester, Document
from rag.service import RAGService
from rag.citations import map_citations


def test_end_to_end_chain():
    dense = type("FakeDense", (), {"storage": {}, "add_chunks": lambda self, chunks: [self.storage.__setitem__(c['id'], c) for c in chunks], "query": lambda self, emb, k=5, filters=None: [{"id": _id, "score_vector": (0.9 if "secret" in c['text'] else 0.1), "document": c['text'], "metadata": c['metadata']} for _id, c in self.storage.items()]})()
    sparse = SparseRetriever()
    embedder = HashEmbedder()
    ing = Ingester(dense, sparse, embedder, None)
    doc = Document(doc_id="doc1", title="Secret Doc", source="tests", doc_type="note", version="1", text="This document contains the secret phrase: SECRET_PHRASE.")
    ing.ingest(doc)

    class Cfg: k = 5; threshold = 0.2; w_dense = 0.7; w_sparse = 0.3
    hybrid = HybridRetriever(dense, sparse, Cfg())
    service = RAGService(embedder, hybrid, Cfg())

    telemetry = service.route_and_retrieve("secret phrase", {})
    assert telemetry["decision"] == "hit"
    # synthesize an answer that includes topk[0].document
    answer = f"Found in docs: {telemetry['topk'][0]['document']}"
    cited = map_citations(answer, telemetry['topk'])
    assert cited
    assert cited[0]["doc_id"] == "doc1"
