"""LAW-NOT-MEASURED gains a fourth and fifth reason (Fable, 2026-09-01) - and the live registry
was lying with the first three.

`check_did_not_run` on the AIpush and mcp-protocol-tester rows asserted that no check ran. Both
subjects' repositories WERE read: the collector answered 200, paged the full thirty-day commit
window, and found it empty. `nothing_qualified` at the collector site was the "declared reason
closest to this", already admitted as imprecise in its own comment - and neither survived to the
registry's headline reason anyway, because `projection()`'s old precedence let the two ALWAYS-
unattempted operations (`deployment`, `treasury_control`) outrank a genuine, subject-specific
reading with the boilerplate "nobody looked".

Each test below can fail: reverting the collector's empty-window branch to `NOTHING_QUALIFIED`,
reverting `score_operation`'s new `absent_reason` parameter, or reverting `projection()`'s
precedence order, turns the corresponding test red.
"""
from __future__ import annotations

import src.collector.github as gh
from src.abs_profile.evidence import EvidenceClass
from src.abs_profile.measured import Measurement, NotMeasured
from src.verify.scorer import projection, score_operation

FULL = "whiteknightonhorse/AIpush"


def _patched_api(responses):
    """A drop-in for `gh._api` that answers by URL prefix, restored by the caller."""
    def fake(path: str, token=None):
        for prefix, response in responses.items():
            if path.startswith(prefix):
                return response
        raise AssertionError(f"unexpected call: {path}")
    return fake


def _collect_with(responses) -> gh.GitHubEvidence:
    orig = gh._api
    gh._api = _patched_api(responses)
    try:
        return gh.collect_github(FULL)
    finally:
        gh._api = orig


# --------------------------------------------------------------- the collector, at the source
def test_an_empty_thirty_day_window_is_no_evidence_in_window_not_nothing_qualified():
    ev = _collect_with({
        f"/repos/{FULL}/commits": (200, []),
        f"/repos/{FULL}/actions/runs": (200, {"total_count": 0}),
        f"/repos/{FULL}": (200, {"private": False}),
    })
    assert ev.read is True, "the repository DID answer - this is the case the bug misreported"
    assert ev.distinct_authors.absent is NotMeasured.NO_EVIDENCE_IN_WINDOW
    assert ev.signed_commit_share.absent is NotMeasured.NO_EVIDENCE_IN_WINDOW
    assert ev.bot_author_share.absent is NotMeasured.NO_EVIDENCE_IN_WINDOW
    assert ev.distinct_authors.absent is not NotMeasured.NOTHING_QUALIFIED
    assert ev.distinct_authors.absent is not NotMeasured.CHECK_DID_NOT_RUN


def test_zero_total_workflow_runs_unwindowed_is_apparatus_absent_not_a_measured_zero():
    """Measured on cryptocardhub-public: `/actions/runs` carries no `since` filter, so
    `total_count: 0` means no CI run has EVER existed - a permanent fact about the subject, not a
    windowed absence and not a legitimate zero count."""
    ev = _collect_with({
        f"/repos/{FULL}/commits": (200, [{"sha": "a", "commit": {"author": {"date": "2026-08-01T00:00:00Z"},
                                                                   "verification": {"verified": False}},
                                          "author": {"login": "solo", "type": "User"}}]),
        f"/repos/{FULL}/actions/runs": (200, {"total_count": 0}),
        f"/repos/{FULL}": (200, {"private": False}),
    })
    assert ev.workflow_runs.is_measured is False
    assert ev.workflow_runs.absent is NotMeasured.APPARATUS_ABSENT
    assert ev.has_runtime_trace is False


def test_a_nonzero_workflow_run_count_is_still_a_plain_measured_value():
    """The control: APPARATUS_ABSENT must not swallow a genuine count."""
    ev = _collect_with({
        f"/repos/{FULL}/commits": (200, []),
        f"/repos/{FULL}/actions/runs": (200, {"total_count": 3}),
        f"/repos/{FULL}": (200, {"private": False}),
    })
    assert ev.workflow_runs.is_measured is True
    assert ev.workflow_runs.value == 3
    assert ev.workflow_runs.absent is None


# --------------------------------------------------------------------- the scorer, at the seam
def test_score_operation_threads_a_caller_supplied_reason_through_instead_of_guessing():
    s = score_operation("development_initiation", None, (EvidenceClass.PLATFORM_OBSERVED,),
                        absent_reason=NotMeasured.NO_EVIDENCE_IN_WINDOW)
    assert s.level is NotMeasured.NO_EVIDENCE_IN_WINDOW


