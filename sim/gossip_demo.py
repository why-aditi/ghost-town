"""The gossip test / demo (PRD Day-4 centerpiece).

Inject a distinctive secret into ONE agent, run the town live, then print the
propagation chain — every agent that ends up holding a version of the secret,
with the tick and exact wording at each hop (mutations included) — and assert
it reached >= 2 other agents.

    python -m sim.gossip_demo                 # default: tell Tilda (a gossip), 10 ticks
    python -m sim.gossip_demo elara 12        # tell the baker instead, 12 ticks
"""
import os
import random
import sys

os.environ.setdefault("GHOST_SCORE", "0")  # skip importance scoring -> fewer LLM calls

from sim import config
from sim.llm.client import LLMBudget
from sim.tick import run_tick
from sim.world import World

# A juicy, distinctive secret — markers don't collide with any persona text,
# so the chain (and its mutations) is easy to trace.
SECRET = "Silas the merchant secretly buried a chest of gold under the old oak tree."
MARKERS = ("gold", "buried", "chest", "oak", "coins", "treasure")


def _about_secret(text: str) -> bool:
    t = text.lower()
    return any(m in t for m in MARKERS)


def holders(world) -> dict[str, list[dict]]:
    """agent_id -> their memories that mention the secret (sorted by tick)."""
    out = {}
    for a in world.agents():
        hits = [m for m in world.memory.all(a["id"]) if _about_secret(m["text"])]
        if hits:
            out[a["id"]] = hits
    return out


def main() -> None:
    source = sys.argv[1] if len(sys.argv) > 1 else "tilda"
    ticks = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)  # live progress

    world = World.new(":memory:")
    if world.agent(source) is None:
        sys.exit(f"no such agent '{source}'. choose one of: "
                 f"{', '.join(a['id'] for a in world.agents())}")

    # Inject the secret into ONE agent's memory only (high importance).
    world.memory.add(source, SECRET, "observation", tick=0, importance=9)
    print(f"🔒 Told only {source}: \"{SECRET}\"\n{'─' * 70}")

    rng = random.Random(7)
    budget = LLMBudget(config.BUDGET_PER_DAY)
    for _ in range(ticks):
        report = run_tick(world, rng, budget)
        occ = {}
        for aid, z in world.positions().items():
            occ.setdefault(z, []).append(aid)
        where = " ".join(f"{z}:{','.join(sorted(a))}" for z, a in sorted(occ.items()))
        convos = ", ".join(f"{a}-{b}" for a, b in report.conversations) or "none"
        print(f"tick {report.tick} ({report.time_slot}) | {where}")
        print(f"    talk: {convos}")
        for g in report.gossip:
            mark = "🟡GOSSIP" if _about_secret(g) else "  "
            print(f"    {mark} {g}")
        world.advance_time()

    # Propagation chain: every holder, in the order they learned it.
    chain = holders(world)
    events = sorted(
        ((m["tick"], aid, m["text"]) for aid, mems in chain.items() for m in mems),
        key=lambda e: (e[0], e[1]))
    print(f"\n{'─' * 70}\nPROPAGATION CHAIN (exact wording at each hop):")
    for tick, aid, text in events:
        tag = "SOURCE" if aid == source and tick == 0 else "heard "
        print(f"  t{tick:<2} [{tag}] {aid:<7}: {text}")

    others = [aid for aid in chain if aid != source]
    print(f"\n{'─' * 70}\nReached {len(others)} other agent(s): {', '.join(others) or 'none'}")
    if len(others) >= 2:
        print("✅ GOSSIP TEST PASSED (secret reached >= 2 others).")
    else:
        sys.exit("❌ GOSSIP TEST FAILED (secret reached < 2 others). "
                 "Try more ticks, or a more sociable source agent.")


if __name__ == "__main__":
    main()
