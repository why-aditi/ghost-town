"""Pairing heuristic (pure) + transfer write + grounding. LLM mocked."""
from sim.llm.client import LLMBudget
from sim.models import DialogueResult
from sim.phases import converse as conv
from sim.phases.remember import remember
from sim.tests.util import new_world

_CTX = {"tick": 1, "time_slot": "afternoon", "day": 0}


# --- pairing heuristic ---
def test_pairs_only_co_located():
    pairs = conv.choose_pairs({"a": "cafe", "b": "farm"}, {"a": 0.9, "b": 0.9}, {})
    assert pairs == []


def test_sociable_pair_preferred_and_capped():
    positions = {"a": "cafe", "b": "cafe", "c": "cafe", "d": "cafe"}
    soc = {"a": 0.9, "b": 0.9, "c": 0.1, "d": 0.1}
    pairs = conv.choose_pairs(positions, soc, {}, max_pairs=2)
    assert len(pairs) <= 2
    assert ("a", "b") in pairs                     # highest sociability pair chosen


def test_no_agent_double_booked():
    positions = {"a": "cafe", "b": "cafe", "c": "cafe"}
    pairs = conv.choose_pairs(positions, {"a": .5, "b": .5, "c": .5}, {}, max_pairs=2)
    used = [x for p in pairs for x in p]
    assert len(used) == len(set(used))             # nobody appears twice


def test_repeat_pair_yields_to_fresh_partner():
    # a,b are the most sociable, but they talked last tick -> a should now be
    # forced onto a fresh partner so info spreads to new people
    positions = {"a": "square", "b": "square", "c": "square"}
    soc = {"a": 0.9, "b": 0.9, "c": 0.5}
    pairs = conv.choose_pairs(positions, soc, {}, max_pairs=1, avoid={("a", "b")})
    assert ("a", "b") not in pairs
    assert pairs and "c" in pairs[0]           # a or b now talks to c


def test_repeat_pair_still_chosen_when_no_alternative():
    pairs = conv.choose_pairs({"a": "square", "b": "square"}, {"a": .9, "b": .9},
                              {}, max_pairs=1, avoid={("a", "b")})
    assert pairs == [("a", "b")]               # only candidate -> repeat allowed


def test_rivalry_negative_sentiment_still_pairs():
    # |sentiment| drives pairing, so rivals (negative) beat strangers
    positions = {"a": "cafe", "b": "cafe", "c": "cafe", "d": "cafe"}
    soc = {k: 0.5 for k in "abcd"}
    rel = {("a", "b"): -0.9}                        # a despises b
    pairs = conv.choose_pairs(positions, soc, rel, max_pairs=1)
    assert pairs == [("a", "b")]


# --- transfer write + grounding ---
def test_transfer_written_to_learner_memory(monkeypatch):
    world = new_world()
    # tilda tells pip a fact; pip should end up with it in memory
    result = DialogueResult.model_validate({
        "exchanges": [{"speaker": "tilda", "text": "Have you heard the news?"}],
        "transfers": {"pip": ["Tilda told me the baker is planning something big"]},
        "relationships": {"pip": {"sentiment_delta": 0.1, "summary": "a good source"}},
    })
    monkeypatch.setattr("sim.llm.client.complete_json", lambda *a, **k: result)
    # force tilda & pip to be the pair
    monkeypatch.setattr(conv, "choose_pairs", lambda *a, **k: [("pip", "tilda")])

    dialogues = conv.converse(world, _CTX, LLMBudget())
    remember(world, {}, dialogues, _CTX, LLMBudget())

    pip_mems = [m["text"] for m in world.memory.all("pip")]
    assert any("baker is planning something big" in t for t in pip_mems)
    # relationship update applied
    assert world.relationship("pip", "tilda")["summary"] == "a good source"


def test_ungrounded_secret_transfer_dropped(monkeypatch):
    world = new_world()
    # pip "tells" tilda Odette's mine secret — pip can't know it -> dropped
    result = DialogueResult.model_validate({
        "exchanges": [],
        "transfers": {"tilda": ["Pip told me the old mine collapse was no accident"]},
        "relationships": {},
    })
    monkeypatch.setattr("sim.llm.client.complete_json", lambda *a, **k: result)
    monkeypatch.setattr(conv, "choose_pairs", lambda *a, **k: [("pip", "tilda")])

    dialogues = conv.converse(world, _CTX, LLMBudget())
    assert dialogues[0].transfers.get("tilda", []) == []   # grounded out
