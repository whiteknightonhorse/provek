"""T-2.6 - three score invariants, including the machine check of transport independence."""
import ast
import pathlib

from src.abs_profile.evidence import EvidenceClass
from src.abs_profile.ladder import L
from src.abs_profile.measured import NotMeasured
from src.verify.scorer import projection, score_operation


def test_absence_of_evidence_is_NOT_L0():
    """L0 means "a human does it" - a claim about the world. Absence of data is not that claim."""
    s = score_operation("pricing", None, ())
    assert s.is_measured is False
    assert s.level is not L.L0


def test_the_scorer_names_WHICH_absence_and_never_claims_a_source_refused():
    """Fable R1. The old assertion accepted either reason and so locked the wrong one in place.

    UNREADABLE asserts that a source was approached and refused to answer. Only a collector can
    establish that, because only a collector talks to a source. The scorer must never produce it -
    and for every passport issued before 2026-08-20 it did, about sources nobody had tried to read.
    """
    nobody_looked = score_operation("deployment", None, ())
    assert nobody_looked.level is NotMeasured.CHECK_DID_NOT_RUN

    looked_found_nothing_usable = score_operation("deploy", L.L4, (EvidenceClass.SELF_REPORTED,))
    assert looked_found_nothing_usable.level is NotMeasured.NOTHING_QUALIFIED

    for evidence in [(), (EvidenceClass.SELF_REPORTED,), (EvidenceClass.PLATFORM_OBSERVED,)]:
        for level in [None, L.L0, L.L4]:
            assert score_operation("op", level, evidence).level is not NotMeasured.UNREADABLE


def test_confidence_and_limiters_survive_to_the_emitted_artefact():
    """Fable R3. They were computed, armed by a law, and dropped at `to_machine`.

    Every subject in the cohort is scored with weak_mixed_signal, so every published level is
    O1-limited `inferred`. An artefact that omits that publishes a stronger claim than the one that
    was measured.
    """
    from datetime import datetime, timezone

    from src.abs_profile.identity import Binding, BindingKind
    from src.abs_profile.measured import Measurement
    from src.passport.passport import Accountability, Provenance, build
    from src.verify.control_map import ControlMap, Coverage, Surface

    scores = [score_operation("development_initiation", L.L4,
                              (EvidenceClass.PLATFORM_OBSERVED,), 5,
                              weak_mixed_signal=True, runtime_trace=False),
              score_operation("deployment", None, ())]
    cov = Coverage([Surface.GITHUB], {"treasury": "no access"}, "a key in CI")
    p = build(Binding(BindingKind.GIT, "a/b"), scores, ControlMap([], cov),
              Measurement(value=40), Provenance("1.0.0", "1.0.0", 30), Accountability(),
              now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    ops = p.to_machine()["verified"]["operations"]

    assert ops[0]["confidence"] == "inferred", "an O1-limited level may not be published as measured"
    assert "O1:mixed_classes->inferred" in ops[0]["limiters_applied"]
    assert "O2:no_runtime_trace->capped_L2" in ops[0]["limiters_applied"]
    assert ops[1]["measured"] is False
    assert ops[1]["level"] == "check_did_not_run"


def test_self_reported_alone_cannot_produce_a_score():
    """Otherwise the score retells the subject's claim disguised as a measurement."""
    s = score_operation("deploy", L.L4, (EvidenceClass.SELF_REPORTED,))
    assert s.is_measured is False


def test_control_map_cap_lowers_a_claimed_level():
    """A claimed L5 must drop when a live privileged path exists."""
    s = score_operation("deploy", L.L5, (EvidenceClass.PLATFORM_OBSERVED,), control_map_cap=4)
    assert s.level is L.L4


def test_projection_is_absent_when_nothing_measured_not_zero():
    """A zero would mean "measured and fully non-autonomous" - a different claim."""
    p = projection([score_operation("x", None, ())])
    assert p.is_measured is False
    p2 = projection([score_operation("x", L.L5, (EvidenceClass.PLATFORM_OBSERVED,))])
    assert p2.value == 100


def _imports_of(path: str) -> list[str]:
    tree = ast.parse(pathlib.Path(path).read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names.append(node.module or "")
    return names


FORBIDDEN = ("transport", "erc8004", "web3", "eth", "rpc", "requests", "http")


def test_scorer_does_not_import_transport():
    """The MACHINE guarantee of transport independence (spec 4.4), not a convention.

    IMPORTS are checked by parsing the AST, not the file text. Grepping text is wrong: a word in a
    docstring is not a dependency, and a test that fails on documentation of its own constraint
    pushes people to stop documenting it. The first version of this test failed exactly that way -
    on its own name.

    A genuine failure here means the methodology has fused with a Draft standard and the protection
    against its change has ceased to exist.
    """
    imported = _imports_of("src/verify/scorer.py")
    assert imported, "scorer has no imports at all - the AST parse is broken, not the module clean"
    for mod in imported:
        low = mod.lower()
        assert not any(f in low for f in FORBIDDEN), f"scorer imports transport: {mod}"


def test_the_transport_check_is_ABLE_to_fail():
    """Instrument control: the check must catch a planted import, otherwise it is decoration."""
    assert any(f in "src.transport_erc8004" for f in FORBIDDEN)
