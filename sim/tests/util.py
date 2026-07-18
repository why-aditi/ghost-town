"""Test helpers: a deterministic offline embedder + isolated world factory.

ChromaDB's EphemeralClient shares global state across instances, so each test
world gets its own temp persistent dir. The fake embedder is a stable
bag-of-words hash — no ONNX model download, and word overlap drives cosine
distance so retrieval ranking is meaningful in tests.
"""
import re
import tempfile

from chromadb.api.types import EmbeddingFunction

_DIM = 64


def _vec(text: str) -> list[float]:
    v = [0.0] * _DIM
    for w in re.findall(r"[a-z]+", text.lower()):
        v[sum(map(ord, w)) % _DIM] += 1.0
    if not any(v):
        v[0] = 1.0
    return v


class FakeEmbed(EmbeddingFunction):
    """Stable bag-of-words embedder; subclasses chroma's base so it inherits
    the full non-legacy interface (default_space, get_config, ...)."""

    def __init__(self):
        pass

    def __call__(self, input):
        return [_vec(t) for t in input]

    @staticmethod
    def name() -> str:
        return "fake-hash"

    def get_config(self) -> dict:
        return {}

    @classmethod
    def build_from_config(cls, config) -> "FakeEmbed":
        return cls()


def new_world():
    """A seeded world with an isolated, offline memory store."""
    from sim.world import World
    return World.new(":memory:", memory_path=tempfile.mkdtemp(),
                     embedding_function=FakeEmbed())
