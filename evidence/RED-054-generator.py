#!/usr/bin/env python3
"""Regenerates evidence/RED-054-application-origin-stored-verbatim.txt.

T-SG-14: `tests/test_intake_records_the_application_origin.py` is new (CLAUDE.md invariant 5). The
plant is the exact mistake D-21/D-23 already named once for `mandate` and this field repeats the
same fix for: `const origin = body.origin === "challenge" ? "challenge" : null;` in
`web/functions/api/apply.js` becomes `const origin = body.origin || null;` - a client-supplied
string now reaches the durable record verbatim instead of being refused to the one value this
endpoint actually defines.
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

OUT = ROOT / "evidence" / "RED-054-application-origin-stored-verbatim.txt"
TARGET = ROOT / "web" / "functions" / "api" / "apply.js"
TEST = "tests/test_intake_records_the_application_origin.py"

GOOD = '  const origin = body.origin === "challenge" ? "challenge" : null;'
BROKEN = "  const origin = body.origin || null;"


def _run() -> tuple[int, str]:
    proc = subprocess.run(["python3", "-m", "pytest", TEST, "-q"],
                           cwd=ROOT, capture_output=True, text=True, timeout=60)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def main() -> None:
    original = TARGET.read_text(encoding="utf-8")
    assert original.count(GOOD) == 1, "the expected source shape has moved or is not unique"

    buf = io.StringIO()
    with redirect_stdout(buf):
        print("# RED-054 - application origin, plant: an unrecognised value stored verbatim")
        print("#")
        print("# subject: web/functions/api/apply.js, the `origin` allowlist")
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
                print("CONFIRMED: with the allowlist replaced by a bare fallback, an unrecognised "
                      "origin value is stored verbatim and the suite fails.")
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
