"""T-MY-01 - `scripts/dated_promises.py` reads the clock ahead of the door.

The live file is asserted to YIELD a promise, never to be OK: asserting exit 0 on the live
`gates.yml` would be a second clock beside `test_the_mypy_advisory_state_has_not_expired`.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from src.liveness.obligations import RENEWAL_MARGIN

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("dated_promises", ROOT / "scripts" / "dated_promises.py")
dp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dp)

TODAY = "2026-10-19"


def _wf(tmp_path, stamp: str | None) -> str:
    body = "      - name: mypy\n        run: |\n"
    if stamp:
        body += f"          # ADVISORY-UNTIL: {stamp} - see README\n"
    body += "          mypy src\n"
    f = tmp_path / "gates.yml"
    f.write_text("jobs:\n  lint:\n    steps:\n" + body, encoding="utf-8")
    return str(f)


def _run(tmp_path, stamp, capsys, today=TODAY):
    rc = dp.main(["--file", _wf(tmp_path, stamp), "--today", today])
    return rc, capsys.readouterr().out


def test_a_far_date_is_ok(tmp_path, capsys):
    rc, out = _run(tmp_path, "2026-12-14", capsys)
    assert rc == 0 and "mypy: until 2026-12-14, 56 days left, stage=OK" in out


def test_five_days_out_is_warn_and_prints_the_remedy(tmp_path, capsys):
    assert 5 <= RENEWAL_MARGIN.days
    rc, out = _run(tmp_path, "2026-10-24", capsys)
    assert rc == 1 and "stage=WARN" in out and "ratify a new date in DECISIONS.md" in out


def test_one_day_out_is_last_day(tmp_path, capsys):
    rc, out = _run(tmp_path, "2026-10-20", capsys)
    assert rc == 1 and "stage=LAST_DAY" in out


def test_a_past_date_is_expired_and_says_how_long_ago(tmp_path, capsys):
    rc, out = _run(tmp_path, "2026-10-15", capsys)
    assert rc == 1 and "stage=EXPIRED" in out and "4 days ago" in out


def test_no_sentinel_is_not_measured_not_nothing_due(tmp_path, capsys):
    rc, out = _run(tmp_path, None, capsys)
    assert rc == 2 and "not_measured" in out


def test_an_unreadable_file_is_exit_2(tmp_path, capsys):
    assert dp.main(["--file", str(tmp_path / "absent.yml"), "--today", TODAY]) == 2
    assert "not_measured" in capsys.readouterr().out


def test_the_live_workflow_yields_at_least_one_promise():
    found = dp.promises((ROOT / ".github" / "workflows" / "gates.yml").read_text(encoding="utf-8"))
    assert len(found) >= 1
