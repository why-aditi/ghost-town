"""Action resolution. Pure Python — applies validated plans to world state."""
from sim.models import AgentPlan


def act(world, plans: dict[str, AgentPlan]) -> dict:
    """Apply each plan via world.apply_plan. Rejected agents stay put (safe).

    Returns {"moves": {agent_id: destination}, "rejected": [agent_id, ...]}.
    """
    moves: dict[str, str] = {}
    rejected: list[str] = []
    for agent_id, plan in plans.items():
        applied, _reason = world.apply_plan(plan)
        if applied:
            moves[agent_id] = plan.destination
        else:
            rejected.append(agent_id)  # ponytail: safe action = stay put
    return {"moves": moves, "rejected": rejected}
