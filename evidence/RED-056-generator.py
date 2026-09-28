#!/usr/bin/env python3
"""Regenerates evidence/RED-056-a-changed-digest-formula-would-still-read-golden.txt.

T-GL-04: `tests/test_genlayer_witness_digest_matches_provek.py` is new (CLAUDE.md invariant 5). The
plant changes `_digest`'s field separator from `"|"` to `","` - the exact shape of drift that would
silently break the one guarantee `integrations/genlayer-witness/tests/fixtures/digest_golden.json`
exists to pin: that this repository's own digest formula still produces what the GenLayer
contract's `_url_reachable_digest` (a separate Python 3.12 reader of the same fixture) independently
computes.
"""
from __future__ import annotations

import io
import os
import pathlib
import subprocess
import sys
from contextlib import redirect_stdout

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp  # noqa: E402

OUT = ROOT / "evidence" / "RED-056-a-changed-digest-formula-would-still-read-golden.txt"
TARGET = ROOT / "src" / "witness" / "witness.py"
TEST = "tests/test_genlayer_witness_digest_matches_provek.py"

GOOD = 'return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()'
BROKEN = 'return hashlib.sha256(",".join(parts).encode("utf-8")).hexdigest()'


def _run() -> tuple[int, str]:
    # `PYTHONDONTWRITEBYTECODE=1`, and not decoration: GOOD and BROKEN are the same length
    # (`"|"` and `","`, one character each), so a `.pyc` cache keyed on mtime+size can read the
    # REVERTED file as unchanged from the BROKEN one written moments earlier when both writes land
    # in the same filesystem-timestamp tick - measured here (both showed `1 failed` even after the
    # file on disk was back to GOOD) before this line was added.
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.run(["python3", "-m", "pytest", TEST, "-q"],
                           cwd=ROOT, capture_output=True, text=True, timeout=60, env=env)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def main() -> None:
    original = TARGET.read_text(encoding="utf-8")
    assert original.count(GOOD) == 1, "the expected source shape has moved or is not unique"

    buf = io.StringIO()
    with redirect_stdout(buf):
        print("# RED-056 - golden vector, plant: _digest's field separator changed")
        print("#")
        print(f"# subject: {TEST}")
        print(f"# {evidence_stamp.tree_stamp()}")
        print()
        ok = True
        try:
            TARGET.write_text(original.replace(GOOD, BROKEN, 1), encoding="utf-8")
            rc, out = _run()
            print(f"--- plant applied ({TEST}) ---")
            print(f"exit code: {rc}")
            print(out)
            print()
            if rc == 0:
                print("NOT REPRODUCED: the plant did not turn the golden-vector test red.")
                ok = False
            else:
                print("CONFIRMED: a changed digest formula no longer matches the golden vector "
                      "the contract-side reader agreed to.")
        finally:
            TARGET.write_text(original, encoding="utf-8")

        rc2, out2 = _run()
        print()
        print(f"--- plant reverted ({TEST}) ---")
        print(f"exit code: {rc2}")
        print(out2)
        if rc2 != 0:
            print()
            print("REGRESSION: the suite is not green again after reverting the plant.")
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
