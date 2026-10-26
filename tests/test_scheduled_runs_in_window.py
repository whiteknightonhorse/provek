"""T-0570 (Fable ruling AUDIT-OPUS-PROVEK-1028 q-1): the runtime trace of limiter O2 is a workflow
run started by `schedule` inside the 30-day window, not the lifetime count of runs of any trigger.

Each test can fail: reverting `has_runtime_trace` to `workflow_runs > 0` turns the first red (1 000
lifetime runs, none scheduled, used to pass the limiter); dropping the second call turns the
others red.
"""
from __future__ import annotations

import src.collector.github as gh
from src.abs_profile.evidence import EvidenceClass
from src.abs_profile.ladder import L
from src.abs_profile.measured import NotMeasured
from src.verify.scorer import WEAK_SIGNAL_CEILING, score_operation

FULL = "whiteknightonhorse/AIpush"
COMMIT = {"sha": "a", "commit": {"author": {"date": "2026-10-01T00:00:00Z"},
                                 "verification": {"verified": True}},
          "author": {"login": "solo", "type": "User"}}


def _collect(runs_total, scheduled):
    """`scheduled` is a response tuple for the event=schedule call. Returns (evidence, paths)."""
    paths: list[str] = []

    def fake(path, token=None):
        paths.append(path)
        if path.startswith(f"/repos/{FULL}/commits"):
            return 200, [COMMIT]
        if path.startswith(f"/repos/{FULL}/actions/runs"):
            if "event=schedule" in path:
                assert "created=>=" in path, "the scheduled read must carry the window start"
                return scheduled
            return 200, {"total_count": runs_total}
        return 200, {"private": False}
    orig = gh._api
    gh._api = fake
    try:
        return gh.collect_github(FULL), paths
    finally:
        gh._api = orig


def _score(ev):
    return score_operation("development_initiation", L.L4, (EvidenceClass.PLATFORM_OBSERVED,),
                           weak_mixed_signal=True, runtime_trace=ev.has_runtime_trace,
                           trace_read=ev.runtime_trace_read)


def test_a_thousand_lifetime_runs_and_no_scheduled_run_in_the_window_is_capped():
    ev, _ = _collect(1000, (200, {"total_count": 0}))
    assert ev.workflow_runs.value == 1000
    assert ev.scheduled_runs_in_window.is_measured and ev.scheduled_runs_in_window.value == 0
    s = _score(ev)
    assert s.level is WEAK_SIGNAL_CEILING
    assert "O2:no_scheduled_run_in_window->capped_L2" in s.limiters_applied


def test_one_scheduled_run_in_the_window_is_a_trace():
    ev, _ = _collect(1000, (200, {"total_count": 1}))
    assert ev.has_runtime_trace is True
    assert not any(x.startswith("O2") for x in _score(ev).limiters_applied)


def test_http_500_on_the_scheduled_read_is_unreadable_and_says_trace_not_measured():
    ev, _ = _collect(1000, (500, None))
    assert ev.scheduled_runs_in_window.absent is NotMeasured.UNREADABLE
    assert ev.runtime_trace_read is False
    assert any("scheduled CI runs not read, HTTP 500" in n for n in ev.notes)
    s = _score(ev)
    assert s.level is WEAK_SIGNAL_CEILING
    assert "O2:trace_not_measured->capped_L2" in s.limiters_applied


def test_no_apparatus_at_all_costs_one_runs_call_only():
    ev, paths = _collect(0, (500, None))
    assert ev.scheduled_runs_in_window.absent is NotMeasured.APPARATUS_ABSENT
    assert sum("/actions/runs" in p for p in paths) == 1
    assert not any("event=schedule" in p for p in paths)
