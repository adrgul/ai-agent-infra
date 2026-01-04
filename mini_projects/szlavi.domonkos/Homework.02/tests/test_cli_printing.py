from __future__ import annotations

from app.cli import CLI, Neighbor


class _DummyEmb:
    def get_embedding(self, text: str):
        return [0.0]


class _DummyStore:
    def add(self, id, text, embedding):
        pass

    def similarity_search(self, embedding, k=3):
        return [("id1", 0.0, "the same"), ("id2", 0.5, "similar 1")]


def test_print_results(capsys):
    cli = CLI(emb_service=_DummyEmb(), vector_store=_DummyStore())
    neighbors = [Neighbor(id="id1", distance=0.0, text="the same"), Neighbor(id="id2", distance=0.5, text="similar 1")]
    cli._print_results("myid", neighbors)
    out = capsys.readouterr().out
    assert "Stored prompt id:" in out
    assert "Retrieved nearest neighbors:" in out
    assert "the same" in out
