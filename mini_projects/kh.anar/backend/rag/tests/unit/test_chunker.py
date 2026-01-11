from rag.chunking.chunker import DeterministicChunker


def test_chunker_basic():
    text = """This is a test document. " * 200
    c = DeterministicChunker(chunk_size=100, chunk_overlap=10)
    chunks = c.chunk("doc1", text)
    # deterministic: with these params we expect >1 chunks
    assert len(chunks) > 1
    # chunks should be contiguous and overlapping by overlap
    assert chunks[0].metadata["start"] == 0
    assert chunks[1].metadata["start"] == 100 - 10
    # ids deterministic
    assert chunks[0].chunk_id == "doc1:0"
    assert chunks[1].chunk_id == "doc1:1"
