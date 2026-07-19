"""Full simulated-day dry run (PRD Day-5 DoD).

Runs N full days (3 ticks each: morning/afternoon/evening + a day-end
reflection), prints the day's chronicle (narrator prose), a sample agent's
reflections, and the per-day / total LLM call count — asserting <= 60/day.

    python -m sim.day_run                 # 2 days
    python -m sim.day_run 1 "a stranger arrives at the square asking about the mine"
"""
import random
import sys

from sim import config
from sim.llm import client
from sim.llm.client import LLMBudget
from sim.tick import run_tick
from sim.world import World

_INSPECT = "tilda"  # a sociable agent, likely to accumulate memories + beliefs


def main() -> None:
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    event = sys.argv[2] if len(sys.argv) > 2 else None
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

    world = World.new(":memory:")
    client.reset_calls()
    if event:
        world.inject_event("square", event, source="user")
        print(f"[injected @ square] {event}\n")

    rng = random.Random(11)
    budget = LLMBudget(config.BUDGET_PER_DAY)
    per_day: dict[int, int] = {}

    for _ in range(days * 3):
        report = run_tick(world, rng, budget)
        print(f"— day {report.day}, {report.time_slot} (calls this tick: {report.llm_calls}) —")
        print(f"  {report.narration}")
        for g in report.gossip:
            print(f"  💬 {g}")
        for r in report.reflections:
            print(f"  🧠 {r}")
        per_day[report.day] = budget.spent(report.day)
        world.advance_time()

    print("\n" + "=" * 70)
    print(f"THE CHRONICLE ({days} day(s)):")
    for entry in world.db.get_story():
        print(f"  [t{entry['tick']}] {entry['prose']}")

    print("\n" + "=" * 70)
    print(f"{_INSPECT}'s reflections (beliefs formed):")
    beliefs = [m for m in world.memory.all(_INSPECT) if m["type"] == "reflection"]
    for m in beliefs:
        print(f"  🧠 (day {m['tick'] // 3}) {m['text']}")
    if not beliefs:
        print("  (none formed)")

    print("\n" + "=" * 70)
    for d, n in sorted(per_day.items()):
        print(f"day {d}: {n} LLM calls  {'OK' if n <= config.BUDGET_PER_DAY else 'OVER BUDGET'}")
    print(f"total LLM calls: {client.total_calls()}")
    over = [d for d, n in per_day.items() if n > config.BUDGET_PER_DAY]
    if over:
        sys.exit(f"❌ BUDGET EXCEEDED on day(s) {over} (> {config.BUDGET_PER_DAY}/day)")
    print(f"✅ within budget (<= {config.BUDGET_PER_DAY} LLM calls/day)")


if __name__ == "__main__":
    main()
