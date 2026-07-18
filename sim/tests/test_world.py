"""World mutation validation: only legal proposals change state."""
import pytest

from sim.models import AgentPlan
from sim.world import World


def fresh() -> World:
    return World.new(":memory:")


def test_valid_move_applied():
    w = fresh()
    w.move_agent("silas", "market")
    assert w.agent("silas")["position"] == "market"


def test_move_to_unknown_zone_raises():
    w = fresh()
    with pytest.raises(ValueError):
        w.move_agent("silas", "atlantis")


def test_move_unknown_agent_raises():
    w = fresh()
    with pytest.raises(ValueError):
        w.move_agent("nobody", "market")


def test_apply_legal_plan():
    w = fresh()
    applied, reason = w.apply_plan(
        AgentPlan(agent_id="bram", destination="farm", action="work", reason="x"))
    assert applied and reason is None
    assert w.agent("bram")["position"] == "farm"


def test_apply_plan_bad_zone_rejected_and_unmoved():
    w = fresh()
    before = w.agent("bram")["position"]
    applied, reason = w.apply_plan(
        AgentPlan(agent_id="bram", destination="atlantis", action="work", reason="x"))
    assert not applied and "zone" in reason
    assert w.agent("bram")["position"] == before  # rejected → not applied


def test_apply_plan_bad_action_rejected():
    w = fresh()
    applied, reason = w.apply_plan(
        AgentPlan(agent_id="bram", destination="farm", action="teleport", reason="x"))
    assert not applied and "action" in reason


def test_advance_time_cycles_slots():
    w = fresh()
    assert w.state() == {"tick": 0, "time_slot": "morning", "day": 0}
    assert w.advance_time()["time_slot"] == "afternoon"
    assert w.advance_time()["time_slot"] == "evening"
    third = w.advance_time()
    assert third == {"tick": 3, "time_slot": "morning", "day": 1}
