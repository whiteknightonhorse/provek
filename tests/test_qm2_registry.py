"""T-S10 - Q-M2's own registry write was dead code (ABI-19-2, invariant 5: a test must be able to
fail).

`scripts/measure_qm2.py` constructed a `PublicRegistry` and never called `.upsert()` or `.write()`
on it - the object existed only to be built, which is the "the section exists" shape invariant 5
forbids in a test and forbids here for the same reason: a constructor nobody calls is a claim
("this measurement publishes a registry entry") that nothing checks. `pipeline.verify()`, the
production entry point this script imitates, always follows `transport.publish` with a registry
upsert; the measurement script had silently dropped that step, so "the cost of ONE verification
pass" was under-counting the one pass production actually performs.

EACH TEST BELOW CAN FAIL: reverting `registry_row` to return the wrong fields, or reverting the
main loop to skip `registry.upsert`/`registry.write`, turns these red.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import tempfile
from datetime import datetime, timezone

from src.abs_profile.identity import Binding, BindingKind
from src.abs_profile.measured import Measurement
from src.collector import github as gh
from src.collector.github import GitHubEvidence
from src.passport.passport import Accountability
from src.registry.public_registry import PublicRegistry
from src.verify.control_map import Capability, ControlMap, ControlPath, Coverage, Surface

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("qm2measure_registry", ROOT / "scripts" / "measure_qm2.py")
qm2measure = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(qm2measure)
# Same undo as test_qm2_unreadable_subject.py: importing the script wraps `gh._api` at module
# scope for its own call-counting, and that patch must not outlive this import.
gh._api = qm2measure._orig

CMAP = ControlMap([ControlPath(Surface.GITHUB, Capability.IMPROVE_OR_FIX, True)],
                  Coverage([Surface.GITHUB], {"server": "runtime not presented"}, "CI secret"))


def _read_evidence(distinct_authors: int = 1, workflow_runs: int = 1) -> GitHubEvidence:
    return GitHubEvidence("whiteknightonhorse/some-repo", False, "deadbeef",
                          Measurement(value=1.0), Measurement(value=distinct_authors),
                          Measurement(value=0.0), Measurement(value=workflow_runs))


def _built_passport():
    ev = _read_evidence()
    b = Binding(BindingKind.GIT, ev.full_name)
    scores = [qm2measure.score_subject(ev, CMAP),
              qm2measure.score_operation("deployment", None, ()),
              qm2measure.score_operation("treasury_control", None, ())]
    p = qm2measure.build(b, scores, CMAP, qm2measure.projection(scores), qm2measure.PROV,
                         Accountability(), verifier_affiliation="same_owner")
    return b, p


def test_registry_row_carries_the_passports_own_status_and_projection():
    b, p = _built_passport()
    row = qm2measure.registry_row(b.as_subject_id(), p, "passports/git_whiteknightonhorse_some-repo.json")
    m = p.to_machine()
    assert row.subject_id == b.as_subject_id()
    assert row.status == p.status
    assert row.projection == m["verified"]["projection"]
    assert row.absent_reason == m["verified"]["projection_absent_reason"]
    assert row.passport_ref == "passports/git_whiteknightonhorse_some-repo.json"
    assert row.verifier_affiliation == "same_owner"


def test_a_measured_pass_is_readable_back_out_of_a_written_registry():
    """The behaviour a silently-unused `PublicRegistry` could never have had: something written to
    disk that a later reader can load. Exercises `.upsert()` and `.write()` directly, the two calls
    the main loop was skipping.
    """
    b, p = _built_passport()
    row = qm2measure.registry_row(b.as_subject_id(), p, "passports/x.json")

    r = PublicRegistry(pathlib.Path(tempfile.mkdtemp()))
    r.upsert(row)
    now = datetime.now(timezone.utc)
    written = json.loads(pathlib.Path(r.write(now)).read_text(encoding="utf-8"))

    assert written["count"] == 1
    assert written["subjects"][0]["subject_id"] == b.as_subject_id()
    assert written["subjects"][0]["passport_ref"] == "passports/x.json"
