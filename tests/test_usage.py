from types import SimpleNamespace

from camrahd_ai.observability import usage as usage_module
from camrahd_ai.observability.usage import UsageTracker


def _chunk(input_tokens, output_tokens):
    return SimpleNamespace(usage_metadata={"input_tokens": input_tokens, "output_tokens": output_tokens})


def test_tracker_accumulates_usage():
    tracker = UsageTracker()
    tracker.add_from_chunk(_chunk(100, 20))
    tracker.add_from_chunk(_chunk(50, 10))
    tracker.add_from_chunk(SimpleNamespace(usage_metadata=None))  # ignored
    assert tracker.input_tokens == 150
    assert tracker.output_tokens == 30
    assert tracker.requests == 2


def test_cost_is_none_without_pricing():
    tracker = UsageTracker()
    tracker.add_from_chunk(_chunk(1000, 1000))
    assert tracker.cost() is None


def test_cost_with_pricing(monkeypatch):
    monkeypatch.setitem(usage_module.config, "pricing", {"input_per_1m": 2.0, "output_per_1m": 10.0})
    tracker = UsageTracker()
    tracker.add_from_chunk(_chunk(1_000_000, 500_000))
    assert tracker.cost() == 2.0 + 5.0
    assert "$" in tracker.summary()
