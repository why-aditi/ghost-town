"""Per-agent memory streams on ChromaDB + the retrieval score (PRD 6.3).

Storage/retrieval only — importance is scored by the LLM in remember.py and
passed in. The ranking math (`rank_memories`) is a pure function, unit-tested
with fixed distances so it never needs a real embedding model.
"""
import chromadb

from sim import config


def retrieval_score(relevance: float, recency: float, importance01: float,
                    alpha=config.ALPHA, beta=config.BETA, gamma=config.GAMMA) -> float:
    """The Stanford-style weighted sum. All inputs in [0, 1]."""
    return alpha * relevance + beta * recency + gamma * importance01


def rank_memories(cands: list[dict], now_tick: int, k: int) -> list[dict]:
    """Score candidate memories and return the top-k (highest score first).

    Each candidate: {text, type, tick, importance, distance} (cosine distance).
    Adds relevance/recency/score fields to each returned dict.
    """
    for c in cands:
        c["relevance"] = max(0.0, 1.0 - c["distance"])          # cosine dist -> similarity
        c["recency"] = config.RECENCY_DECAY ** max(0, now_tick - c["tick"])
        c["score"] = retrieval_score(c["relevance"], c["recency"], c["importance"] / 10)
    return sorted(cands, key=lambda c: c["score"], reverse=True)[:k]


class MemoryStore:
    """One cosine ChromaDB collection per agent. `path=None` -> ephemeral
    (tests/`:memory:` runs). `embedding_function=None` -> Chroma default
    (local ONNX MiniLM); tests inject a fast deterministic embedder."""

    def __init__(self, path: str | None = None, embedding_function=None,
                 collection_prefix: str = ""):
        self.client = chromadb.PersistentClient(path) if path else chromadb.EphemeralClient()
        self.ef = embedding_function
        self.prefix = collection_prefix  # tests use a unique prefix for isolation
        self._n = 0  # id counter (uniqueness only; not ranking-relevant)

    def _coll(self, agent_id: str):
        return self.client.get_or_create_collection(
            f"{self.prefix}memories_{agent_id}", metadata={"hnsw:space": "cosine"},
            embedding_function=self.ef)

    def add(self, agent_id: str, text: str, mtype: str, tick: int, importance: int) -> None:
        self._n += 1
        self._coll(agent_id).add(
            ids=[f"{agent_id}-{tick}-{self._n}"], documents=[text],
            metadatas=[{"type": mtype, "tick": tick, "importance": int(importance)}])

    def retrieve(self, agent_id: str, query: str, k: int, now_tick: int) -> list[dict]:
        coll = self._coll(agent_id)
        n = coll.count()
        if n == 0:
            return []
        r = coll.query(query_texts=[query], n_results=min(config.FETCH_N, n),
                       include=["documents", "metadatas", "distances"])
        cands = [
            {"text": doc, "type": md["type"], "tick": md["tick"],
             "importance": md["importance"], "distance": dist}
            for doc, md, dist in zip(r["documents"][0], r["metadatas"][0], r["distances"][0])
        ]
        return rank_memories(cands, now_tick, k)

    def all(self, agent_id: str) -> list[dict]:
        g = self._coll(agent_id).get(include=["documents", "metadatas"])
        rows = [
            {"text": doc, "type": md["type"], "tick": md["tick"], "importance": md["importance"]}
            for doc, md in zip(g["documents"], g["metadatas"])
        ]
        return sorted(rows, key=lambda m: m["tick"])
