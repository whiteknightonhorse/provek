"""Budget exhaustion is OUR fact. It may never be published as the subject's silence.

On 2026-08-31 a rate-exhausted nightly run wrote `unreadable` into live passports: a claim that a
source was asked and did not answer, about sources that were never asked. The guard existed, but
it stood on the FIRST of three reads, so exhaustion arriving mid-window walked straight past it.
"""
import json

import pytest

import src.collector.declaration as decl
import src.collector.github as gh
from src.verify.control_map import GITHUB_DID_NOT_ANSWER, GITHUB_PARTIAL_READ, build_coverage


def _answers(monkeypatch, mapping):
    """Serve a status per URL fragment, so one test can hold two worlds at once."""
    class P:
        def __init__(self, out): self.stdout = out
    def fake_run(argv, **kw):
        url = argv[-1]
        for fragment, (code, body) in mapping.items():
            if fragment in url:
                return P(f"{json.dumps(body)}\n{code}")
        raise AssertionError(f"test did not plan for {url}")
    monkeypatch.setattr(gh.subprocess, "run", fake_run)


SPENT = {"resources": {"core": {"remaining": 0}}}
LEFT = {"resources": {"core": {"remaining": 42}}}


@pytest.mark.parametrize("path", ["/repos/o/r", "/repos/o/r/commits", "/repos/o/r/actions/runs"])
def test_every_read_is_guarded_not_only_the_first(monkeypatch, path):
    _answers(monkeypatch, {path: (429, {})})
    with pytest.raises(gh.RateLimited):
        gh._api(path)


def test_the_rate_limit_endpoint_itself_is_exempt(monkeypatch):
    """It is how the question is asked. Guarding it would recurse forever."""
    _answers(monkeypatch, {"/rate_limit": (429, {})})
    code, _ = gh._api("/rate_limit")
    assert code == 429


def test_a_403_from_a_blocked_repository_is_NOT_ours(monkeypatch):
    """THE CONTROL THAT DISTINGUISHES. GitHub answers 403 for DMCA- and access-blocked
    repositories too. Treating those as our exhaustion would abort the subject while announcing a
    fact about us - misattribution in the opposite direction from the one the guard prevents."""
    _answers(monkeypatch, {"/rate_limit": (200, LEFT), "/repos/o/r": (403, {})})
    code, _ = gh._api("/repos/o/r")
    assert code == 403


def test_a_403_with_a_spent_budget_IS_ours(monkeypatch):
    _answers(monkeypatch, {"/rate_limit": (200, SPENT), "/repos/o/r": (403, {})})
    with pytest.raises(gh.RateLimited):
        gh._api("/repos/o/r")


def test_collect_github_raises_rather_than_returning_evidence(monkeypatch):
    """No GitHubEvidence at all: an object carrying UNREADABLE would be the published lie."""
    _answers(monkeypatch, {"/repos/o/r": (429, {})})
    with pytest.raises(gh.RateLimited):
        gh.collect_github("o/r")


def test_a_throttled_declaration_read_raises_too(monkeypatch):
    """ONE-PLACE: the second reader had its own copy of the same mistake."""
    monkeypatch.setattr(decl, "_fetch_raw", lambda full, ref: (429, ""))
    with pytest.raises(gh.RateLimited):
        decl.collect_declaration("o/r", "deadbeef")


def test_a_404_declaration_still_means_not_declared(monkeypatch):
    """Control: the fix must not swallow the world it sits next to."""
    monkeypatch.setattr(decl, "_fetch_raw", lambda full, ref: (404, ""))
    assert decl.collect_declaration("o/r", "deadbeef") is not None


def test_coverage_names_the_world_it_is_in():
    """`inspected: []` used to carry ONE reason for TWO worlds - and for a repository that
    answered 200 with a failed commits read, that reason was the opposite of the truth."""
    answered_nothing = build_coverage(github_inspected=False)
    partial = build_coverage(github_inspected=False,
                             github_absent_reason=GITHUB_PARTIAL_READ)
    assert answered_nothing.out_of_reach["github"] == GITHUB_DID_NOT_ANSWER
    assert partial.out_of_reach["github"] == GITHUB_PARTIAL_READ
    assert answered_nothing.out_of_reach["github"] != partial.out_of_reach["github"]


def test_a_complete_read_still_reports_github_inspected():
    """The other direction: the fix must not report every subject as uninspected."""
    assert build_coverage(github_inspected=True).inspected
    assert "github" not in build_coverage(github_inspected=True).out_of_reach
