"""Planning phase: ONE batched Gemini call plans all agents, then anti-bleed
validation (CLAUDE.md). LLM proposes; world.py disposes.

Quiet-tick degradation: if the per-day budget is exhausted, agents continue
their current activity (stay put) with no LLM call and no conversations.
"""
import logging
import re

from sim.llm import client
from sim.llm.client import LLMUnavailable
from sim.models import AgentPlan, BatchPlan
from sim.personas import LEGAL_ACTIONS, WORKPLACE, ZONES

log = logging.getLogger("sim.plan")

_STOP = {"that", "this", "with", "from", "they", "them", "their", "have",
         "will", "about", "into", "been", "were", "your", "what", "when",
         "then", "here", "there", "keep", "want", "need", "goes", "going",
         "today", "morning", "afternoon", "evening", "town", "resident"}


def _tokens(*texts: str) -> set[str]:
    """Distinctive lowercase words (>=4 chars, minus stopwords)."""
    out: set[str] = set()
    for t in texts:
        for w in re.findall(r"[a-z']+", (t or "").lower()):
            if len(w) >= 4 and w not in _STOP:
                out.add(w)
    return out


def _safe_default(agent: dict, why: str) -> AgentPlan:
    """The safe action for a rejected/failed plan: stay put, do nothing."""
    return AgentPlan(agent_id=agent["id"], destination=agent["position"],
                     action="idle", reason=why)


def validate_no_bleed(agent: dict, plan: AgentPlan,
                      secret_tokens: dict[str, set[str]], known: set[str]) -> tuple[bool, str | None]:
    """Reject if the reason references another agent's private info (secrets)
    the agent could not know. Token-overlap heuristic.

    ponytail: substring/token match with a known ceiling — upgrade to embedding
    similarity if false positives bite. This is the interview talking point;
    keeping it mechanical and cheap is the point.
    """
    reason_tokens = _tokens(plan.reason)
    for other_id, stoks in secret_tokens.items():
        if other_id == agent["id"]:
            continue
        leaked = (reason_tokens & stoks) - known
        if leaked:
            return False, f"references {other_id}'s secret ({', '.join(sorted(leaked))})"
    return True, None


def _build_prompt(world, tick_ctx: dict, agents: list[dict]) -> str:
    occ: dict[str, list[str]] = {}
    for a in agents:
        occ.setdefault(a["position"], []).append(a["name"])
    occ_line = "; ".join(f"{z}: {', '.join(sorted(n))}" for z, n in sorted(occ.items()))

    header = (
        "You are the planner for a small town simulation. For EACH resident, "
        "decide where they go this time-slot and what they do, with a ONE-LINE "
        "reason grounded ONLY in that resident's own knowledge (their goals, "
        "memories, and what they can see). A resident must NOT reference another "
        "resident's secrets or private plans.\n"
        f"destination must be one of: {', '.join(ZONES)}.\n"
        f"action must be one of: {', '.join(LEGAL_ACTIONS)}.\n"
        'Return ONLY a JSON object keyed by resident id; each value is '
        '{"destination": "<zone>", "action": "<action>", "reason": "<one line>"}.\n\n'
        f"WORLD: It is {tick_ctx['time_slot']} of day {tick_ctx['day']}. "
        f"Right now — {occ_line}.\n\nRESIDENTS:"
    )

    sections = []
    for a in agents:
        mems = world.recent_memories(a["id"], 3)
        mem_lines = "\n".join(f"  - {m['text']}" for m in mems) or "  - (no memories yet)"
        secrets = "; ".join(a["secrets"]) or "(none)"
        sections.append(
            f"\n### {a['id']} — {a['name']} the {a['occupation']}\n"
            f"workplace: {WORKPLACE.get(a['occupation'], 'square')}; "
            f"currently at: {a['position']}\n"
            f"goals: {', '.join(a['daily_goals'])}\n"
            f"traits: {', '.join(a['traits'])}\n"
            f"secrets (known only to {a['name']}): {secrets}\n"
            f"recent memories:\n{mem_lines}"
        )
    return header + "\n".join(sections)


def plan(world, tick_ctx: dict, budget) -> dict:
    """Return {"plans": {id: AgentPlan}, "rejected": [id], "quiet": bool}."""
    day = tick_ctx["day"]
    agents = world.agents()

    if not budget.can_spend(day):
        log.info("budget exhausted (day %s) -> quiet tick", day)
        plans = {a["id"]: _safe_default(a, "(quiet tick) continuing current activity")
                 for a in agents}
        return {"plans": plans, "rejected": [], "quiet": True}

    try:
        batch = client.complete_json(
            _build_prompt(world, tick_ctx, agents), BatchPlan,
            purpose="planning", provider="mistral",
            model="mistral-small-latest", temperature=0.2)
        budget.spend(day)              # count only a successful planning call
        raw = batch.root
    except (LLMUnavailable, ValueError) as e:
        log.warning("planning failed, defaulting all agents: %s", e)
        return {"plans": {a["id"]: _safe_default(a, "(planning failed) defaulted")
                          for a in agents}, "rejected": [a["id"] for a in agents],
                "quiet": False}

    # Anti-bleed sets. Public knowledge (zones, names, occupations) never counts
    # as a leak; each agent's `known` set is what they may legitimately reference.
    secret_tokens = {a["id"]: _tokens(*a["secrets"]) for a in agents}
    public = _tokens(*ZONES, *[a["name"] for a in agents], *[a["occupation"] for a in agents])

    plans: dict[str, AgentPlan] = {}
    rejected: list[str] = []
    for a in agents:
        aid = a["id"]
        pa = raw.get(aid)
        if pa is None:
            plans[aid] = _safe_default(a, "(missing from plan) defaulted")
            rejected.append(aid)
            continue
        cand = AgentPlan(agent_id=aid, destination=pa.destination,
                         action=pa.action, reason=pa.reason)
        if cand.destination not in world.zones or cand.action not in LEGAL_ACTIONS:
            plans[aid] = _safe_default(a, f"(illegal {cand.destination}/{cand.action}) defaulted")
            rejected.append(aid)
            continue
        mems = [m["text"] for m in world.recent_memories(aid, 3)]
        known = _tokens(a["name"], a["occupation"], *a["traits"], *a["daily_goals"],
                        *a["secrets"], *[r["summary"] for r in world.relationships(aid)],
                        *mems) | public
        ok, why = validate_no_bleed(a, cand, secret_tokens, known)
        if not ok:
            log.info("anti-bleed rejected %s: %s", aid, why)
            plans[aid] = _safe_default(a, f"(anti-bleed) {why}")
            rejected.append(aid)
            continue
        plans[aid] = cand

    return {"plans": plans, "rejected": rejected, "quiet": False}
