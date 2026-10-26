"""T-0578 (Fable ruling AUDIT-OPUS-PROVEK-1028 q-1): the collector counts its own calls, the
passport names its window, and the QM2 journal script reads only counted nights.

Each test can fail: dropping the increment in `_api` turns the counter tests red; computing `since`
from now instead of `until` turns the window test red; dropping `evidence_window` from `to_machine`
turns the schema test red; counting a null row in the journal script turns the last two red.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import src.collector.github as gh
from scripts.budget_journal import build_cost_row, parse_cost_line
from scripts.qm2_from_journal import report

FULL = "o/r"
COMMIT = {"sha": "a", "commit": {"author": {"date": "2026-10-01T00:00:00Z"},
                                 "verification": {"verified": True}},
          "author": {"login": "solo", "type": "User"}}


class _P:
    def __init__(self, out):
        self.stdout = out


def _curl(monkeypatch, answers):
    def fake_run(argv, **kw):
        url = argv[-1]
        for fragment, (code, body) in answers.items():
            if fragment in url:
                return _P(f"{json.dumps(body)}\n{code}")
        raise AssertionError(f"unplanned {url}")
    monkeypatch.setattr(gh.subprocess, "run", fake_run)


def test_every_api_read_increments_the_counter_and_rate_limit_does_not(monkeypatch):
    _curl(monkeypatch, {"/rate_limit": (200, {}), "/repos/o/r": (200, {})})
    before = gh.CALLS["n"]
    gh._api("/repos/o/r")
    gh._api("/repos/o/r")
    gh._api("/rate_limit")
    assert gh.CALLS["n"] - before == 2


def test_collect_github_reports_this_subjects_calls_in_its_notes(monkeypatch):
    def fake(path, token=None):
        gh.CALLS["n"] += 1
        if "/commits" in path:
            return 200, [COMMIT]
        if "/actions/runs" in path:
            return 200, {"total_count": 0}
        return 200, {"private": False}
    monkeypatch.setattr(gh, "_api", fake)
    ev = gh.collect_github(FULL)
    assert "github_calls=3" in ev.notes   # repo, commits (short page), runs (none -> no 2nd read)


def test_until_is_the_end_of_the_window_and_since_is_computed_from_it(monkeypatch):
    paths: list[str] = []

    def fake(path, token=None):
        paths.append(path)
        if "/commits" in path:
            return 200, [COMMIT]
        if "/actions/runs" in path:
            return 200, {"total_count": 0}
        return 200, {"private": False}
    monkeypatch.setattr(gh, "_api", fake)
    until = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    gh.collect_github(FULL, until=until)
    commits = next(p for p in paths if "/commits" in p)
    assert f"since={(until - timedelta(days=gh.EVIDENCE_WINDOW_DAYS)).isoformat()}" in commits


def test_last_page_of_a_link_header():
    link = ('<https://api.github.com/repositories/1/commits?per_page=100&page=2>; rel="next", '
            '<https://api.github.com/repositories/1/commits?per_page=100&page=7>; rel="last"')
    assert gh._last_page(link) == 7
    assert gh._last_page(None) is None


def test_passport_carries_the_window_start_and_end():
    from src.abs_profile.evidence import EvidenceClass
    from src.abs_profile.identity import Binding, BindingKind
    from src.abs_profile.ladder import L
    from src.passport.passport import PROFILE_VERSION, PROTOCOL_VERSION, Accountability, Provenance, build
    from src.verify.control_map import ControlMap, Coverage
    from src.verify.scorer import projection, score_operation
    end = datetime(2026, 10, 26, 3, 43, tzinfo=timezone.utc)
    scores = [score_operation("development_initiation", L.L2, (EvidenceClass.PLATFORM_OBSERVED,))]
    p = build(Binding(BindingKind.GIT, FULL), scores, ControlMap([], Coverage([], {}, "")),
              projection(scores), Provenance(PROTOCOL_VERSION, PROFILE_VERSION, 30),
              Accountability(), now=end + timedelta(minutes=5), evidence_window_end=end)
    w = p.to_machine()["evidence_window"]
    assert w == {"start": (end - timedelta(days=30)).isoformat(), "end": end.isoformat()}


def test_cost_line_is_read_from_the_runs_own_text_and_absent_is_none():
    assert parse_cost_line("noise\nCOST github_calls=27\n") == 27
    assert parse_cost_line("COST github_calls=3\nCOST github_calls=9") == 9
    assert parse_cost_line("rate_limited: x") is None


def test_a_counted_row_overrides_a_reset_straddling_null():
    at = datetime(2026, 10, 27, tzinfo=timezone.utc)
    a = {"remaining": 60, "limit": 60, "reset": 1}
    b = {"remaining": 33, "limit": 60, "reset": 2}
    assert build_cost_row(at=at, n_subjects=10, seconds=33, before=a, after=b,
                          waited_seconds=0)["github_calls_measured"] is None
    row = build_cost_row(at=at, n_subjects=10, seconds=33, before=a, after=b, waited_seconds=0,
                         counted=28)
    assert row["github_calls_measured"] == 28 and row["github_calls_absent_reason"] is None


def test_journal_script_says_not_measured_with_no_counted_night():
    old = {"at": "2026-10-05", "subjects": 10, "github_calls_measured": 26}
    null = {"at": "2026-10-24", "subjects": 10, "github_calls_measured": None}
    out = report([json.dumps(old), json.dumps(null)])
    assert "not_measured: 0 counted nights" in out and "capacity" not in out


def test_journal_script_prices_counted_nights_only():
    old = {"at": "a", "subjects": 10, "github_calls_measured": 10}
    new = {"at": "b", "subjects": 10, "github_calls_measured": 30,
           "github_calls_rate_limit_delta": None}
    out = report([json.dumps(old), json.dumps(new)])
    assert "calls_per_subject=3.00" in out and "20 subjects per hour" in out


def test_until_bounds_both_upstream_reads_and_a_live_run_has_no_upper_bound(monkeypatch):
    paths: list[str] = []

    def fake(path, token=None):
        paths.append(path)
        if "/commits" in path:
            return 200, [COMMIT]
        if "/actions/runs" in path:
            return 200, {"total_count": 5}
        return 200, {"private": False}
    monkeypatch.setattr(gh, "_api", fake)
    until = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    gh.collect_github(FULL, until=until)
    commits = next(p for p in paths if "/commits" in p)
    runs = next(p for p in paths if "event=schedule" in p)
    assert "&until=2026-09-01T12:00:00Z" in commits
    assert "created=2026-08-02T12:00:00Z..2026-09-01T12:00:00Z" in runs
    paths.clear()
    gh.collect_github(FULL)
    assert not any("until=" in p or ".." in p for p in paths)


def test_malformed_provek_until_is_refused():
    import subprocess
    import sys
    from os import environ
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    # The push door runs with PROVEK_GITHUB_TOKEN set (T-0571), and cohort.py refuses a token
    # before it reads PROVEK_UNTIL, so the ambient token must not reach this child.
    env = {k: v for k, v in environ.items() if k != "PROVEK_GITHUB_TOKEN"}
    r = subprocess.run([sys.executable, "scripts/cohort.py"], cwd=root,
                       env={**env, "PROVEK_UNTIL": "not-a-date"},
                       capture_output=True, text=True, timeout=120)
    assert r.returncode != 0
    assert "REFUSED: PROVEK_UNTIL='not-a-date'" in (r.stderr + r.stdout)
