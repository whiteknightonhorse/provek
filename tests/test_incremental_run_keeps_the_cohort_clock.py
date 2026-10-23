"""T-IN-02 / D-68 - a PROVEK_ONLY run carries the document's `generated_at` forward.

THE INCIDENT, 2026-10-23 04:45-05:05: an intake run of ONE subject re-stamped `generated_at` on
the whole registry while nine rows kept the `valid_until` the 03:43:06 daily run gave them. The
window `findings()` compares was then 30 d - 1 h 22 min against a 30 d need with 1 h of
`POLICY_TOLERANCE`, so `DEADLINE TOO LATE TO ACT ON` fired and push.sh refused five commits.
The tolerance is for clock drift inside one run; an intake run is not a cohort run.
"""
from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.liveness import commitments as C
from src.liveness.obligations import MAX_AGE, PASSPORT_VALIDITY, Interval
from src.registry.public_registry import PublicRegistry, Row, Status, document_clock
from src.transport.erc8004_deployment import RecordState, TargetState

ROOT = Path(__file__).resolve().parents[1]
T = datetime(2026, 10, 23, 3, 43, 6, tzinfo=timezone.utc)


def _row(sid: str, issued: datetime) -> Row:
    return Row(sid, Status.VERIFIED, "p", None, "1.0", issued + PASSPORT_VALIDITY, f"ref/{sid}",
               verifier_affiliation="none", issued_at=issued)


def test_the_emitter_stamps_the_given_clock_and_leaves_row_times_at_now(tmp_path):
    now = T + timedelta(minutes=82)
    reg = PublicRegistry(tmp_path)
    reg.upsert(_row("a", now))
    doc = reg.to_machine(now, generated_at=T)
    assert doc["generated_at"] == T.isoformat()
    assert doc["subjects"][0]["issued_at"] == now.isoformat()
    assert doc["subjects"][0]["valid_until"] == (now + PASSPORT_VALIDITY).isoformat()
    assert reg.to_machine(now)["generated_at"] == now.isoformat()   # full runs unchanged


def _findings(generated_at: datetime) -> list[str]:
    # nine rows from the 03:43:06 daily run, one measured 82 minutes later by the intake run
    valid_until = T + PASSPORT_VALIDITY
    run = C.CohortRun(C.ReadState.READ, generated_at=generated_at,
                      earliest_valid_until=valid_until, rows=10)
    watch = C.TargetWatch(RecordState.READ, checked_at=generated_at, target=TargetState.NO_TARGET)
    return [f for f in C.findings(run, generated_at, watch) if "DEADLINE TOO LATE" in f]


def test_mutation_the_incident_shape_is_red_and_the_carried_shape_is_green():
    """MUTATION CONTROL, the arithmetic of 2026-10-23: document stamped T+82 min over rows that
    lapse at T+30 d is a 30 d - 82 min window against a 30 d need, 22 min past the 1 h tolerance."""
    assert MAX_AGE[Interval.BEFORE_REISSUE] + C.RENEWAL_MARGIN - PASSPORT_VALIDITY \
        <= timedelta(hours=1), "premise: a window carried unmoved is inside the tolerance"
    stamped_by_the_intake_run = _findings(T + timedelta(minutes=82))
    assert len(stamped_by_the_intake_run) == 1, stamped_by_the_intake_run
    assert _findings(T) == []


def test_the_chooser_carries_for_incremental_and_defers_for_full():
    assert document_clock(True, T) == T
    assert document_clock(False, T) is None
    assert document_clock(False, None) is None


def test_an_incremental_run_with_no_previous_clock_refuses():
    with pytest.raises(ValueError, match="REFUSED: incremental run with no previous cohort clock"):
        document_clock(True, None)


def _cohort_tree() -> ast.Module:
    return ast.parse((ROOT / "scripts" / "cohort.py").read_text(encoding="utf-8"))


def test_the_only_branch_hands_the_previous_clock_to_the_emitter():
    """Able to fail: change `registry.write(now, DOCUMENT_CLOCK)` back to `registry.write(now)`
    and the write call has one argument; change the `document_clock(bool(ONLY), ...)` first
    argument to `False` and the chooser is no longer told about ONLY. Either turns this red."""
    tree = _cohort_tree()
    writes = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
              and isinstance(n.func, ast.Attribute) and n.func.attr == "write"
              and isinstance(n.func.value, ast.Name) and n.func.value.id == "registry"]
    assert len(writes) == 1
    assert [ast.unparse(a) for a in writes[0].args] == ["now", "DOCUMENT_CLOCK"]
    chosen = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
              and isinstance(n.func, ast.Name) and n.func.id == "document_clock"]
    assert len(chosen) == 1
    assert ast.unparse(chosen[0].args[0]) == "bool(ONLY)"
    assert "previous_generated_at()" in ast.unparse(chosen[0].args[1])
