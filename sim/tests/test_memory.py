"""Retrieval scoring math (fixed inputs, no embeddings) + a chroma round-trip
with the fake embedder."""
from sim import config
from sim.phases.memory import MemoryStore, rank_memories, retrieval_score
from sim.tests.util import FakeEmbed, unique_prefix


def _store() -> MemoryStore:
    return MemoryStore(embedding_function=FakeEmbed(), collection_prefix=unique_prefix())


def test_retrieval_score_formula():
    # score = 1.0*rel + 0.8*rec + 0.6*imp01
    s = retrieval_score(relevance=1.0, recency=1.0, importance01=1.0)
    assert abs(s - (config.ALPHA + config.BETA + config.GAMMA)) < 1e-9
    assert abs(retrieval_score(0.5, 0.5, 0.5) - (1.0*0.5 + 0.8*0.5 + 0.6*0.5)) < 1e-9


def test_recency_decay_favours_recent():
    now = 10
    cands = [
        {"text": "old", "type": "o", "tick": 0, "importance": 5, "distance": 0.0},
        {"text": "new", "type": "o", "tick": 10, "importance": 5, "distance": 0.0},
    ]
    ranked = rank_memories(cands, now_tick=now, k=2)
    assert ranked[0]["text"] == "new"                       # same rel+imp, newer wins
    assert abs(ranked[1]["recency"] - config.RECENCY_DECAY ** 10) < 1e-9


def test_relevance_dominates_over_importance():
    now = 0
    cands = [
        {"text": "relevant", "type": "o", "tick": 0, "importance": 1, "distance": 0.0},
        {"text": "important-but-off", "type": "o", "tick": 0, "importance": 10, "distance": 0.9},
    ]
    ranked = rank_memories(cands, now, k=1)
    assert ranked[0]["text"] == "relevant"  # rel=1.0 beats rel=0.1 even at max importance


def test_add_retrieve_roundtrip():
    store = _store()
    store.add("odette", "the old mine collapse was no accident", "observation", 0, 9)
    store.add("odette", "i drew water from the well this morning", "observation", 1, 2)
    top = store.retrieve("odette", "what happened at the mine", k=1, now_tick=1)
    assert top and "mine" in top[0]["text"]
    assert "score" in top[0] and "relevance" in top[0]


def test_retrieve_empty_collection():
    store = _store()
    assert store.retrieve("nobody", "anything", k=3, now_tick=0) == []
