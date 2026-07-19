"""Conversation phase: pairing heuristic (pure) + one Groq call per pair that
generates the dialogue, extracts information transferred per direction, and
proposes relationship updates. Transfers are grounded (a speaker can only pass
on what they could know) before being written to memory in remember.py.

This is the gossip engine: information exists for an agent only once it's in
their memory stream, so transfers ARE propagation.
"""
import logging
from itertools import combinations

from sim import config
from sim.llm import client
from sim.models import Dialogue, DialogueResult
from sim.personas import ZONES
from sim.text import tokens

log = logging.getLogger("sim.converse")


# --- pairing heuristic (pure, unit-tested) ---
def _pair_score(a: str, b: str, sociability: dict, rel: dict, avoid: set) -> float:
    soc = (sociability.get(a, 0.5) + sociability.get(b, 0.5)) / 2
    strength = max(abs(rel.get((a, b), 0.0)), abs(rel.get((b, a), 0.0)))
    acquainted = 1.0 if ((a, b) in rel or (b, a) in rel) else 0.0
    repeat = config.PAIR_REPEAT_PENALTY if (a, b) in avoid else 0.0
    return (config.PAIR_SOC_W * soc + config.PAIR_REL_W * strength
            + config.PAIR_ACQ_W * acquainted - repeat)


def choose_pairs(positions: dict[str, str], sociability: dict, rel: dict,
                 max_pairs: int = config.MAX_CONVERSATIONS_PER_TICK,
                 avoid: set | None = None) -> list[tuple[str, str]]:
    """Co-located pairs ranked by sociability + |sentiment| + acquaintance,
    minus a repeat penalty for pairs in `avoid` (last tick's pairs). At most
    `max_pairs`, no agent in two conversations. Deterministic."""
    avoid = avoid or set()
    by_zone: dict[str, list[str]] = {}
    for aid, z in positions.items():
        by_zone.setdefault(z, []).append(aid)

    cands = [(a, b) for ids in by_zone.values() for a, b in combinations(sorted(ids), 2)]
    cands.sort(key=lambda p: (-_pair_score(p[0], p[1], sociability, rel, avoid), p))

    chosen: list[tuple[str, str]] = []
    used: set[str] = set()
    for a, b in cands:
        if a in used or b in used:
            continue
        chosen.append((a, b))
        used |= {a, b}
        if len(chosen) >= max_pairs:
            break
    return chosen


def _pairing_inputs(world):
    agents = world.agents()
    sociability = {a["id"]: a["sociability"] for a in agents}
    rel = {(a["id"], r["other_id"]): r["sentiment"]
           for a in agents for r in world.relationships(a["id"])}
    return sociability, rel


# --- dialogue generation ---
def _query(agent: dict, other_name: str) -> str:
    return f"{other_name}; news, secrets, rumors; " + "; ".join(agent["daily_goals"])


def _mem_lines(mems: list[dict]) -> str:
    return "\n".join(f"  - {m['text']}" for m in mems) or "  - (nothing notable)"


def _section(world, agent: dict, other: dict, mems: list[dict]) -> str:
    rel = world.relationship(agent["id"], other["id"])
    opinion = rel["summary"] if rel else "(no prior opinion)"
    return (
        f"### {agent['id']} — {agent['name']} the {agent['occupation']} "
        f"(traits: {', '.join(agent['traits'])})\n"
        f"{agent['name']}'s opinion of {other['name']}: {opinion}\n"
        f"{agent['name']}'s memories:\n{_mem_lines(mems)}"
    )


def _prompt(world, a: dict, b: dict, a_mems, b_mems, zone: str) -> str:
    return (
        "Generate a short, natural conversation (2-4 total exchanges) between two "
        "residents who just met. Each resident may ONLY say things grounded in their "
        "own persona and memories below — never facts they don't know. Residents love "
        "to share surprising or juicy news they know; a gossip especially will eagerly "
        "pass on any secret or rumor from their memories.\n"
        "Return ONLY JSON with keys:\n"
        '  "exchanges": [{"speaker": "<id>", "text": "<line>"}],\n'
        '  "transfers": {"<id>": ["facts THIS resident LEARNED from the other, in '
        'their own words, e.g. \'Rurik told me the merchant owes the farmer money\'"]},\n'
        '  "relationships": {"<id>": {"sentiment_delta": <-1..1>, "summary": "<one line>"}}\n'
        f"Resident ids are {a['id']} and {b['id']}.\n\n"
        f"{_section(world, a, b, a_mems)}\n\n{_section(world, b, a, b_mems)}\n\n"
        f"They are meeting in the {zone}."
    )


