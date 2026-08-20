"""T-2.12 - fail-closed without a mandate, and the refusal reason never collapses into "no"."""
from datetime import datetime, timedelta, timezone

from src.mandate.mandate import Denial, Mandate, may_probe

NOW = datetime(2026, 8, 19, tzinfo=timezone.utc)


def _m(**kw):
    base = dict(subject_id="git:a/b", permitted_actions=frozenset({"latency_probe"}),
                max_calls_per_hour=10, blast_radius="the subject's real customers are not affected",
                liability="the incubator covers direct damage", abort_condition="p95 > 2s",
                valid_from=NOW - timedelta(days=1), valid_until=NOW + timedelta(days=30))
    base.update(kw)
    return Mandate(**base)


def test_no_mandate_means_NO_probe():
    """Probing someone's production without a mandate is an incident, not a verification."""
    ok, why = may_probe(None, "latency_probe", NOW)
    assert ok is False and why is Denial.NO_MANDATE


def test_revoked_and_missing_are_DIFFERENT_reasons():
    """A bare "no" is the same "one return value, two worlds" defect."""
    _, a = may_probe(None, "latency_probe", NOW)
    _, b = may_probe(_m(revoked_at=NOW - timedelta(hours=1)), "latency_probe", NOW)
    assert a is Denial.NO_MANDATE and b is Denial.REVOKED and a != b


def test_expired_mandate_denies():
    _, why = may_probe(_m(valid_until=NOW - timedelta(days=1)), "latency_probe", NOW)
    assert why is Denial.EXPIRED


def test_action_outside_the_mandate_is_denied():
    """A mandate permits SPECIFIC actions, not probing in general."""
    _, why = may_probe(_m(), "fault_injection", NOW)
    assert why is Denial.ACTION_NOT_PERMITTED


def test_rate_limit_is_enforced():
    _, why = may_probe(_m(), "latency_probe", NOW, calls_last_hour=10)
    assert why is Denial.RATE_EXCEEDED


def test_valid_mandate_permits():
    ok, why = may_probe(_m(), "latency_probe", NOW, calls_last_hour=1)
    assert ok is True and why is None


def test_mandate_carries_liability_and_abort_condition():
    """A mandate is a legal object, not a checkbox."""
    m = _m()
    assert m.liability and m.abort_condition and m.blast_radius
