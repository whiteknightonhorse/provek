#!/usr/bin/env python3
"""Regenerates evidence/RED-051-a-stale-run-of-the-same-job-read-as-a-red-check.txt.

T-08 measured on PR #18's head `19a69821` (`check-runs?filter=all`, both `filter=all` and the
default returned the identical 19 rows): the head SHA carried TWO check-runs named "auto-merge" -
one `cancelled` (GitHub's own six-hour kill of a run from before the 69fb4e1 fixup) and this run's
own. `69fb4e1`'s self-exclusion filtered by `$GITHUB_RUN_ID` inside `details_url`, which drops only
the CURRENT run's own check-run - the stale `cancelled` one stayed in `$others`, read as a red
check, and the merge failed six seconds after starting: `##[error]red check(s) on 19a69821...,
not merging: auto-merge`.

This script runs `69fb4e1`'s OWN step script - read with PyYAML from that commit via `git show`,
never retyped by hand - through the exact stub-`gh` harness `tests/
test_dependabot_auto_merge_polling.py` uses, and the CURRENT script through the same harness and
the same fixture (nine green real checks, this run's own "auto-merge" still `in_progress`, PLUS a
stale "auto-merge" from a different, earlier run id with `conclusion: cancelled`), side by side.
"""
from __future__ import annotations

import io
import pathlib
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "scripts"))
import test_dependabot_auto_merge_polling as t  # noqa: E402
import evidence_stamp  # noqa: E402

OUT = ROOT / "evidence" / "RED-051-a-stale-run-of-the-same-job-read-as-a-red-check.txt"
STEP_NAME = t.STEP_NAME
OLD_COMMIT = "69fb4e1"


def _old_script() -> str:
    text = subprocess.run(
        ["git", "show", f"{OLD_COMMIT}:.github/workflows/dependabot-auto-merge.yml"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    doc = yaml.safe_load(text)
    for step in doc["jobs"]["auto-merge"]["steps"]:
        if step.get("name") == STEP_NAME:
            return step["run"]
    raise AssertionError(f"{STEP_NAME!r} not found in {OLD_COMMIT}")


def _stale_run_checks() -> list[dict]:
    checks = t._green_checks()
    checks.append({
        "name": "auto-merge", "status": "completed", "conclusion": "cancelled",
        "details_url": "https://github.com/whiteknightonhorse/provek/actions/runs/999/job/3",
    })
    return checks


def _report(label: str, script_text: str, tmp_root: pathlib.Path) -> tuple[int, bool, str]:
    tmp_path = tmp_root / label.replace(" ", "_").replace("(", "").replace(")", "")
    tmp_path.mkdir()
    # 69fb4e1's script still reads $GITHUB_RUN_ID; the current script no longer does but tolerates
    # the extra env var being set, so one env setup exercises both scripts identically.
    import os
    env_job_name = "auto-merge"
    old_env = os.environ.get("GITHUB_RUN_ID")
    os.environ["GITHUB_RUN_ID"] = "111"
    try:
        rc, stderr, merged, polls = t._run_script(
            script_text, [_stale_run_checks()], tmp_path, job_name=env_job_name,
        )
    finally:
        if old_env is None:
            os.environ.pop("GITHUB_RUN_ID", None)
        else:
            os.environ["GITHUB_RUN_ID"] = old_env
    print(f"--- {label}: nine green checks + self (in_progress) + a STALE cancelled "
          f"\"auto-merge\" from a different run id ---")
    print(f"exit code: {rc}")
    print(f"polls made: {polls}")
    print(f"merged: {merged}")
    print("stderr:")
    print(stderr.strip() or "(empty)")
    print()
    return rc, merged, stderr


def main() -> None:
    buf = io.StringIO()
    with redirect_stdout(buf):
        print("# RED-051 - a stale check-run from an earlier run of the SAME job read as a red check")
        print("#")
        print(f"# subject: the auto-merge poll loop's step script, {OLD_COMMIT} (T-07 fixup) vs current")
        print(f"# {evidence_stamp.tree_stamp()}")
        print()
        with tempfile.TemporaryDirectory() as d:
            tmp_root = pathlib.Path(d)
            rc_old, merged_old, stderr_old = _report(f"{OLD_COMMIT} (T-07 fixup)", _old_script(), tmp_root)
            rc_new, merged_new, stderr_new = _report("current (this fixup)", t._extract_step_script(), tmp_root)

        print("=" * 100)
        ok = True
        if (not merged_old) and rc_old == 1 and "auto-merge" in stderr_old:
            print(f"CONFIRMED: {OLD_COMMIT}'s script reads the stale, unrelated \"auto-merge\" run as a")
            print("red check and refuses to merge - the exact failure measured on PR #18's head 19a69821.")
        else:
            print(f"NOT REPRODUCED: {OLD_COMMIT}'s script did not fail on the stale run as expected -")
            print("the fixture or the extraction may have drifted from what was measured live.")
            ok = False

        if merged_new and rc_new == 0:
            print("CONFIRMED: the current script excludes every check-run named after this job,")
            print("not just the run currently executing, and merges on nine real green checks.")
        else:
            print("REGRESSION: the current script still treats a stale run of its own job as a red")
            print("check - the T-08 fix is not in the tree.")
            ok = False

    text = buf.getvalue()
    sys.stdout.write(text)
    OUT.write_text(text, encoding="utf-8")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
