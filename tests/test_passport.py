"""T-2.7 - tree branches, accountability independence, expiry by time."""
from datetime import timedelta

from src.abs_profile.evidence import EvidenceClass
from src.abs_profile.identity import Binding, BindingKind
from src.abs_profile.ladder import L
from src.abs_profile.measured import Measurement, NotMeasured
from src.passport.passport import Accountability, Fact, Provenance, Status, build
from src.verify.control_map import ControlMap, Coverage, Surface
from src.verify.scorer import score_operation

PROV = Provenance("1.0.0", "1.0.0", 30)
COV = Coverage([Surface.GITHUB], {"treasury": "no access"}, "a key in CI")


def _p(**kw):
    return build(Binding(BindingKind.ERC8004, "42"),
                 [score_operation("deploy", L.L4, (EvidenceClass.PLATFORM_OBSERVED,))],
                 ControlMap([], COV), Measurement(value=80), PROV,
                 Accountability(), **kw)


def test_verified_and_self_reported_are_SEPARATE_BRANCHES():
    """ABI-14-2: the distinction must survive copying a subtree."""
    m = _p(claims={"revenue": "1M"}).to_machine()
    assert "revenue" in m["self_reported"] and "revenue" not in m["verified"]
    assert set(m["verified"]) & set(m["self_reported"]) == set()


def test_accountability_does_not_touch_the_score():
    """Debt 3: accountability lives OUTSIDE the ladder and does not affect the score."""
    a = _p().to_machine()
    b = build(Binding(BindingKind.ERC8004, "42"),
              [score_operation("deploy", L.L4, (EvidenceClass.PLATFORM_OBSERVED,))],
              ControlMap([], COV), Measurement(value=80), PROV,
              Accountability(emergency_stop=Fact.of(True),
                             claims_addressee=Fact.of("Example Ltd"),
                             insurance=Fact.of("policy 123"))).to_machine()
    assert a["verified"] == b["verified"]


def test_empty_control_map_gives_max_autonomy_AND_honest_no_addressee():
    """The symmetry the specification demands: both truths are visible side by side.

    SCHEMA 2.0.0. The 1.0.0 version of this test asserted a bare `None` and so locked the defect
    in place: it passed identically whether the check had run and found nothing or had never run
    at all. The symmetry it means to prove needs a MEASURED absence, which is now sayable.
    """
    m = build(Binding(BindingKind.ERC8004, "42"),
              [score_operation("deploy", L.L4, (EvidenceClass.PLATFORM_OBSERVED,))],
              ControlMap([], COV), Measurement(value=80), PROV,
              Accountability(claims_addressee=Fact.none_found())).to_machine()
    assert m["verified"]["control_map_cap"] == 5
    assert m["accountability"]["claims_addressee"] == {
        "value": None, "measured": True, "reason": None, "confidence": "assumed"}
    # `assumed`, not `measured` (Fable, V4): who answers a claim is not observable from outside,
    # so a completed check here establishes what the SUBJECT says, never what we verified.


def test_an_emitter_that_inspected_nothing_cannot_claim_an_honest_none():
    """The defect that shipped in 1.0.0, now unrepresentable by default.

    Every emitter built `Accountability()` and the artefact read as a completed check. The default
    must make the WEAKEST claim, so that the cheapest thing an author can write is also the most
    honest thing they can write.
    """
    m = _p().to_machine()
    for fieldname in ("emergency_stop", "claims_addressee", "insurance", "dispute_path"):
        assert m["accountability"][fieldname] == {
            "value": None, "measured": False, "reason": "check_did_not_run",
            "confidence": None}, fieldname


def test_a_fact_cannot_be_both_measured_and_excused():
    """Both and neither are the same defect wearing different clothes."""
    import pytest
    with pytest.raises(ValueError):
        Fact(value=None, measured=True, reason=NotMeasured.UNREADABLE)
    with pytest.raises(ValueError):
        Fact(value=None, measured=False, reason=None)
    with pytest.raises(ValueError):
        Fact(value="x", measured=False, reason=NotMeasured.UNREADABLE)


def test_nothing_qualified_is_barred_from_a_presence_field():
    """Fable ruling: a completed presence check emits a measured value, never an absence reason.

    Admitting it would give one state of the world two encodings - the mirror image of the defect
    the schema was rewritten to remove.
    """
    import pytest
    with pytest.raises(ValueError):
        Fact(measured=False, reason=NotMeasured.NOTHING_QUALIFIED)


def test_verified_lapses_to_stale_by_TIME_without_any_event():
    """ABI-15-5: a fact needs a place to expire."""
    p = _p()
    assert p.effective_status(p.issued_at) is Status.VERIFIED
    assert p.effective_status(p.valid_until + timedelta(seconds=1)) is Status.STALE


def test_invalid_control_map_cannot_yield_VERIFIED():
    """A map without coverage claims more than it knows - a passport cannot stand on it."""
    p = build(Binding(BindingKind.DNS, "x.com"),
              [score_operation("deploy", L.L4, (EvidenceClass.PLATFORM_OBSERVED,))],
              ControlMap([], None), Measurement(value=80), PROV, Accountability())
    assert p.status is Status.IN_PROGRESS


def test_passport_carries_provenance_and_binding_strength():
    m = _p().to_machine()
    assert m["provenance"]["protocol_version"] == "1.0.0"
    assert m["binding_strength"] == "strong"
    assert "does not measure reliability" in m["disclaimer"]


def test_absent_projection_is_reported_with_its_REASON():
    """A zero and "there was nothing to measure" are different states of the world."""
    from src.abs_profile.measured import NotMeasured
    p = build(Binding(BindingKind.GIT, "g/h"), [], ControlMap([], COV),
              Measurement(absent=NotMeasured.NOTHING_QUALIFIED), PROV, Accountability())
    m = p.to_machine()
    assert m["verified"]["projection"] is None
    assert m["verified"]["projection_absent_reason"] == "nothing_qualified"


def test_a_measured_accountability_field_must_name_its_register():
    """Fable V4. Omitting the register publishes a self-declaration with a check's authority."""
    import pytest
    with pytest.raises(ValueError):
        Fact(value="Example Ltd", measured=True, reason=None, confidence=None)
    with pytest.raises(ValueError):
        Fact(value="Example Ltd", measured=True, reason=None, confidence="probably")
    with pytest.raises(ValueError):
        Fact(measured=False, reason=NotMeasured.UNREADABLE, confidence="assumed")


def test_the_self_declared_register_is_the_DEFAULT_for_accountability():
    """The cheapest call must make the weakest claim - the rule D-13 exists for.

    Accountability is self-declared by construction (spec 2.6): who answers, whether insurance
    exists, where a dispute goes. A caller who genuinely verified one against observed behaviour
    says so deliberately; a caller who did not gets `assumed` without having to think about it.
    """
    assert Fact.of("Example Ltd").confidence == "assumed"
    assert Fact.none_found().confidence == "assumed"
    assert Fact.of(True, confidence="measured").confidence == "measured"
