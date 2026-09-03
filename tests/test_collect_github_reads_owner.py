"""AUD-013 (Fable, 2026-09-03): `derive_affiliation` (`scripts/cohort.py`) needs the repository's
CURRENT owner on every pass, not the owner recorded once at intake. This pins the other half of
that fix at its source: `GitHubEvidence.owner` must come off the SAME `/repos/{full_name}` response
`private` already reads - no second `api.github.com` call, and no cost to the anonymous budget the
rest of this project's rate-limit accounting depends on.

Same `_patched_api` technique as `tests/test_absence_reasons_reflect_what_ran.py`.
"""
from __future__ import annotations

import src.collector.github as gh

FULL = "whiteknightonhorse/AIpush"


def _patched_api(responses):
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


def test_MUTATION_owner_login_is_read_off_the_repos_response():
    """RED with `owner=` dropped from `collect_github`'s return (the pre-fix shape): `ev.owner` is
    `None` even though the repository answered. GREEN: the login already sitting in the `/repos`
    payload comes through."""
    ev = _collect_with({
        f"/repos/{FULL}/commits": (200, []),
        f"/repos/{FULL}/actions/runs": (200, {"total_count": 0}),
        f"/repos/{FULL}": (200, {"private": False, "owner": {"login": "whiteknightonhorse"}}),
    })
    assert ev.owner == "whiteknightonhorse"


def test_a_repository_that_did_not_answer_reads_owner_as_none_not_a_guess():
    """404/refused: nothing about the subject is known, including who owns it now - `owner` must
    stay `None` rather than default to the caller's own name or an empty string."""
    ev = _collect_with({f"/repos/{FULL}": (404, None)})
    assert ev.read is False
    assert ev.owner is None


def test_a_response_missing_the_owner_key_reads_as_none_not_a_crash():
    """Defensive against a `/repos` payload that answers 200 but, for whatever reason, carries no
    `owner` object at all - `.get()` chained, not `["owner"]["login"]`, so this reads `None`
    instead of raising `KeyError`/`TypeError`."""
    ev = _collect_with({
        f"/repos/{FULL}/commits": (200, []),
        f"/repos/{FULL}/actions/runs": (200, {"total_count": 0}),
        f"/repos/{FULL}": (200, {"private": False}),
    })
    assert ev.owner is None
