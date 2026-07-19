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
    prose = narrate_phase.narrate(s["world"], s["tick_ctx"], s["moves"], s["dialogues"])
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


def run_tick(world: World, rng: random.Random, budget: LLMBudget) -> TickReport:
    """Run one full tick against the current world clock. Returns a report.

    Does NOT advance the clock — cli.py advances after rendering so the report
    and map reflect the tick that just ran.
    """
    w = world.state()
    tick_ctx = {"tick": w["tick"], "time_slot": w["time_slot"], "day": w["day"]}
    before = budget.spent(w["day"])
    final = GRAPH.invoke({
        "world": world, "rng": rng, "budget": budget, "tick_ctx": tick_ctx,
        "trace": [], "plans": {}, "rejected": [], "quiet": False, "moves": {},
        "dialogues": [], "memories": [], "narration": "",
    })
    return TickReport(
        tick=tick_ctx["tick"],
        time_slot=tick_ctx["time_slot"],
        day=tick_ctx["day"],
        planned=final["plans"],
        moves=final["moves"],
        rejected=final["rejected"],
        conversations=[tuple(d.participants) for d in final["dialogues"]],
        gossip=[f"{learner} learned: {fact}"
                for d in final["dialogues"]
                for learner, facts in d.transfers.items() for fact in facts],
        narration=final["narration"],
        quiet=final["quiet"],
        llm_calls=budget.spent(w["day"]) - before,   # actual: planning + scoring
    )
