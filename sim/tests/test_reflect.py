"""Day-end reflection, narrator storage, and user-event importance. LLM mocked."""
from sim import config
from sim.llm.client import LLMBudget
from sim.models import ReflectionResult
from sim.phases import narrate as narrate_phase
from sim.phases import reflect as reflect_phase
from sim.phases.remember import remember
from sim.tests.util import new_world

_EVE = {"tick": 2, "time_slot": "evening", "day": 0}


def test_reflection_writes_belief_memories(monkeypatch):
    world = new_world()
    result = ReflectionResult.model_validate(
        {"tilda": ["I believe Silas is hiding something", "The square is where news breaks"]})
    monkeypatch.setattr("sim.llm.client.complete_json", lambda *a, **k: result)

    written = reflect_phase.reflect(world, _EVE, LLMBudget())

    assert ("tilda", "I believe Silas is hiding something") in written
    beliefs = [m for m in world.memory.all("tilda") if m["type"] == "reflection"]
    assert any("hiding something" in m["text"] for m in beliefs)
    assert all(m["importance"] == config.REFLECTION_IMPORTANCE for m in beliefs)


def test_reflection_skipped_when_budget_exhausted(monkeypatch):
    world = new_world()
    called = {"n": 0}
    monkeypatch.setattr("sim.llm.client.complete_json",
                        lambda *a, **k: called.__setitem__("n", called["n"] + 1))
    assert reflect_phase.reflect(world, _EVE, LLMBudget(per_day=0)) == []
    assert called["n"] == 0


def test_user_event_gets_high_importance(monkeypatch):
    monkeypatch.setenv("GHOST_SCORE", "0")           # skip scoring -> defaults + overrides only
    world = new_world()
    world.move_agent("tilda", "square")
    world.inject_event("square", "a stranger arrives asking about the mine", source="user")

    remember(world, plans={}, dialogues=[], tick_ctx={"tick": 0, "time_slot": "morning", "day": 0},
             budget=LLMBudget())

    witnessed = [m for m in world.memory.all("tilda") if "stranger arrives" in m["text"]]
    assert witnessed and witnessed[0]["importance"] == config.USER_EVENT_IMPORTANCE


def test_narrator_template_stores_story(monkeypatch):
    monkeypatch.setenv("GHOST_NARRATE", "0")         # force template path (no LLM call)
    world = new_world()
    prose = narrate_phase.narrate(world, {"tick": 0, "time_slot": "morning", "day": 0},
                                  moves={"tilda": "square"}, dialogues=[], budget=LLMBudget())
    assert "morning" in prose
    assert world.db.get_story()[-1]["prose"] == prose
