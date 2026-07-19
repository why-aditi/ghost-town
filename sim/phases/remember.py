"""Memory writes: build observations of what each agent can see, then score
importance for ALL new memories in one batched Mistral call, then persist.

Observations are of *observable* facts (who's here, what they're doing, events
in the zone) — never another agent's secret or private reasoning, so this is
not a bleed. Information only enters an agent's mind here; that's the substrate
gossip will propagate over (Day 4).
"""
import logging
import os

from sim import config
from sim.llm import client
from sim.models import ImportanceScores, MemoryEntry

log = logging.getLogger("sim.remember")

_ACTION_PHRASE = {"work": "working", "wander": "wandering",
                  "go_home": "heading home", "idle": "resting"}


def _phrase(action: str) -> str:
    return _ACTION_PHRASE.get(action, action)


def _gather(world, plans, dialogues, tick_ctx) -> list[tuple[str, str, str]]:
    """Return [(agent_id, text, type)] of new memories this tick."""
    slot = tick_ctx["time_slot"]
    tick = tick_ctx["tick"]
    positions = world.positions()
    names = {a["id"]: a["name"] for a in world.agents()}
    by_zone: dict[str, list[str]] = {}
    for aid, z in positions.items():
        by_zone.setdefault(z, []).append(aid)

    entries: list[tuple[str, str, str]] = []
    for aid, z in positions.items():
        my_action = plans[aid].action if aid in plans else "idle"
        entries.append((aid, f"I spent the {slot} {_phrase(my_action)} at the {z}.", "observation"))
        for other in sorted(by_zone[z]):
            if other == aid:
                continue
            oact = plans[other].action if other in plans else "idle"
            entries.append((aid, f"I saw {names[other]} {_phrase(oact)} at the {z}.", "observation"))
        for e in world.events_at(z):
            if e["tick_injected"] == tick:               # only newly-arrived events
                entries.append((aid, f"I witnessed at the {z}: {e['description']}", "observation"))

    for d in dialogues:
        for aid in d.participants:
            other = names[[p for p in d.participants if p != aid][0]]
            entries.append((aid, f"I talked with {other} in the {d.zone}.", "conversation"))
        # Gossip payload: what each participant LEARNED, from their perspective.
        for learner, facts in d.transfers.items():
            for fact in facts:
                entries.append((learner, fact, "conversation"))
    return entries


def _score(entries: list[tuple[str, str, str]], tick_ctx, budget) -> list[int]:
    """One batched Mistral call scores every new memory 1-10. Skipped on quiet
    ticks / on failure -> DEFAULT_IMPORTANCE. Never raises."""
    day = tick_ctx["day"]
    n = len(entries)
    if n == 0:
        return []
    # GHOST_SCORE=0 skips the scoring LLM call (e.g. the gossip demo, to cut
    # per-tick calls) -> everything gets default importance.
    if os.getenv("GHOST_SCORE") == "0" or not budget.can_spend(day):
        return [config.DEFAULT_IMPORTANCE] * n

    numbered = "\n".join(f"{i}: {text}" for i, (_, text, _) in enumerate(entries))
    prompt = (
        "Rate how important each memory is to the person who experienced it, "
        "from 1 (mundane routine) to 10 (life-changing or emotionally charged). "
        "Return ONLY a JSON object mapping each memory's index (as a string) to "
        "its integer score.\n\nMemories:\n" + numbered
    )
    try:
        resp = client.complete_json(prompt, ImportanceScores, purpose="importance",
                                    provider="mistral", temperature=0.0)
        budget.spend(day)
        scores = resp.root
        return [max(1, min(10, int(scores.get(str(i), config.DEFAULT_IMPORTANCE))))
                for i in range(n)]
    except Exception as e:  # noqa: BLE001 - scoring must never break a tick
        log.warning("importance scoring failed, using default: %s",
                    str(e).splitlines()[0][:120])
        return [config.DEFAULT_IMPORTANCE] * n


def remember(world, plans, dialogues, tick_ctx, budget) -> list[MemoryEntry]:
    entries = _gather(world, plans, dialogues, tick_ctx)
    importances = _score(entries, tick_ctx, budget)
    tick = tick_ctx["tick"]
    written = []
    for (aid, text, mtype), imp in zip(entries, importances):
        world.memory.add(aid, text, mtype, tick, imp)
        written.append(MemoryEntry(agent_id=aid, text=text, type=mtype,
                                   importance=imp, tick=tick))
    return written
