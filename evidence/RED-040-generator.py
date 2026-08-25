#!/usr/bin/env python3
"""Produces evidence/RED-040-an-unstamped-file-would-have-passed-silently.txt.

WHAT THIS PROVES (invariant 5: "the section exists" is not a test). T-S14 added
`scripts/evidence_stamp.py` and `scripts/ratchet_evidence.py` - a helper that writes `tree: <sha>`
into an artefact's header, and a ratchet that refuses any file under `evidence/` that lacks one and
is not named in `requirements/EVIDENCE_LEGACY.txt`. A ratchet that has only ever been run against a
tree it already agrees with cannot be told apart from `return []`. This file plants a REAL,
unstamped file directly in `evidence/`, runs the ratchet as a subprocess against the actual working
tree, and keeps the verbatim red output - then removes the plant and proves the ratchet is clean
again, so the artefact also shows the gate is not left in whatever state the mutation left it.

SELF-APPLICATION. This file's own OUTPUT carries the stamp it argues for, produced by the same
`evidence_stamp.tree_stamp()` every `*-generator.py` now calls - the task's own completion
criterion asks for exactly that, and a generator preaching a rule its own artefact does not follow
would be the asymmetry §3.1 of SPEC.md was corrected for once already.

ONE MUTATION, NOT SIX, AND THAT IS THE RIGHT SHAPE HERE. RED-032's six mutations attack six
distinct ways a REGEX could be wrong; this ratchet has exactly one behaviour to demonstrate - an
evidence file with no stamp and no legacy exemption is refused - so a second or third mutation
would be the same fact restated, which RED-032's own generator refuses on sight (`dead in seen`).

WHAT THIS FILE DOES TO THE WORKING TREE, AND WHAT IT PROMISES ABOUT IT. It creates one file under
`evidence/`, proves the marker landed, runs the ratchet, deletes the file in a `finally`, and
refuses to write the artefact unless the ratchet is provably clean both before the plant and after
the removal. A run that leaves the plant behind, or that cannot restore a clean ratchet, writes
nothing.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp  # noqa: E402

OUT = ROOT / "evidence" / "RED-040-an-unstamped-file-would-have-passed-silently.txt"
RATCHET = ROOT / "scripts" / "ratchet_evidence.py"
VICTIM = ROOT / "evidence" / "_red040-planted-unstamped.txt"
VICTIM_TEXT = (
    "This file was planted by evidence/RED-040-generator.py to prove\n"
    "scripts/ratchet_evidence.py refuses an unstamped, non-legacy evidence file.\n"
    "It carries no revision stamp anywhere in it.\n"
)


def run_ratchet() -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(RATCHET)], cwd=ROOT,
                        capture_output=True, text=True, timeout=60, check=False)
    return p.returncode, (p.stdout + p.stderr).strip()


def main() -> int:
    if VICTIM.exists():
        print(f"REFUSED: {VICTIM} already exists - clean up before running this.")
        return 1

    rc_before, out_before = run_ratchet()
    if rc_before != 0:
        print(f"REFUSED: the ratchet is not clean before any mutation (exit {rc_before}).\n"
              f"{out_before}")
        return 1

    try:
        VICTIM.write_text(VICTIM_TEXT, encoding="utf-8")
        if not VICTIM.exists() or "tree:" in VICTIM.read_text(encoding="utf-8"):
            print("REFUSED: the plant did not land as an unstamped file.")
            return 1

        rc_red, out_red = run_ratchet()
    finally:
        VICTIM.unlink(missing_ok=True)

    if VICTIM.exists():
        print(f"REFUSED: {VICTIM} was not removed.")
        return 1
    if rc_red != 1:
        print(f"REFUSED: planting the unstamped file did not exit 1 (got {rc_red}) - only exit 1 "
              f"is a ratchet that RAN and refused.\n{out_red}")
        return 1
    if VICTIM.name not in out_red or "no 'tree:" not in out_red:
        print(f"REFUSED: the red output does not name the planted file and its actual reason.\n"
              f"{out_red}")
        return 1

    rc_after, out_after = run_ratchet()
    if rc_after != 0:
        print(f"REFUSED: the ratchet is not clean again after the plant was removed (exit "
              f"{rc_after}).\n{out_after}")
        return 1

    body = f"""# RED-040 - an unstamped file would have passed silently before this task
#
# {evidence_stamp.tree_stamp()}
#
# Produced by evidence/RED-040-generator.py, checked in beside this file so the run below can be
# repeated rather than believed. Proves scripts/ratchet_evidence.py CAN FAIL (invariant 5): a real,
# unstamped file was written directly into evidence/, judged by the ratchet as a subprocess against
# the actual working tree, and removed again - each state captured in its own buffer rather than
# assumed from the fact that a file was written.
#
# SUBJECT: scripts/ratchet_evidence.py, arming LAW-EVIDENCE-STAMPED-TREE (D-39, T-S14).

{"=" * 100}
BEFORE THE PLANT - `python3 scripts/ratchet_evidence.py`, exit {rc_before}
{"=" * 100}

{out_before}

{"=" * 100}
THE PLANT - evidence/_red040-planted-unstamped.txt, verbatim
{"=" * 100}

{VICTIM_TEXT}
{"=" * 100}
WITH THE PLANT IN PLACE - `python3 scripts/ratchet_evidence.py`, exit {rc_red}
{"=" * 100}

{out_red}

{"=" * 100}
AFTER THE PLANT WAS REMOVED - `python3 scripts/ratchet_evidence.py`, exit {rc_after}
{"=" * 100}

{out_after}
"""
    OUT.write_text(body, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
