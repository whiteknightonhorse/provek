"""T-2.8 - four state-machine rules, each checked for its ability to fail."""
from datetime import datetime, timezone

import pytest

from src.registry.lifecycle import Lifecycle, Status, Trigger, UndefinedTransition

NOW = datetime(2026, 8, 19, tzinfo=timezone.utc)


def test_undefined_transition_is_IMPOSSIBLE_not_undocumented():
    lc = Lifecycle(Status.UNVERIFIED)
    with pytest.raises(UndefinedTransition):
        lc.apply(Trigger.VIOLATION_FOUND, NOW, "e1")
    assert lc.status is Status.UNVERIFIED      # the state did not move


def test_unmeasurable_gives_STALE_never_SUSPENDED():
    """ABI-33-4 - the verifier does not punish the subject for its own blindness."""
    lc = Lifecycle(Status.UNVERIFIED)
    lc.apply(Trigger.MANDATE_ACCEPTED, NOW)
    lc.apply(Trigger.EVIDENCE_SUFFICIENT, NOW)
    assert lc.apply(Trigger.UNMEASURABLE, NOW) is Status.STALE


def test_violation_DOES_suspend_but_needs_evidence():
    """A negative public verdict is a legal act; it is not issued without evidence."""
    lc = Lifecycle(Status.VERIFIED)
    with pytest.raises(UndefinedTransition):
        lc.apply(Trigger.VIOLATION_FOUND, NOW)          # without an evidence reference
    assert lc.apply(Trigger.VIOLATION_FOUND, NOW, "evidence/x.json") is Status.SUSPENDED


def test_history_is_append_only_and_carries_trigger():
    lc = Lifecycle(Status.UNVERIFIED)
    lc.apply(Trigger.MANDATE_ACCEPTED, NOW)
    lc.apply(Trigger.EVIDENCE_SUFFICIENT, NOW)
    h = lc.history
    assert len(h) == 2 and h[0].trigger is Trigger.MANDATE_ACCEPTED
    assert isinstance(h, tuple)                          # cannot be mutated from outside
    lc.apply(Trigger.VALIDITY_EXPIRED, NOW)
    assert len(lc.history) == 3 and lc.history[:2] == h   # the past was not rewritten


def test_withdrawal_is_terminal_from_anywhere():
    for start in (Status.VERIFIED, Status.SUSPENDED, Status.STALE):
        lc = Lifecycle(start)
        assert lc.apply(Trigger.MANDATE_WITHDRAWN, NOW) is Status.WITHDRAWN
        with pytest.raises(UndefinedTransition):
            lc.apply(Trigger.MANDATE_ACCEPTED, NOW)


def test_suspended_can_be_remedied_not_left_forever():
    """ABI-15-6: suspension is a consequential act and must have a way out."""
    lc = Lifecycle(Status.SUSPENDED)
    assert lc.apply(Trigger.REMEDIED, NOW) is Status.IN_PROGRESS
