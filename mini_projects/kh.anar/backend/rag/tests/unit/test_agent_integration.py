from rag.service import RAGService
from rag.embeddings.embedder import HashEmbedder
from rag.retrieval.sparse import SparseRetriever
from rag.retrieval.hybrid import HybridRetriever

from ..ingestion.ingester import Document
from rag.ingestion.ingester import Ingester
from ..retrieval.dense import DenseRetriever

from app.services.agent import AgentOrchestrator


class FakeDenseSimple:
    def __init__(self):
        self.storage = {}

    def add_chunks(self, chunks):
        for c in chunks:
            self.storage[c["id"]] = c

    def query(self, embedding, k=5, filters=None):
        # returns canary at top if exists
        res = []
        for _id, c in self.storage.items():
            score = 0.9 if "CANARY_TOKEN" in c["text"] else 0.1
            res.append({"id": _id, "score_vector": score, "document": c.get("text"), "metadata": c.get("metadata")})
        res.sort(key=lambda x: x["score_vector"], reverse=True)
        return res[:k]


def test_agent_kb_first_behavior():
    dense = FakeDenseSimple()
    sparse = SparseRetriever()
    embedder = HashEmbedder()
    ing = Ingester(dense, sparse, embedder, None)
    doc = Document(doc_id="doc-canary", title="Canary Doc", source="tests", doc_type="note", version="1", text="CANARY_TOKEN present to verify KB-first route.")
    ing.ingest(doc)

    class Cfg: k = 5; threshold = 0.2; w_dense = 0.7; w_sparse = 0.3
    hybrid = HybridRetriever(dense, sparse, Cfg())
    rag_service = RAGService(embedder, hybrid, Cfg())

    agent = AgentOrchestrator(rag_service=rag_service)
    state = {"user_id": "u1", "session_id": "s1", "query": "Where is CANARY_TOKEN?", "history": []}

    # Run the workflow synchronously (the graph invocation is async)
    import asyncio

    async def run_and_check():
        out = await agent.run(state)
        # after route_query, rag_context should be set
        assert "rag_telemetry" in out
        assert out["rag_telemetry"]["decision"] == "hit"
        assert out["rag_context"]

    asyncio.run(run_and_check())
