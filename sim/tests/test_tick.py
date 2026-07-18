"""Tick phase ordering + that planned destinations get applied. LLM mocked."""
import random

from sim.llm.client import LLMBudget
from sim.models import BatchPlan
from sim.personas import WORKPLACE
from sim.tick import GRAPH, run_tick
from sim.world import World


def _everyone_to_work(world) -> BatchPlan:
    return BatchPlan.model_validate({
        a["id"]: {"destination": WORKPLACE[a["occupation"]], "action": "work",
                  "reason": f"{a['name']} heads to work"}
        for a in world.agents()
    })


def _init(world):
    return {
        "world": world, "rng": random.Random(0), "budget": LLMBudget(),
        "tick_ctx": {"tick": 0, "time_slot": "morning", "day": 0},
        "trace": [], "plans": {}, "rejected": [], "quiet": False, "moves": {},
        "dialogues": [], "memories": [], "narration": "",
    }


def test_phases_run_in_strict_order(monkeypatch):
    world = World.new(":memory:")
    monkeypatch.setattr("sim.llm.client.complete_json",
                        lambda *a, **k: _everyone_to_work(world))
    final = GRAPH.invoke(_init(world))
    assert final["trace"] == ["plan", "act", "converse", "remember", "narrate"]


def test_planned_destinations_applied(monkeypatch):
    world = World.new(":memory:")
    monkeypatch.setattr("sim.llm.client.complete_json",
                        lambda *a, **k: _everyone_to_work(world))
    report = run_tick(world, random.Random(0), LLMBudget())
    for a in world.agents():
        assert a["position"] == WORKPLACE[a["occupation"]]
    assert report.llm_calls == 1 and report.quiet is False
