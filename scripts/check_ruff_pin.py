#!/usr/bin/env python3
"""T-DEP-06 - the ruff the door runs is the ruff CI runs: the single `ruff==` pin.

scripts/push.sh runs THIS file with `~/orchestra/lintenv/bin/python`, the hash-pinned install of
requirements/ci-lint.txt; the instrument is resolved through `sys.executable`. Same shape as the
pin half of scripts/check_mypy_ceiling.py (T-MY-02).

  exit 0  ruff <v> is the pin
  exit 2  not_measured, three different lines:
            unreadable         - no file, no `ruff==` line, or more than one
            check_did_not_run  - ruff did not start
            instrument mismatch - the running ruff is not the pin
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_PIN = re.compile(r"^ruff==(\S+)")

REBUILD = ("python3 -m venv ~/orchestra/lintenv && ~/orchestra/lintenv/bin/pip install --quiet "
           "--require-hashes --only-binary=:all: -r requirements/ci-lint.txt")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--requirements", type=Path, default=ROOT / "requirements" / "ci-lint.txt",
                    help="for tests only")
    args = ap.parse_args(argv)

    try:
        text = Path(args.requirements).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"not_measured: unreadable - {args.requirements}: {exc}")
        return 2
    pins = [m.group(1).removesuffix("\\").strip()
            for m in (_PIN.match(ln) for ln in text.splitlines()) if m]
    if len(pins) != 1:
        print(f"not_measured: unreadable - {len(pins)} `ruff==` lines in {args.requirements}, "
              "want exactly one")
        return 2
    pin = pins[0]

    try:
        res = subprocess.run([sys.executable, "-m", "ruff", "--version"],
                             capture_output=True, text=True)
    except OSError as exc:
        print(f"not_measured: check_did_not_run - ruff did not start: {exc}")
        return 2
    m = re.match(r"ruff (\S+)", res.stdout)
    if res.returncode != 0 or not m:
        err = (res.stderr.strip().splitlines() or [""])[0]
        print(f"not_measured: check_did_not_run - ruff did not start: {res.returncode}, {err}")
        return 2
    running = m.group(1)
    if running != pin:
        print(f"not_measured: instrument mismatch: running ruff {running}, pin is {pin}. "
              f"Door: rebuild ~/orchestra/lintenv: {REBUILD}")
        return 2
    print(f"ruff {running} is the pin")
    return 0


if __name__ == "__main__":
    sys.exit(main())
