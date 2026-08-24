"""T-S8 - LAW-NOT-MEASURED at the Q-M2 cost model's own scoring boundary (ABI-13-6, invariant 1).

`scripts/measure_qm2.py` scored `development_initiation` off whether `distinct_authors` happened to
be measured, and an UNREAD subject's `distinct_authors` is unmeasured for the same reason a subject
the collector genuinely read sometimes leaves it unmeasured: the old `else` branch could not tell
"the collector counted authors and found more than one" apart from "the collector never got to
count anything". `whiteknightonhorse/gov-auction-report` answers 404 to an anonymous reader
(reproduced live in evidence/RED-037-*) and the old branch handed it `level: L2` (after the
weak-signal cap), `measured: true`, `projection: 40` regardless - a number the collector never gave
the scorer, invariant 1 read backwards.

EACH TEST BELOW CAN FAIL: reverting `score_subject` to `L.L4 if ... else L.L3` with no `ev.read`
guard turns the first one red immediately, with a real level and a real number where invariant 1
requires neither.
"""
from __future__ import annotations

import importlib.util
import pathlib

from src.abs_profile.ladder import L
from src.abs_profile.measured import Measurement, NotMeasured
from src.collector import github as gh
from src.collector.github import GitHubEvidence
from src.verify.control_map import Capability, ControlMap, ControlPath, Coverage, Surface

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("qm2measure", ROOT / "scripts" / "measure_qm2.py")
qm2measure = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(qm2measure)
# Importing the script wraps `gh._api` at MODULE SCOPE for its own call-counting (a side effect of
# a script meant to be run, not imported) - and that patch outlives this import for the rest of the
# pytest session unless undone here. `tests/test_granted_channel_only.py` inspects `_api`'s own
# signature and goes red against the wrapper's, which carries no default for `token`.
gh._api = qm2measure._orig

CMAP = ControlMap([ControlPath(Surface.GITHUB, Capability.IMPROVE_OR_FIX, True)],
                  Coverage([Surface.GITHUB], {"server": "runtime not presented"}, "CI secret"))


def _unread(full_name: str = "whiteknightonhorse/gov-auction-report") -> GitHubEvidence:
    absent = Measurement(absent=NotMeasured.UNREADABLE)
    return GitHubEvidence(full_name, None, None, absent, absent, absent, absent,
                          notes=["repository not read, HTTP 404"], read=False)


def _read(distinct_authors: int, workflow_runs: int = 0) -> GitHubEvidence:
    return GitHubEvidence("whiteknightonhorse/some-repo", False, "deadbeef",
                          Measurement(value=1.0), Measurement(value=distinct_authors),
                          Measurement(value=0.0), Measurement(value=workflow_runs))


def test_an_unread_subject_gets_neither_a_level_nor_a_projection():
    score = qm2measure.score_subject(_unread(), CMAP)
    assert score.level == NotMeasured.UNREADABLE
    assert score.is_measured is False

    proj = qm2measure.projection([score,
                                  qm2measure.score_operation("deployment", None, ()),
                                  qm2measure.score_operation("treasury_control", None, ())])
    assert proj.value is None, "an unread subject must not carry a projection number"
    assert proj.absent is NotMeasured.UNREADABLE


def test_a_read_sole_author_subject_still_reaches_L4_capped_by_the_control_map():
    """The fix must not flatten the branch it repairs - a genuinely-read subject still scores."""
    score = qm2measure.score_subject(_read(distinct_authors=1, workflow_runs=1), CMAP)
    assert score.is_measured
    assert score.level == L.L4


def test_a_read_multi_author_subject_is_measured_and_distinct_from_the_unread_state():
    score = qm2measure.score_subject(_read(distinct_authors=2), CMAP)
    assert score.is_measured
    assert score.level != NotMeasured.UNREADABLE


def test_read_and_unread_evidence_with_identical_unmeasured_author_counts_score_differently():
    """The exact confusion the old branch made: both leave `distinct_authors` unmeasured.

    A subject the collector genuinely read but could not extract an author count from (an empty
    commit list, say) is `nothing_qualified` territory - still measured, still scored. A subject
    the collector never reached is `unreadable` and must not be scored at all. Same input to the
    old `if ev.distinct_authors.is_measured ...` test; different, correct outputs here.
    """
    absent = Measurement(absent=NotMeasured.UNREADABLE)
    read_but_empty = GitHubEvidence("whiteknightonhorse/empty-repo", False, "deadbeef",
                                    absent, absent, absent, absent, read=True)
    unread = _unread()
    assert read_but_empty.distinct_authors.is_measured == unread.distinct_authors.is_measured

    scored = qm2measure.score_subject(read_but_empty, CMAP)
    refused = qm2measure.score_subject(unread, CMAP)
    assert scored.level != NotMeasured.UNREADABLE
    assert refused.level == NotMeasured.UNREADABLE
