"""T-2.10 - silence as a finding, the fifth state, a finite watcher chain."""
from datetime import datetime, timedelta, timezone

from src.liveness.obligations import MAX_AGE, Interval, Obligation, Registry, SleepState

NOW = datetime(2026, 8, 19, 12, tzinfo=timezone.utc)


def test_empty_registry_is_SUSPICIOUS_not_clean():
    """There was nothing to check" and "everything is clean" are different states of the world."""
    f = Registry().sweep(NOW)
    assert f and "EMPTY OBLIGATION REGISTRY" in f[0]


def test_silence_becomes_a_named_finding():
    r = Registry()
    r.declare(Obligation("scorer", "runtime stamp", Interval.DAILY,
                         last_seen=NOW - timedelta(days=3), consumer="passport"))
    out = r.sweep(NOW)
    assert out and "SILENCE" in out[0] and "scorer" in out[0]


def test_never_seen_is_a_finding_not_an_absence():
    r = Registry()
    r.declare(Obligation("prober", "execution record", Interval.DAILY, consumer="scorer"))
    assert "SILENCE" in r.sweep(NOW)[0]


def test_producer_without_consumer_is_the_FIFTH_state():
    """A producer verified in isolation proves nothing about its consumer."""
    r = Registry()
    r.declare(Obligation("collector", "artifact", Interval.DAILY, last_seen=NOW, consumer=None))
    assert "NO CONSUMER" in r.sweep(NOW)[0]


def test_healthy_obligation_produces_no_finding():
    r = Registry()
    r.declare(Obligation("scorer", "stamp", Interval.DAILY, last_seen=NOW, consumer="passport"))
    assert r.sweep(NOW) == []


def test_watcher_chain_is_finite_and_names_its_terminus():
    """An endless chain of watchers is not reliability, it is an unanswered question."""
    chain = Registry().watcher_chain()
    assert chain[-1] == "external_heartbeat"
    assert len(chain) == 3


def test_five_sleep_states_are_distinct():
    assert len({s.value for s in SleepState}) == 5


def test_every_interval_carries_a_bound():
    """An interval with no MAX_AGE entry raises KeyError inside `finding()`, and a sweep that dies
    part way through has reported nothing about the obligations it had not reached yet - silence
    produced by the instrument built to end silence."""
    assert set(MAX_AGE) == set(Interval)
