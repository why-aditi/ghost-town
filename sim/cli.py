"""Headless runner: `python -m sim.cli --ticks 6 --seed 42`.

Renders an ASCII zone map + a tick report each tick. Deterministic under a
fixed seed (single shared RNG threaded through planning).
"""
import argparse
import random
import sys

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


def main() -> None:
    ap = argparse.ArgumentParser(prog="sim.cli")
    ap.add_argument("--ticks", type=int, default=6)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--db", default=":memory:", help="sqlite path or :memory:")
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")  # box-drawing chars on Windows cp1252
    world = World.new(args.db)
    rng = random.Random(args.seed)
    budget = LLMBudget()

    for _ in range(args.ticks):
        report = run_tick(world, rng, budget)
        print(render_report(report))
        print(render_map(world))
        print()
        world.advance_time()


if __name__ == "__main__":
    main()
