"""LAW-NOT-MEASURED. This test MUST FAIL if "not measured" ever collapses into a zero again."""
import pytest

from src.abs_profile.measured import Measurement, NotMeasured


def test_measurement_carries_exactly_one_of_value_or_absence():
    Measurement(value=12.5)
    Measurement(absent=NotMeasured.UNREADABLE)
    with pytest.raises(ValueError):
        Measurement()                                        # empty is forbidden
    with pytest.raises(ValueError):
        Measurement(value=1, absent=NotMeasured.UNREADABLE)   # doubled is forbidden


def test_six_absences_are_distinct_states_not_one():
    """Exactly the defect that hid a twelve-week source outage.

    Grew from three to five on 2026-09-01 (Fable): `NO_EVIDENCE_IN_WINDOW` and
    `APPARATUS_ABSENT` were added because the original three were made to lie - the live registry
    said `check_did_not_run` about two subjects whose GitHub history genuinely WAS read. Grew to
    six the same day: `NOT_DECLARED` is the accountability block's own species of the same defect
    (a subject's `provek.json` was read and simply said nothing about a field, which is not the
    same claim as "the check never ran"). Six distinct states, still never a zero, still never
    each other.
    """
    assert len({m.value for m in NotMeasured}) == 6
    assert NotMeasured.NOTHING_QUALIFIED != NotMeasured.UNREADABLE
    assert NotMeasured.CHECK_DID_NOT_RUN != NotMeasured.NOTHING_QUALIFIED
    assert NotMeasured.NO_EVIDENCE_IN_WINDOW != NotMeasured.CHECK_DID_NOT_RUN
    assert NotMeasured.NO_EVIDENCE_IN_WINDOW != NotMeasured.NOTHING_QUALIFIED
    assert NotMeasured.APPARATUS_ABSENT != NotMeasured.UNREADABLE
    assert NotMeasured.APPARATUS_ABSENT != NotMeasured.NO_EVIDENCE_IN_WINDOW
    assert NotMeasured.NOT_DECLARED != NotMeasured.CHECK_DID_NOT_RUN
    assert NotMeasured.NOT_DECLARED != NotMeasured.UNREADABLE


def test_absent_measurement_is_NOT_a_failure():
    """ABI-33-4: a missing measurement is not a violation - otherwise the verifier punishes its own blindness."""
    assert Measurement(absent=NotMeasured.UNREADABLE).gate_verdict(floor=10) == "NOT_MEASURED"
    assert Measurement(value=9).gate_verdict(floor=10) == "FAIL"
    assert Measurement(value=10).gate_verdict(floor=10) == "PASS"


def test_zero_is_a_measured_value_not_an_absence():
    """A MEASURED zero and a zero standing in for absence are different worlds."""
    m = Measurement(value=0)
    assert m.is_measured is True
    assert m.gate_verdict(floor=0) == "PASS"
