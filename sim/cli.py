"""Headless runner: `python -m sim.cli --ticks 6 --seed 42`.

Renders an ASCII zone map + a tick report each tick. Deterministic under a
fixed seed (single shared RNG threaded through planning).
"""
import argparse
import random
import sys

from sim import config
from sim.llm.client import LLMBudget
from sim.personas import ZONES
from sim.tick import run_tick
from sim.world import World

_COLS = 4          # zones per map row
_INNER = 14        # box inner width


def render_map(world: World) -> str:
    names = {a["id"]: a["name"] for a in world.agents()}
    by_zone: dict[str, list[str]] = {z: [] for z in ZONES}
    for agent_id, zone in world.positions().items():
        by_zone[zone].append(names[agent_id][0])

    def cell(zone: str) -> list[str]:
        initials = " ".join(sorted(by_zone[zone])) or "-"
        return [
            "┌" + "─" * _INNER + "┐",
            "│" + zone.center(_INNER) + "│",
            "│" + initials.center(_INNER) + "│",
            "└" + "─" * _INNER + "┘",
        ]

    lines = []
    for row_start in range(0, len(ZONES), _COLS):
        cells = [cell(z) for z in ZONES[row_start:row_start + _COLS]]
        for r in range(4):
            lines.append(" ".join(c[r] for c in cells))
    return "\n".join(lines)


def render_report(report) -> str:
    convos = ", ".join(f"{a}-{b}" for a, b in report.conversations) or "none"
    quiet = "  [QUIET TICK]" if report.quiet else ""
    out = [
        f"── Tick {report.tick}  (day {report.day}, {report.time_slot})  "
        f"llm_calls={report.llm_calls}{quiet} ──",
        report.narration,
    ]
    for aid, p in sorted(report.planned.items()):
        flag = " ✗" if aid in report.rejected else ""
        out.append(f"  {aid:<7} → {p.destination:<7} [{p.action}]{flag}: {p.reason}")
    out.append(f"conversations: {convos}")
    return "\n".join(out)


def render_inspect(world, agent_id: str) -> str:
    agent = world.agent(agent_id)
    if agent is None:
        return f"=== INSPECT {agent_id}: no such agent ==="
    out = [f"=== INSPECT {agent_id} — memory stream ==="]
    for m in world.memory.all(agent_id):
        out.append(f"  t{m['tick']} [{m['type']}] imp={m['importance']}: {m['text']}")
    q = "; ".join(agent["daily_goals"])
    now = world.state()["tick"]
    out.append(f"  -- top-{config.TOP_K_PLAN} retrieval for goals ({q!r}):")
    for m in world.memory.retrieve(agent_id, q, config.TOP_K_PLAN, now):
        out.append(f"     score={m['score']:.3f} (rel={m['relevance']:.2f} "
                   f"rec={m['recency']:.2f} imp={m['importance']}): {m['text']}")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(prog="sim.cli")
    ap.add_argument("--ticks", type=int, default=6)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--db", default=":memory:", help="sqlite path or :memory:")
    ap.add_argument("--inject", nargs=2, metavar=("ZONE", "DESCRIPTION"),
                    help="inject a user event into a zone before tick 0")
    ap.add_argument("--inspect", metavar="AGENT",
                    help="after the run, dump this agent's memories + retrieval")
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")  # box-drawing chars on Windows cp1252
    # Memory is ephemeral in v1 (persistent chroma = P1 save/load). --db still
    # persists world state (tick, positions, events, story) across runs.
    world = World.new(args.db, memory_path=None)
    rng = random.Random(args.seed)
    budget = LLMBudget(config.BUDGET_PER_DAY)

    if args.inject:
        zone, desc = args.inject
        if zone not in world.zones:
            sys.exit(f"error: unknown zone '{zone}'. valid zones: {', '.join(ZONES)}")
        world.inject_event(zone, desc, source="user")
        print(f"[injected @ {zone}] {desc}\n")

    for _ in range(args.ticks):
        report = run_tick(world, rng, budget)
        print(render_report(report))
        print(render_map(world))
        print()
        world.advance_time()

    if args.inspect:
        print(render_inspect(world, args.inspect))


if __name__ == "__main__":
    main()