def generate_dialogue(world, a_id: str, b_id: str, tick_ctx: dict):
    a, b = world.agent(a_id), world.agent(b_id)
    now = tick_ctx["tick"]
    a_mems = world.memory.retrieve(a_id, _query(a, b["name"]), config.TOP_K_CONV, now)
    b_mems = world.memory.retrieve(b_id, _query(b, a["name"]), config.TOP_K_CONV, now)
    result = client.complete_json(
        _prompt(world, a, b, a_mems, b_mems, a["position"]), DialogueResult,
        purpose="dialogue", provider="groq", temperature=config.DIALOGUE_TEMPERATURE)
    return result, a_mems, b_mems


# --- transfer grounding: a speaker can't pass on a third party's secret they
# don't know (reuses the anti-bleed idea). Lenient so real gossip still flows. ---
def _known(agent: dict, mems: list[dict], public: set) -> set:
    return tokens(agent["name"], agent["occupation"], *agent["traits"],
                  *agent["daily_goals"], *agent["secrets"],
                  *[m["text"] for m in mems]) | public


def _already_known(fact: str, learner_mems: list[dict]) -> bool:
    """The learner already holds this fact (>=3 shared distinctive tokens)."""
    ftoks = tokens(fact)
    if len(ftoks) < 3:
        return False
    return any(len(ftoks & tokens(m["text"])) >= 3 for m in learner_mems)


def _ground_transfers(world, a, b, a_mems, b_mems, transfers: dict) -> dict:
    agents = world.agents()
    public = tokens(*ZONES, *[ag["name"] for ag in agents], *[ag["occupation"] for ag in agents])
    secret_tokens = {ag["id"]: tokens(*ag["secrets"]) for ag in agents}
    known = {a["id"]: _known(a, a_mems, public), b["id"]: _known(b, b_mems, public)}
    speaker = {a["id"]: b["id"], b["id"]: a["id"]}  # learner -> who told them

    grounded: dict[str, list[str]] = {}
    for learner, facts in transfers.items():
        sp = speaker.get(learner)
        if sp is None:
            continue
        learner_mems = world.memory.all(learner)
        kept = []
        for fact in facts:
            ftoks = tokens(fact)
            leaks = any(other != sp and (ftoks & stoks) - known[sp]
                        for other, stoks in secret_tokens.items())
            if leaks:
                log.info("dropped ungrounded transfer to %s: %r", learner, fact)
            elif _already_known(fact, learner_mems):
                log.info("skipped already-known transfer to %s: %r", learner, fact)
            else:
                kept.append(fact)
        if kept:
            grounded[learner] = kept
    return grounded


def converse(world, tick_ctx: dict, budget) -> list[Dialogue]:
    day = tick_ctx["day"]
    now = tick_ctx["tick"]
    sociability, rel = _pairing_inputs(world)
    # A pair is "on cooldown" for PAIR_COOLDOWN_TICKS after talking, so gossip
    # keeps reaching new ears instead of looping between the same two agents.
    avoid = {p for p, t in world.pair_last_tick.items()
             if now - t < config.PAIR_COOLDOWN_TICKS}
    pairs = choose_pairs(world.positions(), sociability, rel, avoid=avoid)
    for p in pairs:
        world.pair_last_tick[p] = now

    dialogues: list[Dialogue] = []
    for a_id, b_id in pairs:
        if not budget.can_spend(day):
            break
        try:
            result, a_mems, b_mems = generate_dialogue(world, a_id, b_id, tick_ctx)
            budget.spend(day)
        except Exception as e:  # noqa: BLE001 - one bad dialogue shouldn't kill the tick
            log.warning("dialogue %s-%s failed: %s", a_id, b_id, str(e).splitlines()[0][:120])
            continue

        a, b = world.agent(a_id), world.agent(b_id)
        transfers = _ground_transfers(world, a, b, a_mems, b_mems, result.transfers)
        for agent_id, upd in result.relationships.items():
            if agent_id in (a_id, b_id):
                other = b_id if agent_id == a_id else a_id
                world.update_relationship(agent_id, other, upd.sentiment_delta, upd.summary)

        dialogues.append(Dialogue(
            participants=[a_id, b_id], zone=a["position"],
            exchanges=[f"{t.speaker}: {t.text}" for t in result.exchanges],
            transfers=transfers))
    return dialogues
