"""LLM client: JSON validation + one retry, provider fallback, budget math.
No real API calls — provider functions are monkeypatched."""
import pytest
from pydantic import BaseModel

import sim.llm.client as client
from sim.llm.client import LLMBudget, LLMUnavailable, complete, complete_json


class M(BaseModel):
    x: int


def test_retry_on_invalid_json_then_succeeds(monkeypatch):
    calls = {"n": 0}

    def fake_complete(prompt, **k):
        calls["n"] += 1
        return "not json at all" if calls["n"] == 1 else '{"x": 5}'

    monkeypatch.setattr(client, "complete", fake_complete)
    out = complete_json("p", M, purpose="t")
    assert out.x == 5 and calls["n"] == 2  # one retry with error feedback


def test_retry_exhausted_propagates(monkeypatch):
    monkeypatch.setattr(client, "complete", lambda p, **k: "still not json")
    with pytest.raises(Exception):
        complete_json("p", M, purpose="t")


def test_fallback_to_other_provider(monkeypatch):
    def boom(*a):
        raise LLMUnavailable("no mistral key")

    monkeypatch.setattr(client, "_mistral", boom)
    monkeypatch.setattr(client, "_groq", lambda prompt, model, temp, jm: ('{"x": 9}', 7))
    assert complete("p", purpose="t", provider="mistral") == '{"x": 9}'


def test_all_providers_fail_raises(monkeypatch):
    monkeypatch.setattr(client.time, "sleep", lambda s: None)  # no real backoff waits

    def boom(*a):
        raise RuntimeError("transient")

    monkeypatch.setattr(client, "_mistral", boom)
    monkeypatch.setattr(client, "_groq", boom)
    with pytest.raises(LLMUnavailable):
        complete("p", purpose="t", provider="mistral")


def test_budget_counts_and_rolls_over():
    b = LLMBudget(per_day=2)
    assert b.can_spend(0)
    b.spend(0)
    b.spend(0)
    assert not b.can_spend(0)   # 2/2 used today
    assert b.can_spend(1)       # new day resets the counter
    assert b.spent(1) == 0
