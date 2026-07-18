"""Co-location pairing heuristic: pure and deterministic."""
from sim.phases.converse import pair_colocated


def test_pairs_within_zone():
    pairs = pair_colocated({"a": "cafe", "b": "cafe"})
    assert pairs == [("a", "b")]


def test_solo_agent_not_paired():
    assert pair_colocated({"a": "cafe", "b": "farm"}) == []


def test_odd_agent_left_unpaired():
    pairs = pair_colocated({"a": "cafe", "b": "cafe", "c": "cafe"})
    assert pairs == [("a", "b")]  # c unpaired


def test_deterministic_ordering():
    positions = {"z": "cafe", "a": "cafe", "m": "cafe", "b": "cafe"}
    assert pair_colocated(positions) == [("a", "b"), ("m", "z")]


def test_pairs_across_multiple_zones_sorted():
    positions = {"a": "cafe", "b": "cafe", "y": "farm", "x": "farm"}
    assert pair_colocated(positions) == [("a", "b"), ("x", "y")]
