#!/usr/bin/env python3
"""Regenerates evidence/RED-058-a-mutant-without-the-raw-map-initialisation-crashes.txt.

T-HY-02 (`REPO-hygiene-0928.ruling-1.md`'s alert #80, `py/potentially-uninitialized-local-variable`
on `scripts/fetch_shorts_map.py`): the fix reads at line 116 (`raw_map: dict | None = None`) and
simplified the guard right after it from `state == "ok" and body is not None and
isinstance(raw_map, dict)` to plain `isinstance(raw_map, dict)`. CodeQL's finding was a false
positive AGAINST TODAY'S GUARD - the three-part condition's own `state == "ok"` short-circuits
before `raw_map` is ever read on a path where it was not assigned - but the repair is real anyway,
because the simplified guard removes that short-circuit and now depends entirely on the
initialisation to stay safe. The plant below removes exactly that one line and nothing else, then
runs `tests/test_fetch_shorts_map_main.py` against the mutated file: its first case (`fetch()`
answers `("source_answered_non_200", 503, None)`, so `body is None` and the block that used to
assign `raw_map` is skipped entirely) hits the bare `isinstance(raw_map, dict)` with the name never
bound - an `UnboundLocalError`, Python's actual name for the shape CodeQL flagged.
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

OUT = ROOT / "evidence" / "RED-058-a-mutant-without-the-raw-map-initialisation-crashes.txt"
TARGET = ROOT / "scripts" / "fetch_shorts_map.py"
INIT_LINE = "    raw_map: dict | None = None\n"
CMD = [sys.executable, "-m", "pytest", "-q", "tests/test_fetch_shorts_map_main.py"]


def _run() -> tuple[int, str]:
    proc = subprocess.run(CMD, cwd=ROOT, capture_output=True, text=True, timeout=60)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def main() -> None:
    original = TARGET.read_text(encoding="utf-8")
    assert INIT_LINE in original, "the initialisation line the fix added is missing before the plant even runs"
    mutated = original.replace(INIT_LINE, "", 1)
    assert mutated != original

    buf = io.StringIO()
    with redirect_stdout(buf):
        print("# RED-058 - tests/test_fetch_shorts_map_main.py, plant: raw_map's pre-initialisation removed")
        print("#")
        print(f"# subject: {' '.join(CMD)}")
        print(f"# {evidence_stamp.tree_stamp()}")
        print()
        ok = True
        try:
            TARGET.write_text(mutated, encoding="utf-8")
            rc, out = _run()
            print("--- plant applied (raw_map: dict | None = None removed) ---")
            print(f"exit code: {rc}")
            print(out)
            print()
            if rc == 0:
                print("NOT REPRODUCED: the plant did not turn the new test red.")
                ok = False
            elif "UnboundLocalError" not in out:
                print("NOT REPRODUCED: red, but not for the expected reason (no UnboundLocalError).")
                ok = False
            else:
                print("CONFIRMED: without the pre-initialisation, a non-ok fetch with body=None "
                      "crashes with UnboundLocalError on the bare `isinstance(raw_map, dict)` guard - "
                      "the same shape alert #80 named, reproduced by execution rather than by "
                      "resemblance to CodeQL's rule.")
        finally:
            TARGET.write_text(original, encoding="utf-8")

        rc2, out2 = _run()
        print()
        print("--- plant reverted ---")
        print(f"exit code: {rc2}")
        print(out2)
        if rc2 != 0:
            print()
            print("REGRESSION: the gate is not green again after reverting the plant.")
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
