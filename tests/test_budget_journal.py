"""T-76 (Fable ruling, 2026-09-05) - the anonymous budget gate `scripts/budget_journal.py` adds to
the nightly re-measure. The measured failure: ten subjects each paid for a 403 plus a confirming
`/rate_limit` read against a budget that was ALREADY zero before `cohort.py`'s first request -
spent by a neighbour sharing this host's address, not by the cohort. These tests pin the arithmetic
that replaces "burn ten reads to discover what one `/rate_limit` read already knew".
"""
from __future__ import annotations

from datetime import datetime, timezone

from scripts.budget_journal import build_cost_row, parse_core, wait_seconds_for

SPENT = {"resources": {"core": {"remaining": 0, "limit": 60, "reset": 1_000_060}}}
ROOMY = {"resources": {"core": {"remaining": 28, "limit": 60, "reset": 1_000_060}}}


def test_parse_core_reads_the_three_measured_fields():
    assert parse_core(SPENT) == {"remaining": 0, "limit": 60, "reset": 1_000_060}


def test_parse_core_is_none_for_an_unreadable_endpoint():
    """`None` in - curl failed, or GitHub sent something that is not JSON - and `None` out. Never
    a zero: an unread instrument is not the same fact as an empty budget."""
    assert parse_core(None) is None
    assert parse_core({}) is None
    assert parse_core({"resources": {}}) is None
    assert parse_core({"resources": {"core": {"remaining": 0}}}) is None  # limit/reset missing


def test_MUTATION_an_empty_budget_with_a_future_reset_waits_exactly_that_long():
    """RED with the pre-fix nightly chain (no gate at all): ten subjects spend ten reads against a
    budget already at zero. GREEN: one wait, computed from the measured `reset`, zero subject reads
    burnt discovering what this call already knows."""
    core = parse_core(SPENT)
    assert wait_seconds_for(core, now_epoch=1_000_000) == 60


def test_a_reset_already_in_the_past_waits_zero_not_negative():
    core = parse_core(SPENT)
    assert wait_seconds_for(core, now_epoch=1_000_200) == 0


def test_a_budget_with_room_waits_zero():
    core = parse_core(ROOMY)
    assert wait_seconds_for(core, now_epoch=1_000_000) == 0


def test_an_unreadable_rate_limit_endpoint_waits_zero_not_treated_as_empty():
    """The instrument failing is `not_measured`, not license to assume the worst-case wait."""
    assert wait_seconds_for(None, now_epoch=1_000_000) == 0


NOW = datetime(2026, 9, 5, 6, 0, 0, tzinfo=timezone.utc)


def test_cost_row_measures_the_real_difference_of_two_reads():
    before = parse_core({"resources": {"core": {"remaining": 60, "limit": 60, "reset": 1_000_060}}})
    after = parse_core({"resources": {"core": {"remaining": 30, "limit": 60, "reset": 1_000_060}}})
    row = build_cost_row(at=NOW, n_subjects=10, seconds=20, before=before, after=after,
                         waited_seconds=0)
    assert row["github_calls_measured"] == 30
    assert row["github_calls_absent_reason"] is None
    assert row["remaining_before"] == 60
    assert row["remaining_after"] == 30
    assert row["limit"] == 60
    assert "github_calls_assumed" not in row


def test_MUTATION_an_unreadable_read_yields_absence_not_a_guessed_number():
    """RED with a naive `before - after`: `None - None` raises, or a silent `.get(..., 0)` would
    publish a fabricated zero. GREEN: named absence, same discipline as `skip_rate_limited`."""
    row = build_cost_row(at=NOW, n_subjects=10, seconds=20, before=None, after=None,
                         waited_seconds=0)
    assert row["github_calls_measured"] is None
    assert row["github_calls_absent_reason"] == "rate_limit_endpoint_unreadable"


def test_MUTATION_a_window_reset_mid_run_is_named_not_arithmetic():
    """The hourly window rolled over between the two reads - `after.remaining - before.remaining`
    would silently count a fresh hour's budget this run never spent. Named instead."""
    before = parse_core({"resources": {"core": {"remaining": 2, "limit": 60, "reset": 1_000_060}}})
    after = parse_core({"resources": {"core": {"remaining": 55, "limit": 60, "reset": 1_003_660}}})
    row = build_cost_row(at=NOW, n_subjects=10, seconds=20, before=before, after=after,
                         waited_seconds=0)
    assert row["github_calls_measured"] is None
    assert row["github_calls_absent_reason"] == "window_reset_during_run"


def test_seconds_per_subject_and_zero_subjects_stay_none_not_a_zero_division():
    row = build_cost_row(at=NOW, n_subjects=0, seconds=19, before=None, after=None,
                         waited_seconds=0)
    assert row["seconds_per_subject"] is None
    assert row["subjects"] == 0
