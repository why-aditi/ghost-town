"""Tick phase ordering + that planned destinations get applied. LLM mocked.

A full tick makes two LLM calls (planning, importance scoring), so the mock is
schema-aware: BatchPlan for planning, ImportanceScores for scoring.
"""
import random

from sim.llm.client import LLMBudget
from sim.models import BatchPlan, ImportanceScores
from sim.personas import WORKPLACE
from sim.tick import GRAPH, run_tick
from sim.tests.util import new_world


def _mock_llm(world):
    def fake(prompt, schema, **k):
        if schema is BatchPlan:
            return BatchPlan.model_validate({
                a["id"]: {"destination": WORKPLACE[a["occupation"]], "action": "work",
                          "reason": f"{a['name']} heads to work"}
                for a in world.agents()
            })
        return ImportanceScores.model_validate({})  # scorer -> all default importance
    return fake


def _init(world):
    return {
        "world": world, "rng": random.Random(0), "budget": LLMBudget(),
        "tick_ctx": {"tick": 0, "time_slot": "morning", "day": 0},
        "trace": [], "plans": {}, "rejected": [], "quiet": False, "moves": {},
        "dialogues": [], "memories": [], "narration": "",
    }


def test_phases_run_in_strict_order(monkeypatch):
    world = new_world()
    monkeypatch.setattr("sim.llm.client.complete_json", _mock_llm(world))
    final = GRAPH.invoke(_init(world))
    assert final["trace"] == ["plan", "act", "converse", "remember", "narrate"]


def test_planned_destinations_applied(monkeypatch):
    world = new_world()
    monkeypatch.setattr("sim.llm.client.complete_json", _mock_llm(world))
    report = run_tick(world, random.Random(0), LLMBudget())
    for a in world.agents():
        assert a["position"] == WORKPLACE[a["occupation"]]
    assert report.llm_calls == 2 and report.quiet is False  # planning + scoring
