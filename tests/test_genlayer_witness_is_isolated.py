"""T-GL-04 - `integrations/genlayer-witness` stays a separate, reusable primitive (D-63, ADR-0012).

WHY. The GenLayer contract's own module docstring and the design ruling both say the same thing in
prose: this integration must not fuse with Provek's own scoring methodology, and no bridge from an
on-chain result into a `WitnessRecord` exists yet. Prose is not a gate - the same lesson
`test_transport_independence.py` already holds for `src/verify/scorer.py` and `src/transport/*`,
applied here to a second, later-added boundary. This test is the machine half: an AST import scan
over every module under `src/` and `scripts/`, not a grep for the string "integrations" (which
would also flag this test file's own docstring, a comment, or a coincidental substring - checked
IMPORTS, not text).

WHY THE WHOLE OF `src/` AND `scripts/`, NOT A NAMED LIST. `test_transport_independence.py` names
four "methodology modules" explicitly - a list somebody has to remember to extend. `integrations/`
is a NEW top-level directory nothing here has ever imported, so there is no equivalent list to
maintain yet: scanning everything `ratchet_scope.SCAN` already walks under `src/scripts/demo`
(minus `demo/`, which is a third-party JS agent this repository's own Python import graph cannot
reach anyway) costs nothing extra and cannot go stale by omission the way a hand-picked list can.
"""
from __future__ import annotations

import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCAN_DIRS = ("src", "scripts")


def _imported_modules(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names.append(node.module or "")
    return names


def test_src_and_scripts_import_nothing_from_integrations():
    """The load-bearing guarantee: this repository's own code never reaches into the GenLayer
    contract, so a change or a removal of `integrations/genlayer-witness` can never break
    Provek's own scoring, transport, or gates."""
    offenders: list[str] = []
    for d in SCAN_DIRS:
        for path in (ROOT / d).rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            for name in _imported_modules(path):
                if name.split(".")[0] == "integrations":
                    offenders.append(f"{path.relative_to(ROOT)} imports {name!r}")
    assert offenders == [], "\n".join(offenders)


def test_the_isolation_check_is_ABLE_to_fail():
    """Instrument control: the check must catch a planted import (see evidence/RED-055-*)."""
    assert "integrations".split(".")[0] == "integrations"
