"""Tick phase ordering + determinism under a fixed seed."""
import random

from sim.tick import GRAPH, run_tick
from sim.world import World


def test_phases_run_in_strict_order():
    world = World.new(":memory:")
    final = GRAPH.invoke({
        "world": world, "rng": random.Random(0), "trace": [],
        "tick_ctx": {"tick": 0, "time_slot": "morning", "day": 0},
        "plans": {}, "moves": {}, "rejected": [], "dialogues": [],
        "memories": [], "narration": "",
    })
    assert final["trace"] == ["plan", "act", "converse", "remember", "narrate"]


def test_deterministic_positions_same_seed():
    def run():
        world = World.new(":memory:")
        rng = random.Random(42)
        for _ in range(6):
            run_tick(world, rng)
            world.advance_time()
        return world.positions()

    assert run() == run()


def test_different_seed_diverges():
    def run(seed):
        world = World.new(":memory:")
        rng = random.Random(seed)
        for _ in range(6):
            run_tick(world, rng)
            world.advance_time()
        return world.positions()

    assert run(1) != run(999)  # not a guarantee in theory, but true here
