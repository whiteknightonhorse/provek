#!/usr/bin/env python3
"""Regenerates evidence/RED-052-plain-badge-defect-still-prints-the-projection.txt.

T-SG-14: `tests/test_badge_plain_variant_drops_the_number.py` is new, so CLAUDE.md invariant 5 ("a
test MUST BE ABLE TO FAIL") is checked here directly rather than by citing a past incident. The
plant disables `healthySvg`'s `if (plain) { ... }` early return (renamed to `if (false && plain)`,
one token changed) so a `?plain=1` request falls through to the numbered rendering exactly as it
would if a future edit moved code around this guard and broke it - the single most likely way this
feature regresses, since `onRequestGet` still passes `plain: true` through unchanged and a diff
that only touched `healthySvg` would look small.
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

OUT = ROOT / "evidence" / "RED-052-plain-badge-defect-still-prints-the-projection.txt"
TARGET = ROOT / "web" / "functions" / "badge" / "[id].js"
TEST = "tests/test_badge_plain_variant_drops_the_number.py"

GOOD = "  if (plain) {"
BROKEN = "  if (false && plain) {"


def _run() -> tuple[int, str]:
    proc = subprocess.run(["python3", "-m", "pytest", TEST, "-q"],
                           cwd=ROOT, capture_output=True, text=True, timeout=60)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def main() -> None:
    original = TARGET.read_text(encoding="utf-8")
    assert GOOD in original, "the expected source shape has moved - update GOOD/BROKEN above"

    buf = io.StringIO()
    with redirect_stdout(buf):
        print("# RED-052 - plain badge, plant: healthySvg's if (plain) early return disabled")
        print("#")
        print("# subject: web/functions/badge/[id].js, healthySvg's plain-vs-numbered branch")
        print(f"# {evidence_stamp.tree_stamp()}")
        print()
        ok = True
        try:
            TARGET.write_text(original.replace(GOOD, BROKEN), encoding="utf-8")
            rc, out = _run()
            print(f"--- plant applied ({TEST}) ---")
            print(f"exit code: {rc}")
            print(out)
            print()
            if rc == 0:
                print("NOT REPRODUCED: the plant did not turn the suite red - the test does not "
                      "cover this source shape.")
                ok = False
            else:
                print("CONFIRMED: with the plain guard disabled, ?plain=1 falls through to the "
                      "numbered rendering and the plain-badge test suite fails.")
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
