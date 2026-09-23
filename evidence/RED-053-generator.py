#!/usr/bin/env python3
"""Regenerates evidence/RED-053-verified-by-provek-gate-removed.txt.

T-SG-14: `tests/test_verified_by_provek_snippet_is_gated_and_dated.py` is new (CLAUDE.md invariant
5). No component test runner exists in this repository, so the test itself is a source scan over
`web/src/pages/Passport.tsx` - the same shape `tests/test_stale_on_the_surface.py` already uses for
this exact page. The plant mirrors the single most likely accidental regression for a source-scan
test: the CONDITION still exists in the file (`canClaimVerified` is computed, unused, one line
above), but the JSX no longer reads it - `{canClaimVerified && (` becomes `{true && (`, the way a
quick "let me just see the button" edit during development looks, if it were committed by mistake.
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

OUT = ROOT / "evidence" / "RED-053-verified-by-provek-gate-removed.txt"
TARGET = ROOT / "web" / "src" / "pages" / "Passport.tsx"
TEST = "tests/test_verified_by_provek_snippet_is_gated_and_dated.py"

GOOD = "{canClaimVerified && ("
BROKEN = "{true && ("


def _run() -> tuple[int, str]:
    proc = subprocess.run(["python3", "-m", "pytest", TEST, "-q"],
                           cwd=ROOT, capture_output=True, text=True, timeout=60)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def main() -> None:
    original = TARGET.read_text(encoding="utf-8")
    assert original.count(GOOD) == 1, "the expected source shape has moved or is not unique"

    buf = io.StringIO()
    with redirect_stdout(buf):
        print("# RED-053 - Verified-by-Provek button, plant: the status gate is bypassed in the JSX")
        print("#")
        print("# subject: web/src/pages/Passport.tsx, ShareActions's canClaimVerified gate")
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
                print("NOT REPRODUCED: the plant did not turn the suite red.")
                ok = False
            else:
                print("CONFIRMED: with the gate bypassed in the JSX, the source-scan suite fails.")
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
