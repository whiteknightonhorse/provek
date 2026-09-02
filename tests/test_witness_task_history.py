"""Phase 2 - `Passport.task_history` (WitnessRecord v0, spec 4.2-bis point 4, the D-05 slot):
never inside `verified`, never moves the score - same mandatory-control shape
`tests/test_phase2_service.py` already holds `service`/`service_endpoint` to.
"""
from __future__ import annotations

from src.abs_profile.evidence import EvidenceClass
from src.abs_profile.identity import Binding, BindingKind
from src.abs_profile.ladder import L
from src.passport.passport import Accountability, Provenance, build
from src.verify.control_map import ControlMap, Coverage, Surface
from src.verify.scorer import projection, score_operation

FULL = "whiteknightonhorse/example"

_RECORD = {
    "witness_id": "11111111-1111-1111-1111-111111111111",
    "subject_id": "git:whiteknightonhorse/example",
    "criterion": {"type": "url_reachable", "url": "https://example.com"},
    "result": "PASS",
    "evidence_digest": "abc123",
    "checked_at": "2026-09-02T00:00:00+00:00",
    "witnessed_fee_paid": False,
}


def _minimal_passport(**kw):
    scores = [score_operation("development_initiation", L.L3, (EvidenceClass.PLATFORM_OBSERVED,)),
             score_operation("deployment", None, ()),
             score_operation("treasury_control", None, ())]
    cov = Coverage([Surface.GITHUB], {"treasury": "no access"}, "a key in CI")
    binding = Binding(BindingKind.GIT, FULL)
    return build(binding, scores, ControlMap([], cov), projection(scores),
                Provenance("1.1.0", "1.1.0", 30), Accountability(), **kw)


def test_task_history_is_top_level_not_inside_verified():
    p = _minimal_passport(task_history=[_RECORD])
    m = p.to_machine()
    assert "task_history" in m
    assert "task_history" not in m["verified"]
    entry = m["task_history"][0]
    assert entry == {
        "witness_id": "11111111-1111-1111-1111-111111111111",
        "criterion_type": "url_reachable",
        "result": "PASS",
        "checked_at": "2026-09-02T00:00:00+00:00",
        "url": "/w/11111111-1111-1111-1111-111111111111/",
    }


def test_task_history_defaults_to_empty():
    m = _minimal_passport().to_machine()
    assert m["task_history"] == []


def test_MANDATORY_CONTROL_task_history_never_moves_the_score():
    """A passport with a populated task_history and one with none, built from otherwise IDENTICAL
    inputs, must produce a byte-identical `verified` branch: a fixed-fee witnessing event is not
    evidence of autonomy, and must not be a way to buy a higher projection."""
    bare = _minimal_passport().to_machine()
    full = _minimal_passport(task_history=[_RECORD, {**_RECORD, "witness_id": "2", "result": "FAIL"}]).to_machine()
    assert bare["verified"] == full["verified"]
    assert bare["status"] == full["status"]
    assert bare["task_history"] != full["task_history"]


def test_MANDATORY_CONTROL_a_scorer_that_read_task_history_would_be_CAUGHT():
    """The live mutation, same discipline as `test_MANDATORY_CONTROL_a_scorer_that_read_service_
    would_be_CAUGHT` in tests/test_phase2_service.py: wrap `build()` so a non-empty task_history
    bumps the projection, and prove the invariant assertion above WOULD fail against it."""
    scores = [score_operation("development_initiation", L.L3, (EvidenceClass.PLATFORM_OBSERVED,)),
             score_operation("deployment", None, ()),
             score_operation("treasury_control", None, ())]
    cov = Coverage([Surface.GITHUB], {"treasury": "no access"}, "a key in CI")
    binding = Binding(BindingKind.GIT, FULL)
    real_build = build

    def mutant_build(*args, **kwargs):
        p = real_build(*args, **kwargs)
        th = kwargs.get("task_history")
        if th and p.verified.get("projection") is not None:
            p.verified["projection"] += 1
        return p

    bare = mutant_build(binding, scores, ControlMap([], cov), projection(scores),
                        Provenance("1.1.0", "1.1.0", 30), Accountability()).to_machine()
    full = mutant_build(binding, scores, ControlMap([], cov), projection(scores),
                        Provenance("1.1.0", "1.1.0", 30), Accountability(),
                        task_history=[_RECORD]).to_machine()

    assert bare["verified"] != full["verified"]
    assert full["verified"]["projection"] == bare["verified"]["projection"] + 1
