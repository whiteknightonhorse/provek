#!/usr/bin/env python3
"""Regenerates evidence/RED-060-old-live-call-form-fails-the-offline-surface-check.txt.

T-GL-03d-callform (GL-05-call-signature.ruling-1.md): the fix rewrites the 7 call sites in
`tests/integration/test_provek_evidence_witness_live.py` from the direct-harness's positional form
(`contract.witness("a", "b", ...)`) to the `args=[...]` form `gltest.contracts.Contract` actually
accepts (see the dispatcher's Studionet transcript, evidence/GL-studionet-20260928T053855Z.txt: 4
failed with `TypeError: ... takes from 1 to 2 positional arguments but 5 were given`). The new
`tests/direct/test_live_harness_surface.py::test_integration_call_sites_use_args_kwarg_only` catches
this offline, by AST-walking `tests/integration/*.py` - the plant restores the OLD (c8599ad,
positional) text of the live-test file and re-runs the offline check against it.
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

OUT = ROOT / "evidence" / "RED-060-old-live-call-form-fails-the-offline-surface-check.txt"
WITNESS_DIR = ROOT / "integrations" / "genlayer-witness"
LIVE_TEST = WITNESS_DIR / "tests" / "integration" / "test_provek_evidence_witness_live.py"
OLD_REVISION = "c8599ad"
GLENV_PYTHON = pathlib.Path.home() / "orchestra" / "glenv" / "bin" / "python3"
CMD = [str(GLENV_PYTHON), "-m", "pytest", "-q", "tests/direct/test_live_harness_surface.py"]


def _run() -> tuple[int, str]:
    proc = subprocess.run(CMD, cwd=WITNESS_DIR, capture_output=True, text=True, timeout=60)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def _old_text() -> str:
    proc = subprocess.run(
        ["git", "show", f"{OLD_REVISION}:integrations/genlayer-witness/tests/integration/"
                        "test_provek_evidence_witness_live.py"],
        cwd=ROOT, capture_output=True, text=True, timeout=30, check=True,
    )
    return proc.stdout


def main() -> None:
    assert GLENV_PYTHON.is_file(), f"{GLENV_PYTHON} (T-GL-02's venv) is missing"
    assert LIVE_TEST.is_file(), "the live-test file the plant restores an old copy of is missing"
    original = LIVE_TEST.read_text(encoding="utf-8")
    old = _old_text()
    assert old != original, "the old (c8599ad) text is identical to the current fix - nothing to plant"

    buf = io.StringIO()
    with redirect_stdout(buf):
        print("# RED-060 - offline call-form check, plant: live-test file reverted to c8599ad "
              "(positional call form)")
        print("#")
        print(f"# subject: {' '.join(CMD)} (integrations/genlayer-witness/)")
        print(f"# {evidence_stamp.tree_stamp()}")
        print()
        ok = True
        try:
            LIVE_TEST.write_text(old, encoding="utf-8")
            rc, out = _run()
            print(f"--- plant applied ({LIVE_TEST.relative_to(ROOT)} reverted to {OLD_REVISION}) ---")
            print(f"exit code: {rc}")
            print(out)
            print()
            if rc == 0:
                print("NOT REPRODUCED: the offline check did not turn red against the old call form.")
                ok = False
            else:
                print("CONFIRMED: the old positional call form fails the offline surface check "
                      "(rc != 0) - caught without any network call, matching the dispatcher's "
                      "studionet TypeError.")
        finally:
            LIVE_TEST.write_text(original, encoding="utf-8")

        rc2, out2 = _run()
        print()
        print("--- plant reverted (live-test file restored to the fixed args= form) ---")
        print(f"exit code: {rc2}")
        print(out2)
        if rc2 != 0:
            print()
            print("REGRESSION: the check is not green again on the real (fixed) tree.")
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