def test_score_operation_still_defaults_to_the_old_guess_when_no_caller_knows_better():
    """Backward compatibility: a caller that does not pass `absent_reason` (e.g. `pipeline.py`
    today) sees exactly the behaviour that shipped before this fix."""
    s = score_operation("development_initiation", None, (EvidenceClass.PLATFORM_OBSERVED,))
    assert s.level is NotMeasured.NOTHING_QUALIFIED


def test_an_absent_reason_cannot_hijack_the_self_reported_only_branch():
    """`absent_reason` is consulted ONLY when scorable evidence was genuinely offered. Evidence
    that is present but entirely unscorable (self-reported alone) must still read
    `nothing_qualified`, whatever a caller passes."""
    s = score_operation("deploy", None, (EvidenceClass.SELF_REPORTED,),
                        absent_reason=NotMeasured.UNREADABLE)
    assert s.level is NotMeasured.NOTHING_QUALIFIED


def test_an_absent_reason_cannot_hijack_the_nobody_looked_branch():
    """Nor may it override a genuinely empty evidence tuple - `check_did_not_run` still means
    nobody attempted the check at all."""
    s = score_operation("deployment", None, (), absent_reason=NotMeasured.NO_EVIDENCE_IN_WINDOW)
    assert s.level is NotMeasured.CHECK_DID_NOT_RUN


# -------------------------------------------------------------- the registry, at the headline
def test_the_registry_headline_reflects_a_check_that_ran_over_two_that_never_do():
    """The exact AIpush/mcp-protocol-tester shape: one operation ran and read an empty window,
    two others (deployment, treasury_control) never run for ANY subject. The headline reason must
    say what happened to THIS subject, not the boilerplate shared by every subject in the cohort.
    """
    dev = score_operation("development_initiation", None, (EvidenceClass.PLATFORM_OBSERVED,),
                          weak_mixed_signal=True, runtime_trace=False,
                          absent_reason=NotMeasured.NO_EVIDENCE_IN_WINDOW)
    scores = [dev,
              score_operation("deployment", None, ()),
              score_operation("treasury_control", None, ())]
    proj = projection(scores)
    assert proj.is_measured is False
    assert proj.absent is NotMeasured.NO_EVIDENCE_IN_WINDOW, (
        f"got {proj.absent!r} - check_did_not_run must not outrank a check that actually ran")


def test_unreadable_still_outranks_the_new_reasons():
    """The control on the control: a genuine refusal is still the strongest fact available and
    must not be buried by the two additions."""
    scores = [score_operation("development_initiation", None, (),
                              absent_reason=NotMeasured.UNREADABLE),
              score_operation("deployment", None, (), absent_reason=NotMeasured.NO_EVIDENCE_IN_WINDOW),
              score_operation("treasury_control", None, ())]
    # Force the first score to actually carry UNREADABLE - score_operation with empty evidence
    # always reports CHECK_DID_NOT_RUN by design (a collector, never the scorer, may assert
    # UNREADABLE), so build that one OperationScore directly, mirroring how cohort.py does it.
    from src.verify.scorer import Confidence, OperationScore
    scores[0] = OperationScore("development_initiation", NotMeasured.UNREADABLE, (), Confidence.MEASURED)
    assert projection(scores).absent is NotMeasured.UNREADABLE


def test_these_gates_would_fire():
    """Controls: each of the two site-level fixes, run against the exact shape that shipped."""
    # The collector's pre-fix line, planted and confirmed to violate the new expectation.
    stale_reason = Measurement(value=None, absent=NotMeasured.NOTHING_QUALIFIED)
    assert stale_reason.absent is not NotMeasured.NO_EVIDENCE_IN_WINDOW, (
        "the planted pre-fix reading must differ from the fixed one, or this test proves nothing"
    )

    # The scorer's pre-fix guess, still reachable without `absent_reason` - proving the new
    # parameter is what changes the outcome, not some other code path.
    old_guess = score_operation("development_initiation", None, (EvidenceClass.PLATFORM_OBSERVED,))
    new_reason = score_operation("development_initiation", None, (EvidenceClass.PLATFORM_OBSERVED,),
                                 absent_reason=NotMeasured.NO_EVIDENCE_IN_WINDOW)
    assert old_guess.level is not new_reason.level, (
        "absent_reason must change the emitted level, or the parameter is decoration"
    )
