"""Memory writes. Phase 1: plain observation/conversation records, fixed
importance. Day 3 adds LLM importance scoring and ChromaDB embedding.
"""
from sim.models import Dialogue, MemoryEntry


def remember(world, moves: dict[str, str], dialogues: list[Dialogue],
             tick: int) -> list[MemoryEntry]:
    """Write one observation per mover + one conversation memory per participant."""
    written: list[MemoryEntry] = []

    for agent_id, destination in moves.items():
        text = f"I went to the {destination}."
        world.add_memory(agent_id, text, "observation", importance=1)
        written.append(MemoryEntry(agent_id=agent_id, text=text,
                                   type="observation", importance=1, tick=tick))

    for d in dialogues:
        for agent_id in d.participants:
            other = [p for p in d.participants if p != agent_id][0]
            text = f"I talked with {other} in the {d.zone}."
            world.add_memory(agent_id, text, "conversation", importance=2)
            written.append(MemoryEntry(agent_id=agent_id, text=text,
                                       type="conversation", importance=2, tick=tick))
    return written
