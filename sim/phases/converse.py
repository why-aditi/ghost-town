"""Conversation phase. Phase 1: pairing heuristic only — no dialogue LLM.

`pair_colocated` is a pure, deterministic function (unit-tested). Day 4 adds
the per-pair dialogue call + information transfer on top of the same pairing.
"""
from sim.models import Dialogue


def pair_colocated(positions: dict[str, str]) -> list[tuple[str, str]]:
    """Pair agents sharing a zone. Deterministic: sort ids, pair consecutively.

    Odd agent out in a zone is left unpaired. Zones processed in sorted order.
    """
    by_zone: dict[str, list[str]] = {}
    for agent_id, zone in positions.items():
        by_zone.setdefault(zone, []).append(agent_id)

    pairs: list[tuple[str, str]] = []
    for zone in sorted(by_zone):
        ids = sorted(by_zone[zone])
        for i in range(0, len(ids) - 1, 2):
            pairs.append((ids[i], ids[i + 1]))
    return pairs


def converse(world) -> list[Dialogue]:
    """Stub: every co-located pair 'talks'. No transfers yet (Day 4)."""
    pairs = pair_colocated(world.positions())
    dialogues = []
    for a, b in pairs:
        zone = world.agent(a)["position"]
        dialogues.append(Dialogue(
            participants=[a, b],
            zone=zone,
            exchanges=[f"(stub) {a} and {b} talk in the {zone}"],
            transfers=[],
        ))
    return dialogues
