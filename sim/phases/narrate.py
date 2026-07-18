"""Narrator. Phase 1: templated prose, no LLM. Day 5 swaps in the Groq call.

Story log entries: <= 3 sentences, present tense, readable by non-tech people.
"""
from sim.models import Dialogue


def narrate(world, tick_ctx: dict, moves: dict[str, str],
            dialogues: list[Dialogue]) -> str:
    """Return (and persist) a short present-tense summary of the tick."""
    n_moves = len(moves)
    n_convos = len(dialogues)
    prose = (
        f"It is {tick_ctx['time_slot']} of day {tick_ctx['day']}. "
        f"{n_moves} residents move about town."
    )
    if n_convos:
        zones = sorted({d.zone for d in dialogues})
        prose += f" {n_convos} conversation(s) happen in the {', '.join(zones)}."
    world.add_story(tick_ctx["tick"], prose)
    return prose
