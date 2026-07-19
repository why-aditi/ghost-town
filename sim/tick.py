"""Per-tick LangGraph: plan -> act -> converse -> remember -> narrate.

Strict phase order is a non-negotiable arch decision (CLAUDE.md). Nodes are
thin wrappers over the phases/ functions — the graph is only wiring, so the
real logic stays plain, testable Python. Compiled once at import.
"""
import random
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from sim.llm.client import LLMBudget
from sim.models import TickReport
from sim.phases import act as act_phase
from sim.phases import converse as converse_phase
from sim.phases import narrate as narrate_phase
from sim.phases import plan as plan_phase
from sim.phases import reflect as reflect_phase
from sim.phases import remember as remember_phase
from sim.world import World


class TickState(TypedDict, total=False):
    world: World
    rng: random.Random
    budget: LLMBudget
    tick_ctx: dict
    plans: dict
    rejected: list
    quiet: bool
    moves: dict
    dialogues: list
    memories: list
    narration: str
    trace: list  # phase-execution order, for tests + debugging


def _plan(s: TickState) -> dict:
    res = plan_phase.plan(s["world"], s["tick_ctx"], s["budget"])
    return {"plans": res["plans"], "rejected": res["rejected"],
            "quiet": res["quiet"], "trace": s["trace"] + ["plan"]}


def _act(s: TickState) -> dict:
    res = act_phase.act(s["world"], s["plans"])
    return {"moves": res["moves"], "trace": s["trace"] + ["act"]}


def _converse(s: TickState) -> dict:
    # Quiet tick (budget exhausted): no conversations (CLAUDE.md).
    dialogues = ([] if s["quiet"]
                 else converse_phase.converse(s["world"], s["tick_ctx"], s["budget"]))
    return {"dialogues": dialogues, "trace": s["trace"] + ["converse"]}


def _remember(s: TickState) -> dict:
    mems = remember_phase.remember(s["world"], s["plans"], s["dialogues"],
                                   s["tick_ctx"], s["budget"])
    return {"memories": mems, "trace": s["trace"] + ["remember"]}


def _narrate(s: TickState) -> dict:
    prose = narrate_phase.narrate(s["world"], s["tick_ctx"], s["moves"],
                                  s["dialogues"], s["budget"])
    return {"narration": prose, "trace": s["trace"] + ["narrate"]}


def _build_graph():
    g = StateGraph(TickState)
    for name, fn in [("plan", _plan), ("act", _act), ("converse", _converse),
                     ("remember", _remember), ("narrate", _narrate)]:
        g.add_node(name, fn)
    g.add_edge(START, "plan")
    g.add_edge("plan", "act")
    g.add_edge("act", "converse")
    g.add_edge("converse", "remember")
    g.add_edge("remember", "narrate")
    g.add_edge("narrate", END)
    return g.compile()


GRAPH = _build_graph()


def _build_report(tick_ctx, final, reflections, calls) -> TickReport:
    return TickReport(
        tick=tick_ctx["tick"], time_slot=tick_ctx["time_slot"], day=tick_ctx["day"],
        planned=final["plans"], moves=final["moves"], rejected=final["rejected"],
        conversations=[tuple(d.participants) for d in final["dialogues"]],
        gossip=[f"{learner} learned: {fact}" for d in final["dialogues"]
                for learner, facts in d.transfers.items() for fact in facts],
        reflections=[f"{aid}: {belief}" for aid, belief in reflections],
        narration=final["narration"], quiet=final["quiet"], llm_calls=calls,
    )


# Human-readable progress label per phase, for the SSE stream / UI.
_PHASE_LABEL = {
    "plan": "agents are deciding what to do…",
    "act": "agents move about town…",
    "converse": "conversations unfold…",
    "remember": "everyone forms memories…",
    "narrate": "the chronicler writes it down…",
    "reflect": "agents reflect on the day…",
}


def run_tick_stream(world: World, rng: random.Random, budget: LLMBudget):
    """Generator yielding (phase, data) as each phase completes, then
    ("report", TickReport). Powers both run_tick and the API's SSE stream.
    Does NOT advance the clock."""
    w = world.state()
    tick_ctx = {"tick": w["tick"], "time_slot": w["time_slot"], "day": w["day"]}
    before = budget.spent(w["day"])
    final = {"plans": {}, "rejected": [], "quiet": False, "moves": {},
             "dialogues": [], "narration": "", "trace": []}
    init = {"world": world, "rng": rng, "budget": budget, "tick_ctx": tick_ctx,
            "memories": [], **final}

    for update in GRAPH.stream(init, stream_mode="updates"):
        for node, delta in update.items():
            final.update(delta)
            data = {"label": _PHASE_LABEL.get(node, node)}
            if node == "converse":
                data["conversations"] = [list(d.participants) for d in final["dialogues"]]
            elif node == "narrate":
                data["narration"] = final["narration"]
            yield node, data

    reflections = []
    if tick_ctx["time_slot"] == "evening" and not final["quiet"]:
        reflections = reflect_phase.reflect(world, tick_ctx, budget)
        yield "reflect", {"label": _PHASE_LABEL["reflect"],
                          "beliefs": [f"{a}: {b}" for a, b in reflections]}

    calls = budget.spent(w["day"]) - before
    yield "report", _build_report(tick_ctx, final, reflections, calls)


def run_tick(world: World, rng: random.Random, budget: LLMBudget) -> TickReport:
    """Run one full tick; return the report. Does NOT advance the clock."""
    report = None
    for phase, data in run_tick_stream(world, rng, budget):
        if phase == "report":
            report = data
    return report
