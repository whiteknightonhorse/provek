"""T-01-ci-red-isoformat-z: `parse_iso_ts` is the ONE place a `Z`-terminated ISO-8601 timestamp gets
read in this repository (LAW #ONE-PLACE, `src/abs_profile/isotime.py`). Before this fix
`src/collector/repo.py:116` called `datetime.fromisoformat` directly on a git-produced commit date
and crashed outright on Python 3.10 the first time that date carried a trailing `Z` - see
`tests/test_collector_repo.py::test_oldest_commit_line_with_a_trailing_Z_does_not_crash_the_read`
for the mutation control on that specific call site; this file controls the shared function itself.
"""
from datetime import datetime, timezone

from src.abs_profile.isotime import parse_iso_ts


def test_a_trailing_Z_parses_as_utc():
    """THE DEFECT ITSELF. Python 3.10's `datetime.fromisoformat` raises ValueError on a trailing
    `Z`; the whole point of this module is that its caller never sees that exception."""
    assert parse_iso_ts("2026-09-03T02:35:56Z") == datetime(2026, 9, 3, 2, 35, 56,
                                                             tzinfo=timezone.utc)


def test_an_explicit_offset_still_parses():
    """THE CONTROL FOR THE OTHER WORLD. A fix that only handled `Z` and broke the pre-existing
    `+00:00` spelling would trade one defect for another."""
    assert parse_iso_ts("2026-09-03T02:35:56+00:00") == datetime(2026, 9, 3, 2, 35, 56,
                                                                 tzinfo=timezone.utc)


def test_a_naive_timestamp_is_stamped_utc_not_left_ambiguous():
    assert parse_iso_ts("2026-09-03T02:35:56") == datetime(2026, 9, 3, 2, 35, 56,
                                                            tzinfo=timezone.utc)


def test_garbage_is_none_not_a_raised_error():
    """Matches this repository's own `NotMeasured` discipline: a read failure is a state, never an
    exception the caller must remember to catch."""
    assert parse_iso_ts("not a timestamp") is None
    assert parse_iso_ts("20 August 2026") is None


def test_a_non_string_is_none():
    assert parse_iso_ts(None) is None
    assert parse_iso_ts(12345) is None
