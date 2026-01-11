from rag.ingestion.ingester import Ingester, Document
from rag.embeddings.embedder import HashEmbedder
from rag.retrieval.sparse import SparseRetriever
from rag.retrieval.hybrid import HybridRetriever


class FakeDense:
    def __init__(self):
        self.storage = {}

    def add_chunks(self, chunks):
        for c in chunks:
            self.storage[c['id']] = c

    def query(self, embedding, k=5, filters=None):
        # filters may include metadata access_scope
        res = []
        for _id, c in self.storage.items():
            # respect filters: if access_scope provided, only return matching metadata
            if filters and filters.get('access_scope') and c.get('metadata', {}).get('access_scope') != filters.get('access_scope'):
                continue
            res.append({"id": _id, "score_vector": 0.9 if 'PRIVATE' in c['text'] else 0.1, "document": c['text'], "metadata": c['metadata']})
        res.sort(key=lambda x: x['score_vector'], reverse=True)
        return res[:k]


def test_rbac_filter_respected():
    dense = FakeDense()
    sparse = SparseRetriever()
    embedder = HashEmbedder()
    ing = Ingester(dense, sparse, embedder, None)

    doc_public = Document(doc_id='doc-pub', title='P', source='t', doc_type='note', version='1', access_scope='public', text='public content')
    doc_priv = Document(doc_id='doc-priv', title='Private', source='t', doc_type='note', version='1', access_scope='private', text='PRIVATE content')
    ing.ingest(doc_public)
    ing.ingest(doc_priv)

    class Cfg: k = 5; threshold = 0.2; w_dense = 0.7; w_sparse = 0.3
    hr = HybridRetriever(dense, sparse, Cfg())

    emb = embedder.embed_text('private')
    out_no_filter = hr.retrieve(emb, 'private', filters=None)
    # private doc should appear if no filters
    assert any('doc-priv' in h['id'] or h.get('metadata', {}).get('doc_id') == 'doc-priv' for h in out_no_filter['topk'])

    out_filtered = hr.retrieve(emb, 'private', filters={'access_scope': 'public'})
    # with public filter, private doc must not appear
    assert not any('doc-priv' in h['id'] or h.get('metadata', {}).get('doc_id') == 'doc-priv' for h in out_filtered['topk'])
