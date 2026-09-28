#!/usr/bin/env python3
"""T-GL-04 - `genvm-lint check` cannot be run bare as a CI/door gate for this contract.

WHY THIS SCRIPT EXISTS RATHER THAN A BARE `genvm-lint check contracts/...` COMMAND. The installed
`genvm-linter==0.11.0` CLI (`cli.py`: `sys.exit(0 if (lint_result.ok and validate_result.ok) else
1)`) has no baseline, allowlist or `--ignore` flag of any kind - ANY surviving warning, however
well-understood, makes `check` exit 1. `README.md` (this directory) already names two E010
warnings on `leader_fn`/`validator_fn` as confirmed false positives (the linter's reachability
check does not recognise the `import genlayer.gl.vm as glvm; glvm.run_nondet_unsafe(...)` alias
form ruling-2 SS2 specifies and the boilerplate's own `PatternTest.py` uses) that are kept, not
worked around, because switching to the fully-dotted form to silence a linter false positive was
judged the wrong trade. A bare `genvm-lint check` step would therefore be permanently red for a
reason that is not a defect - which is not what "the contract passes the GenVM linter" is supposed
to measure.

So this script runs `genvm-lint check --json`, itself, and asks the one question a CI status can
actually answer honestly: is the warning set EXACTLY the two named, understood false positives -
no more, no fewer, no different line or message - and did SDK-semantic validation pass. Any other
shape (a third warning, a moved line, a changed message, `validate.ok` false, the binary missing,
unparseable JSON) is a hard failure, because any of those really could be a regression this project
has never seen, and treating an unrecognised shape as "probably fine" is invariant 1's own mistake
turned on this project's own tooling.

ONE SCRIPT, NOT TWO COPIES OF THIS LOGIC (L-2). `.github/workflows/gates.yml`'s `genlayer` job and
`scripts/push.sh`'s door step 9 both need to run this exact check; writing the JSON-interpretation
logic once here, called identically by both, is what keeps a future edit to the accepted-warning
set (or a real new one) from being fixed in one and not the other - the exact shape of defect this
project's whole `test_door_matches_ci.py` exists to catch for the commands it can only compare as
substrings.

WHY `sys.executable`-RELATIVE, NOT A HARDCODED PATH. This script runs in two different Python 3.12
environments - `~/orchestra/glenv` at the door, a fresh `actions/setup-python` environment in CI -
and neither path is valid in the other. `genvm-lint`'s own console-script entry point is installed
into the same `bin/` directory as whichever `python3` is running this script, so resolving it via
`sys.executable`'s own directory finds the right one in both places without naming either.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTRACT = HERE.parent / "contracts" / "provek_evidence_witness.py"

# The exact, confirmed-false-positive warning set this project has decided to keep rather than
# silence (see this directory's README.md, "Known genvm-lint check warnings"). `col` is not
# compared: it is the one field the linter's own line/message pair does not need to make the
# identification unambiguous, and pinning it too would make this script brittle to a change in the
# linter's own column-counting convention rather than to a change in THIS contract.
EXPECTED_WARNINGS = [
    {"code": "E010", "line": 231,
     "msg": "gl.nondet.* call in 'ProvekEvidenceWitness.witness.<locals>.leader_fn' "
            "not reachable from equivalence principle block"},
    {"code": "E010", "line": 248,
     "msg": "gl.nondet.* call in 'ProvekEvidenceWitness.witness.<locals>.validator_fn' "
            "not reachable from equivalence principle block"},
]


def _genvm_lint() -> Path:
    """The `genvm-lint` console script beside the interpreter running this file."""
    # NOT `.resolve()`: a venv's `bin/python3` is ordinarily a symlink to the base interpreter,
    # and resolving it would walk past the venv's own `bin/` - where `pip install` actually put
    # this console script - to a directory that never has it.
    return Path(sys.executable).parent / "genvm-lint"


def main() -> int:
    if not CONTRACT.is_file():
        print(f"NOT MEASURED: {CONTRACT} does not exist", file=sys.stderr)
        return 1

    genvm_lint = _genvm_lint()
    if not genvm_lint.is_file():
        print(f"NOT MEASURED: {genvm_lint} does not exist - a missing instrument is a red, "
              "never a skip", file=sys.stderr)
        return 1

    try:
        proc = subprocess.run([str(genvm_lint), "check", str(CONTRACT), "--json"],
                               capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"NOT MEASURED: genvm-lint could not be run: {e}", file=sys.stderr)
        return 1

    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError:
        print("NOT MEASURED: genvm-lint did not print JSON:", file=sys.stderr)
        print(proc.stdout, file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
        return 1

    lint = report.get("lint") or {}
    validate = report.get("validate") or {}
    actual_warnings = [{"code": w.get("code"), "line": w.get("line"), "msg": w.get("msg")}
                        for w in lint.get("warnings") or []]

    problems = []
    if actual_warnings != EXPECTED_WARNINGS:
        problems.append(
            "lint warnings changed from the two named false positives in README.md:\n"
            f"  expected: {json.dumps(EXPECTED_WARNINGS)}\n"
            f"  actual:   {json.dumps(actual_warnings)}\n"
            "A new or different warning may be a real regression; a warning that disappeared "
            "means README.md's note is stale and should be removed in the same commit as this "
            "script (see the module docstring in provek_evidence_witness.py and this contract's "
            "own README.md).")
    if not validate.get("ok"):
        problems.append(f"SDK-semantic validation failed: {json.dumps(validate)}")

    if problems:
        print("X check_genvm_lint.py:")
        for p in problems:
            print(f"  - {p}")
        return 1

    print(f"check_genvm_lint.py: clean (exactly the {len(EXPECTED_WARNINGS)} named E010 false "
          f"positives, validate ok - contract {validate.get('contract')}, "
          f"{validate.get('methods')} methods)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
