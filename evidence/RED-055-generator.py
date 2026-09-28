#!/usr/bin/env python3
"""Regenerates evidence/RED-055-a-scoring-module-importing-the-genlayer-contract-would-pass.txt.

T-GL-04: `tests/test_genlayer_witness_is_isolated.py` is new (CLAUDE.md invariant 5). The plant is
the exact fusion ADR-0002/D-63 exist to forbid: a real scoring module reaching into
`integrations/genlayer-witness` for a result, one import line appended to a file the ratchet
already scans.
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

OUT = ROOT / "evidence" / "RED-055-a-scoring-module-importing-the-genlayer-contract-would-pass.txt"
TARGET = ROOT / "src" / "witness" / "witness.py"
TEST = "tests/test_genlayer_witness_is_isolated.py"

PLANT = ("\nfrom integrations.genlayer_witness.contracts.provek_evidence_witness "
         "import ProvekEvidenceWitness  # RED-055 plant\n")


def _run() -> tuple[int, str]:
    proc = subprocess.run(["python3", "-m", "pytest", TEST, "-q"],
                           cwd=ROOT, capture_output=True, text=True, timeout=60)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def main() -> None:
    original = TARGET.read_text(encoding="utf-8")

    buf = io.StringIO()
    with redirect_stdout(buf):
        print("# RED-055 - isolation, plant: src/ importing the GenLayer contract")
        print("#")
        print(f"# subject: {TEST}")
        print(f"# {evidence_stamp.tree_stamp()}")
        print()
        ok = True
        try:
            TARGET.write_text(original + PLANT, encoding="utf-8")
            rc, out = _run()
            print(f"--- plant applied ({TEST}) ---")
            print(f"exit code: {rc}")
            print(out)
            print()
            if rc == 0:
                print("NOT REPRODUCED: the plant did not turn the isolation test red.")
                ok = False
            else:
                print("CONFIRMED: an import of the GenLayer contract from src/ is caught.")
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
