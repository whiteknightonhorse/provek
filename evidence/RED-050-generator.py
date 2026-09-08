#!/usr/bin/env python3
"""Regenerates evidence/RED-050-empty-check-runs-read-as-all-green.txt.

Fable's ruling-1 on `e5e613c` (taskloop/disputes/07-automerge-waits-for-itself.ruling-1.md)
rejected that commit: given a head SHA whose check-runs endpoint has registered NOTHING yet (the
state on the very first poll of every real PR, before the other nine checks show up), the loop
read the empty list as `pending -eq 0` and merged the PR before a single real check had run.

This script runs `e5e613c`'s OWN step script - read with PyYAML from that commit via `git show`,
never retyped by hand - through the exact stub-`gh` harness `tests/
test_dependabot_auto_merge_polling.py` uses, and the CURRENT script through the same harness and
the same fixture, side by side. tree: e5e613ce (the commit this task's fixup follows).
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

OUT = ROOT / "evidence" / "RED-050-empty-check-runs-read-as-all-green.txt"
STEP_NAME = t.STEP_NAME
OLD_COMMIT = "e5e613c"


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


def _report(label: str, script_text: str, tmp_root: pathlib.Path) -> tuple[int, bool, int]:
    tmp_path = tmp_root / label.replace(" ", "_")
    tmp_path.mkdir()
    rc, stderr, merged, polls = t._run_script(
        script_text, [[]], tmp_path, wait_limit=2, poll_interval=1,
    )
    print(f"--- {label}: given check-runs == [] on every poll ---")
    print(f"exit code: {rc}")
    print(f"polls made: {polls}")
    print(f"merged: {merged}")
    print("stderr:")
    print(stderr.strip() or "(empty)")
    print()
    return rc, merged, polls


def main() -> None:
    buf = io.StringIO()
    with redirect_stdout(buf):
        print(f"# RED-050 - an empty check-runs list read as \"everything is green\"")
        print(f"#")
        print(f"# subject: the auto-merge poll loop's step script, {OLD_COMMIT} (ruling-1 REJECT) vs current")
        print(f"# {evidence_stamp.tree_stamp()}")
        print()
        with tempfile.TemporaryDirectory() as d:
            tmp_root = pathlib.Path(d)
            rc_old, merged_old, polls_old = _report(f"{OLD_COMMIT} (ruling-1 REJECT)", _old_script(), tmp_root)
            rc_new, merged_new, polls_new = _report("current (this fixup)", t._extract_step_script(), tmp_root)

        print("=" * 100)
        ok = True
        if merged_old and rc_old == 0 and polls_old == 1:
            print(f"CONFIRMED: {OLD_COMMIT} merges on the FIRST poll of an empty check-runs list -")
            print("nothing measured, read as everything green. This is the defect ruling-1 named.")
        else:
            print(f"NOT REPRODUCED: {OLD_COMMIT}'s script did not merge on an empty list as expected -")
            print("the fixture or the extraction may have drifted from the ruling's description.")
            ok = False

        if (not merged_new) and rc_new == 1:
            print("CONFIRMED: the current script refuses to merge on the same empty list, and times")
            print("out with its own named reason instead.")
        else:
            print("REGRESSION: the current script no longer distinguishes an empty check-runs list")
            print("from an all-green one - the fix ruling-1 required is not in the tree.")
            ok = False

    text = buf.getvalue()
    sys.stdout.write(text)
    OUT.write_text(text, encoding="utf-8")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
