#!/usr/bin/env python3
"""Regenerates evidence/RED-062-a-drifted-copy-of-the-genlayer-pin-set-would-pass.txt.

T-GL-07a-mirror-prep (D-64): `integrations/genlayer-witness/requirements/ci-genlayer.txt` is a
copy of the root `requirements/ci-genlayer.txt`, admitted only under
`tests/test_genlayer_ci_requirements_one_place.py`. The plant appends one byte to the copy, shows
the test go red, restores the copy byte-for-byte, and shows it green again.
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

OUT = ROOT / "evidence" / "RED-062-a-drifted-copy-of-the-genlayer-pin-set-would-pass.txt"
COPY = ROOT / "integrations" / "genlayer-witness" / "requirements" / "ci-genlayer.txt"
CMD = [sys.executable, "-m", "pytest", "-q", "tests/test_genlayer_ci_requirements_one_place.py"]


def _run() -> tuple[int, str]:
    proc = subprocess.run(CMD, cwd=ROOT, capture_output=True, text=True, timeout=120)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def main() -> None:
    assert COPY.is_file(), f"{COPY} is missing"
    original = COPY.read_bytes()
    buf = io.StringIO()
    ok = True
    with redirect_stdout(buf):
        print("# RED-062 - one-place law for the GenLayer pin set, plant: one byte appended to the "
              "mirror's copy")
        print("#")
        print(f"# subject: {' '.join(CMD[1:])}")
        print(f"# {evidence_stamp.tree_stamp()}")
        print()
        try:
            COPY.write_bytes(original + b"\n")
            rc, out = _run()
            print("--- plant applied (one byte appended to the copy) ---")
            print(f"exit code: {rc}")
            print(out)
            print()
            if rc == 0:
                print("NOT REPRODUCED: a drifted copy passed the one-place test.")
                ok = False
            else:
                print("CONFIRMED: the drifted copy turns the test red (rc != 0).")
        finally:
            COPY.write_bytes(original)
        assert COPY.read_bytes() == original
        rc2, out2 = _run()
        print()
        print("--- plant reverted (copy restored byte-for-byte) ---")
        print(f"exit code: {rc2}")
        print(out2)
        print()
        if rc2 != 0:
            print("REGRESSION: the test is not green again on the real tree.")
            ok = False
        else:
            print("CONFIRMED: green again with the plant reverted.")
    text = buf.getvalue()
    sys.stdout.write(text)
    OUT.write_text(text, encoding="utf-8")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
