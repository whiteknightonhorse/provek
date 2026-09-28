#!/usr/bin/env python3
"""Regenerates evidence/RED-057-integration-tests-fail-to-collect-without-the-package-marker.txt.

T-GL-03c-collect (GL-05-harness-import.ruling-1.md, points 1-3): `scripts/push.sh` step 9/9 and
gates.yml's `genlayer` job both gained a `pytest --collect-only -q tests/integration` line so this
class of defect - a relative import inside `tests/integration/` failing before any network call is
even attempted - is measured at the door and in CI, not just discovered by a dispatcher run against
studionet (see the original transcript this task carried in,
evidence/GL-studionet-20260928T045002Z.txt). The plant removes the one file the fix added,
`integrations/genlayer-witness/tests/integration/__init__.py`, and re-runs exactly the command the
door and CI now run.
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

OUT = ROOT / "evidence" / "RED-057-integration-tests-fail-to-collect-without-the-package-marker.txt"
WITNESS_DIR = ROOT / "integrations" / "genlayer-witness"
MARKER = WITNESS_DIR / "tests" / "integration" / "__init__.py"
# Same interpreter `scripts/push.sh` step 9/9 uses (T-GL-02's isolated Python 3.12 venv, not this
# repository's own 3.10) - `gltest`/`genlayer-py` only exist there.
GLENV_PYTHON = pathlib.Path.home() / "orchestra" / "glenv" / "bin" / "python3"
CMD = [str(GLENV_PYTHON), "-m", "pytest", "--collect-only", "-q", "tests/integration"]


def _run() -> tuple[int, str]:
    proc = subprocess.run(CMD, cwd=WITNESS_DIR, capture_output=True, text=True, timeout=60)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def main() -> None:
    assert GLENV_PYTHON.is_file(), f"{GLENV_PYTHON} (T-GL-02's venv) is missing"
    assert MARKER.is_file(), "the package marker the fix added is missing before the plant even runs"
    original = MARKER.read_text(encoding="utf-8")

    buf = io.StringIO()
    with redirect_stdout(buf):
        print("# RED-057 - collect-only gate, plant: tests/integration/__init__.py removed")
        print("#")
        print(f"# subject: {' '.join(CMD)} (integrations/genlayer-witness/)")
        print(f"# {evidence_stamp.tree_stamp()}")
        print()
        ok = True
        try:
            MARKER.unlink()
            rc, out = _run()
            print("--- plant applied (__init__.py removed) ---")
            print(f"exit code: {rc}")
            print(out)
            print()
            if rc == 0:
                print("NOT REPRODUCED: the plant did not turn the collect-only gate red.")
                ok = False
            else:
                print("CONFIRMED: without the package marker, tests/integration fails to collect "
                      "(rc != 0) - caught before any network call, matching the dispatcher's "
                      "studionet transcript.")
        finally:
            MARKER.write_text(original, encoding="utf-8")

        rc2, out2 = _run()
        print()
        print("--- plant reverted (__init__.py restored) ---")
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
