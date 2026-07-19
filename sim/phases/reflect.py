"""Day-end reflection (PRD 6.3): each agent distills the day's salient memories
into 2-3 belief statements, stored as high-importance `reflection` memories.
This is what makes agents *change* over days.

ONE batched Mistral call handles all agents (budget-friendly, like planning).
Fires only at day-end (the evening tick) — called from tick.run_tick.
"""
import logging

from sim import config
from sim.llm import client
from sim.models import ReflectionResult

log = logging.getLogger("sim.reflect")


def _prompt(day_mems: dict[str, list[dict]], names: dict[str, str]) -> str:
    header = (
        "You distill each resident's day into higher-level beliefs. For each "
        "resident below, read the salient things that happened to them today and "
        "write 2-3 short belief statements they now hold — about people, the town, "
        "or themselves — grounded ONLY in their own memories (a resident cannot "
        "believe something they never experienced).\n"
        "Return ONLY a JSON object keyed by resident id; each value is a list of "
        "2-3 belief strings.\n\nRESIDENTS:"
    )
    sections = []
    for aid, mems in day_mems.items():
        lines = "\n".join(f"  - {m['text']}" for m in mems)
        sections.append(f"\n### {aid} — {names[aid]}\ntoday's memories:\n{lines}")
    return header + "\n".join(sections)


def reflect(world, tick_ctx: dict, budget) -> list[tuple[str, str]]:
    """Return [(agent_id, belief)] written this day-end. Empty if skipped."""
    day, tick = tick_ctx["day"], tick_ctx["tick"]
    if not budget.can_spend(day):
        log.info("budget exhausted -> skipping reflection")
        return []

    names = {a["id"]: a["name"] for a in world.agents()}
    day_mems: dict[str, list[dict]] = {}
    for aid in names:
        mems = [m for m in world.memory.all(aid) if m["tick"] // 3 == day]
        if mems:
            mems.sort(key=lambda m: m["importance"], reverse=True)
            day_mems[aid] = mems[:config.REFLECT_TOP_N]
    if not day_mems:
        return []

    try:
        resp = client.complete_json(_prompt(day_mems, names), ReflectionResult,
                                    purpose="reflection", provider="mistral")
        budget.spend(day)
    except Exception as e:  # noqa: BLE001 - reflection is optional depth, never fatal
        log.warning("reflection failed: %s", str(e).splitlines()[0][:120])
        return []

    written = []
    for aid, beliefs in resp.root.items():
        if aid not in names:
            continue
        for belief in beliefs:
            world.memory.add(aid, belief, "reflection", tick, config.REFLECTION_IMPORTANCE)
            written.append((aid, belief))
    return written
