#!/usr/bin/env python3
"""T-MY-02 - the advisory mypy backlog may not grow: one program on both sides of the door.

CI (gates.yml `mypy` step) and scripts/push.sh run THIS file, each with the interpreter that holds
the hash-pinned install of requirements/ci-lint.txt (CI's `python`, the door's
`~/orchestra/lintenv/bin/python`). The instrument is resolved through `sys.executable`, and its
version is checked against the pin before any count is believed.

  exit 0  mypy ran under the pinned version and the error count is at or below the ceiling
  exit 1  the backlog grew, or mypy is CLEAN (the advisory state's own end condition)
  exit 2  not_measured: no single pin, wrong instrument, no ceiling for this pin, mypy did not run
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# D-65 Decision 3. The ONE place the number lives in code. Keyed by the mypy version pinned in
# requirements/ci-lint.txt: a value may only move DOWN; a NEW key is added only with a MEASURED-0NN
# transcript under that pin, in the same commit as the pin.
CEILING = {"2.4.0": 43}

_PIN = re.compile(r"^mypy==(\S+)")


def pinned_version(path: Path) -> str | None:
    """The `X` of the single `mypy==X` line, else None (zero or several pins)."""
    found = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = _PIN.match(line)
        if m:
            found.append(m.group(1).removesuffix("\\").strip())
    return found[0] if len(found) == 1 else None


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "mypy", *args], capture_output=True, text=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--requirements", type=Path, default=ROOT / "requirements" / "ci-lint.txt",
                    help="for tests only")
    args = ap.parse_args(argv)

    pin = pinned_version(args.requirements)
    if pin is None:
        print("not_measured: no single mypy== pin in requirements/ci-lint.txt")
        return 2

    ver = _run("--version")
    m = re.match(r"mypy (\S+)", ver.stdout)
    running = m.group(1) if m else "unknown"
    if running != pin:
        print(f"instrument mismatch: running mypy {running}, pin is {pin}. Door: rebuild "
              "~/orchestra/lintenv: python3 -m venv ~/orchestra/lintenv && "
              "~/orchestra/lintenv/bin/pip install --quiet --require-hashes --only-binary=:all: "
              "-r requirements/ci-lint.txt. CI: the pin and the install come from the same file "
              "- this cannot happen there.")
        return 2

    if pin not in CEILING:
        print(f"pin moved to {pin} and no ceiling is measured under it: measure "
              f"(evidence/MEASURED-0NN), add CEILING[\"{pin}\"] in the same commit (D-65 Decision 3)")
        return 2

    res = _run("src", "--ignore-missing-imports", "--no-error-summary")
    out = res.stdout + res.stderr
    print(out, end="" if out.endswith("\n") or not out else "\n")
    rc = res.returncode
    if rc not in (0, 1):  # mypy's own contract: 0 clean, 1 findings, anything else did not run
        print(f"mypy DID NOT RUN (exit {rc}): not_measured, not a clean baseline")
        return 2
    if rc == 0:
        print(f"mypy is CLEAN under {pin}: drop the ceiling, make the step fully blocking, "
              "in this commit (D-22's trip, kept)")
        return 1
    count = sum(1 for line in out.splitlines() if ": error:" in line)
    ceiling = CEILING[pin]
    if count > ceiling:
        print(f"backlog grew: {count} > ceiling {ceiling} under mypy {pin} (D-65)")
        return 1
    print(f"mypy: {count} errors - advisory under ceiling {ceiling} (mypy {pin}, pinned)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
