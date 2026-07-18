"""Planning phase. Phase 1: STUB minds — random-but-legal plans, no LLM.

Day 2 replaces `plan` with the single batched LLM call and fleshes out
`validate_no_bleed`. The signature and the anti-bleed hook stay put so the
rest of the graph doesn't move.
"""
import random

from sim.models import AgentPlan
from sim.personas import LEGAL_ACTIONS, ZONES


def plan(world, tick_ctx: dict, rng: random.Random) -> dict[str, AgentPlan]:
    """Return {agent_id: AgentPlan}. Legal by construction (stub)."""
    plans: dict[str, AgentPlan] = {}
    for a in world.agents():
        destination = rng.choice(ZONES)
        action = rng.choice(LEGAL_ACTIONS)
        plans[a["id"]] = AgentPlan(
            agent_id=a["id"],
            destination=destination,
            action=action,
            reason=f"(stub) chose to {action} at {destination}",
        )
    return plans


def validate_no_bleed(plan: AgentPlan, memories: list[dict]) -> bool:
    """Anti-bleed hook. Phase 1: no LLM reasons to check, so always passes.

    Day 2: reject any plan whose reason references information absent from this
    agent's memory stream; rejected agents default to a safe action.
    """
    return True
