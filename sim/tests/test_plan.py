"""Anti-bleed validation + missing-agent defaults + budget quiet-tick.
All LLM calls mocked."""
from sim.llm.client import LLMBudget
from sim.models import BatchPlan
from sim.phases import plan as plan_phase
from sim.world import World

_CTX = {"tick": 0, "time_slot": "morning", "day": 0}


def _clean_batch(world) -> BatchPlan:
    return BatchPlan.model_validate({
        a["id"]: {"destination": "square", "action": "idle", "reason": "going about my day"}
        for a in world.agents()
    })


def test_anti_bleed_rejects_secret_reference(monkeypatch):
    world = World.new(":memory:")
    batch = _clean_batch(world)
    # Tilda's reason quotes Odette's private mine secret — she can't know it.
    batch.root["tilda"].reason = "rushing to tell everyone the mine collapse was no accident"
    monkeypatch.setattr("sim.llm.client.complete_json", lambda *a, **k: batch)

    res = plan_phase.plan(world, _CTX, LLMBudget())

    assert "tilda" in res["rejected"]
    assert res["plans"]["tilda"].action == "idle"                 # safe default
    assert res["plans"]["tilda"].destination == world.agent("tilda")["position"]
    assert "anti-bleed" in res["plans"]["tilda"].reason
    assert "pip" not in res["rejected"]                           # clean reason survives


def test_agent_may_reference_own_secret(monkeypatch):
    world = World.new(":memory:")
    batch = _clean_batch(world)
    # Odette referencing her OWN secret is fine — it's in her known set.
    batch.root["odette"].reason = "keeping quiet about the mine collapse i witnessed"
    monkeypatch.setattr("sim.llm.client.complete_json", lambda *a, **k: batch)

    res = plan_phase.plan(world, _CTX, LLMBudget())
    assert "odette" not in res["rejected"]


def test_missing_agent_gets_safe_default(monkeypatch):
    world = World.new(":memory:")
    batch = BatchPlan.model_validate(
        {"silas": {"destination": "market", "action": "work", "reason": "sell goods"}})
    monkeypatch.setattr("sim.llm.client.complete_json", lambda *a, **k: batch)

    res = plan_phase.plan(world, _CTX, LLMBudget())
    assert res["plans"]["silas"].destination == "market"
    assert "bram" in res["rejected"]
    assert res["plans"]["bram"].action == "idle"


def test_quiet_tick_makes_no_llm_call(monkeypatch):
    world = World.new(":memory:")
    called = {"n": 0}

    def spy(*a, **k):
        called["n"] += 1
        raise AssertionError("planning must not call the LLM on a quiet tick")

    monkeypatch.setattr("sim.llm.client.complete_json", spy)
    res = plan_phase.plan(world, _CTX, LLMBudget(per_day=0))  # nothing allowed

    assert res["quiet"] is True
    assert called["n"] == 0
    for a in world.agents():                                  # everyone stays put
        assert res["plans"][a["id"]].destination == a["position"]
