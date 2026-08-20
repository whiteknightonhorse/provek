"""The three weak-signal limiters (Fable ruling, 2026-08-19).

Limiters must live in CODE. A rule written only in a comment is not enforced - this project has
already come close to paying for that.
"""
from src.abs_profile.evidence import EvidenceClass
from src.abs_profile.ladder import L
from src.verify.scorer import WEAK_SIGNAL_CEILING, Confidence, score_operation

OBS = (EvidenceClass.PLATFORM_OBSERVED,)


def test_O1_mixed_signal_can_never_be_MEASURED():
    """The key signed" is cryptographic; "the key is an agent" is self-reported. A mix is not a measurement."""
    s = score_operation("dev", L.L2, OBS, weak_mixed_signal=True)
    assert s.confidence is Confidence.INFERRED
    assert "O1:mixed_classes->inferred" in s.limiters_applied


def test_O1_strong_signal_stays_MEASURED():
    """A limiter must DISCRIMINATE, otherwise it simply lowers everything."""
    assert score_operation("dev", L.L4, OBS).confidence is Confidence.MEASURED


def test_O2_weak_signal_ALONE_cannot_justify_L3_or_above():
    """The key limiter: without a runtime trace of initiation the ceiling is L2."""
    s = score_operation("dev", L.L4, OBS, weak_mixed_signal=True, runtime_trace=False)
    assert s.level is WEAK_SIGNAL_CEILING
    assert "O2:no_runtime_trace->capped_L2" in s.limiters_applied


def test_O2_runtime_trace_lifts_the_ceiling():
    """With a runtime trace the signal is no longer alone, and the ceiling lifts."""
    s = score_operation("dev", L.L4, OBS, weak_mixed_signal=True, runtime_trace=True)
    assert s.level is L.L4
    assert not any(x.startswith("O2") for x in s.limiters_applied)


def test_O3_signal_is_stronger_at_REFUTING_than_confirming():
    """A contradiction legitimately lowers a claimed level; agreement only weakly supports it."""
    s = score_operation("dev", L.L4, OBS, weak_mixed_signal=True,
                        runtime_trace=False, claimed_level=L.L5)
    assert s.level is WEAK_SIGNAL_CEILING
    assert "O3:contradicts_claim->claim_rejected" in s.limiters_applied

    agree = score_operation("dev", L.L4, OBS, runtime_trace=True, claimed_level=L.L4)
    assert not any(x.startswith("O3") for x in agree.limiters_applied)


def test_limiters_are_RECORDED_not_silent():
    """A downgrade with no recorded reason is indistinguishable from a computation error."""
    s = score_operation("dev", L.L5, OBS, weak_mixed_signal=True, claimed_level=L.L5)
    assert s.limiters_applied and all(isinstance(x, str) for x in s.limiters_applied)


def test_control_map_cap_still_applies_on_top():
    s = score_operation("dev", L.L5, OBS, control_map_cap=3)
    assert s.level is L.L3 and "control_map_cap" in s.limiters_applied
