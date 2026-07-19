"""Narrator: 2-3 delightful present-tense sentences per tick for the story log.

Groq call from the tick's moves/conversations/events. Falls back to a plain
template on a quiet tick, when the budget is spent, or on any error — the
chronicle never stops. GHOST_NARRATE=0 forces the template (keeps the gossip
demo fast).
"""
import logging
import os

from sim import config
from sim.llm import client
from sim.models import Dialogue

log = logging.getLogger("sim.narrate")


def _template(world, tick_ctx: dict, moves: dict[str, str],
              dialogues: list[Dialogue]) -> str:
    prose = (f"It is {tick_ctx['time_slot']} of day {tick_ctx['day']}. "
             f"{len(moves)} residents move about town.")
    if dialogues:
        zones = sorted({d.zone for d in dialogues})
        prose += f" {len(dialogues)} conversation(s) happen in the {', '.join(zones)}."
    return prose


def _prompt(world, tick_ctx: dict, moves: dict[str, str],
            dialogues: list[Dialogue]) -> str:
    names = {a["id"]: a["name"] for a in world.agents()}
    facts = []
    for d in dialogues:
        a, b = (names[p] for p in d.participants)
        learned = [f for facts_ in d.transfers.values() for f in facts_]
        note = f" ({learned[0]})" if learned else ""
        facts.append(f"- {a} and {b} talk in the {d.zone}{note}")
    seen_events = set()
    for zone in {world.agent(a)["position"] for a in moves} if moves else set():
        for e in world.events_at(zone):
            if e["tick_injected"] == tick_ctx["tick"] and e["description"] not in seen_events:
                seen_events.add(e["description"])
                facts.append(f"- an event in the {zone}: {e['description']}")
    happenings = "\n".join(facts) or "- a quiet spell; residents go about their work"
    return (
        "You are the warm, slightly playful chronicler of a small town. In 2-3 "
        "present-tense sentences that anyone could enjoy, narrate what just happened "
        f"this {tick_ctx['time_slot']}. Do not invent facts beyond those given; do "
        "not use bullet points or headings.\n\nWhat happened:\n" + happenings
    )


def narrate(world, tick_ctx: dict, moves: dict[str, str],
            dialogues: list[Dialogue], budget) -> str:
    day = tick_ctx["day"]
    if os.getenv("GHOST_NARRATE") == "0" or not budget.can_spend(day):
        prose = _template(world, tick_ctx, moves, dialogues)
    else:
        try:
            prose = client.complete(_prompt(world, tick_ctx, moves, dialogues),
                                    purpose="narrator", provider="groq",
                                    temperature=config.NARRATOR_TEMPERATURE,
                                    json_mode=False).strip()
            budget.spend(day)
        except Exception as e:  # noqa: BLE001 - never let the story stop
            log.warning("narrator failed, using template: %s", str(e).splitlines()[0][:120])
            prose = _template(world, tick_ctx, moves, dialogues)
    world.add_story(tick_ctx["tick"], prose)
    return prose
