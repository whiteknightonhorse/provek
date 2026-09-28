#!/usr/bin/env python3
"""Regenerates evidence/RED-059-local-ahead-was-collapsed-into-diverged.txt.

T-NM-01 (`GL-NIGHTLY-collision.ruling-1.md`, point 3, second bullet): `scripts/sync_main.sh`
distinguished only two outcomes after `equal` - "$REMOTE/$BRANCH is ahead of HEAD" (fast-forward)
and everything else, printed as DIVERGED. "Everything else" also covered a server that is simply
local ahead of the remote by commits `push.sh` has not sent yet - no divergence at all, since
nobody wrote to `$REMOTE/$BRANCH` outside this script's own model. Collapsing that state into
DIVERGED's wording is invariant 1 (`not_measured` is a state of its own) applied to git: a true
statement about one state borrowed to describe a different one.

The plant removes exactly the branch the fix added - the `git merge-base --is-ancestor
"$REMOTE/$BRANCH" HEAD` check and its message - restoring the pre-fix two-way ladder, then runs the
new regression test against the mutated script.
"""
from __future__ import annotations

import io
import pathlib
import subprocess
import sys
from contextlib import redirect_stdout

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp  # noqa: E402

OUT = ROOT / "evidence" / "RED-059-local-ahead-was-collapsed-into-diverged.txt"
TARGET = ROOT / "scripts" / "sync_main.sh"
CMD = [sys.executable, "-m", "pytest", "-q",
       "tests/test_sync_main_ff.py::test_local_ahead_is_named_honestly_not_as_a_diverged_refusal"]

PLANT_BLOCK = '''
# LOCAL AHEAD IS ITS OWN STATE, NOT A THIRD NAME FOR DIVERGED (invariant 1, applied to git).
# `HEAD` being a strict descendant of `$REMOTE/$BRANCH` is not a divergence - nobody wrote to the
# remote side outside this script's model, this server simply has commits `push.sh` has not sent
# yet. Naming it DIVERGED would tell a reader two histories fought over `main`, when in fact only
# one did and it is only half-published. The exit code stays non-zero either way: a nightly
# measurement still must not run on an unpushed HEAD, because a re-measure of the same 4 commits
# tomorrow is `not_measured`-honest and a pretended pass here is not.
if git merge-base --is-ancestor "$REMOTE/$BRANCH" HEAD; then
  ahead_count="$(git rev-list --count "$REMOTE/$BRANCH"..HEAD)"
  echo "sync_main: HEAD ($local_head) is local ahead by $ahead_count unpushed commit(s) of $REMOTE/$BRANCH ($remote_head) - not diverged, nothing to fast-forward, refusing to measure an unpushed tree" >&2
  exit 1
fi

'''


def _run() -> tuple[int, str]:
    proc = subprocess.run(CMD, cwd=ROOT, capture_output=True, text=True, timeout=60)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def main() -> None:
    original = TARGET.read_text(encoding="utf-8")
    assert PLANT_BLOCK in original, "the branch the fix added is missing before the plant even runs"
    mutated = original.replace(PLANT_BLOCK, "\n", 1)
    assert mutated != original

    buf = io.StringIO()
    with redirect_stdout(buf):
        print("# RED-059 - tests/test_sync_main_ff.py, plant: the local-ahead branch removed from sync_main.sh")
        print("#")
        print(f"# subject: {' '.join(CMD)}")
        print(f"# {evidence_stamp.tree_stamp()}")
        print()
        ok = True
        try:
            TARGET.write_text(mutated, encoding="utf-8")
            rc, out = _run()
            print("--- plant applied (local-ahead branch removed, pre-fix two-way ladder restored) ---")
            print(f"exit code: {rc}")
            print(out)
            print()
            if rc == 0:
                print("NOT REPRODUCED: the plant did not turn the new test red.")
                ok = False
            elif "DIVERGED" not in out:
                print("NOT REPRODUCED: red, but not for the expected reason "
                      "(expected the pre-fix script to print DIVERGED for a local-ahead tree).")
                ok = False
            else:
                print("CONFIRMED: without the local-ahead branch, a server that is simply ahead of "
                      "an unmoved origin/main is told it DIVERGED - the false accusation "
                      "GL-NIGHTLY-collision.ruling-1.md named, reproduced by execution.")
        finally:
            TARGET.write_text(original, encoding="utf-8")

        rc2, out2 = _run()
        print()
        print("--- plant reverted ---")
        print(f"exit code: {rc2}")
        print(out2)
        if rc2 != 0:
            print()
            print("REGRESSION: the test is not green again after reverting the plant.")
            ok = False
        else:
            print()
            print("CONFIRMED: green again on the real tree with the plant reverted.")

    text = buf.getvalue()
    sys.stdout.write(text)
    OUT.write_text(text, encoding="utf-8")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
