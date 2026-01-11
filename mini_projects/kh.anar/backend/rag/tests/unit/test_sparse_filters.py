from rag.retrieval.sparse import SparseRetriever


def test_sparse_filtering_by_ids():
    s = SparseRetriever()
    chunks = [
        {"id": "d1:0", "text": "apple orange"},
        {"id": "d2:0", "text": "banana pear"},
    ]
    s.add_chunks(chunks)
    res_all = s.query("apple", k=10)
    assert len(res_all) == 2
    res_filt = s.query("apple", k=10, filter_ids=["d1:0"])
    assert len(res_filt) == 1
    assert res_filt[0]["id"] == "d1:0"