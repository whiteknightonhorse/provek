#!/usr/bin/env python3
"""T-SCOPE-RATCHET - every module is bound to an ABI requirement. An unbound module fails the build.

WHY. Requirements ABI-21-1..4 ("do not sprawl beyond the mission") were, in the first draft of the
traceability matrix, hung on a test that asserted "the non-goals list exists" - a test that CANNOT
FAIL while scope actually sprawls. Fable called that a declaration. This ratchet makes scope
falsifiable: a module nobody needed physically fails the build.

THE DEGENERATION TO WATCH FOR: everything gets hung on one broad requirement. That is caught
mechanically here, by the MAX_SHARE rule below, not by eyesight.
"""
from __future__ import annotations

import collections
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MAP = ROOT / "requirements" / "ABI_MAP.yaml"
SCAN = ("src", "scripts", "demo")
CODE_SUFFIXES = (".py", ".sh", ".mjs")
"""EXPLICIT list of what counts as code.

The first version looked only at `*.py`, so shell scripts were outside supervision entirely: any
number of them could be added and scope would not push back. A checker that inspects one shape
reports success on every other.

AND IT HAPPENED AGAIN, EXACTLY AS THE PARAGRAPH ABOVE PREDICTS. T-2.16 added `demo/amadeus/` -
a JavaScript agent that is half the demo and takes every reading in it - and both the directory
and the `.mjs` shape fell outside this list, so the load-bearing half of a new feature was bound
to no requirement and the build could not go red over it. The widening for `.sh` was the same
lesson; the note recording it sat three lines above the gap. Found by Fable."""
MAX_SHARE = 0.5   # no single requirement may cover more than half the modules


def _load_map(path: pathlib.Path) -> dict[str, list[str]]:
    """Flat YAML of the form `path: [ID, ID]`. Hand-parsed rather than pulling a dependency for it."""
    out: dict[str, list[str]] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, val = line.split(":", 1)
        ids = [i.strip() for i in val.strip().strip("[]").split(",") if i.strip()]
        out[key.strip()] = ids
    return out


def check() -> list[str]:
    """List of violations. An EMPTY list means clean; None is never returned."""
    problems: list[str] = []
    skipped: list[str] = []
    if not MAP.exists():
        return [f"no requirement map at {MAP} - the ratchet cannot tell clean from missing map"]
    mapping = _load_map(MAP)

    found = set()
    for d in SCAN:
        for f in (ROOT / d).rglob("*"):
            if not f.is_file() or f.suffix not in CODE_SUFFIXES:
                continue
            rel = f.relative_to(ROOT).as_posix()
            # EXPLICIT, NAMED skip. Silently skipping an unrecognised shape is forbidden: a checker
            # that quietly walks past what it does not understand reports success on what it never
            # examined. Exactly three known classes of junk are skipped here.
            #
            # `node_modules` JOINED THE LIST THE MOMENT `demo/` DID, and leaving it out was a live
            # trap rather than an untidiness. This walks the filesystem, not the index, so adding
            # `demo/` brought 1414 gitignored third-party `.js` files inside the scan boundary.
            # The build survived only because `CODE_SUFFIXES` happens to carry `.mjs` and not
            # `.js` - and this list has already been widened twice. The next widening would have
            # printed 1414 "MODULE WITHOUT REQUIREMENT" lines for somebody else's code AND, worse,
            # inflated `len(found)` so that the MAX_SHARE rubber-stamp rule silently stopped
            # binding. A gate defeated by a dependency install is not a gate. Found by Fable.
            if "__pycache__" in rel or "node_modules/" in rel or f.name.startswith("._"):
                skipped.append(rel)
                continue
            found.add(rel)
            if rel not in mapping:
                problems.append(f"MODULE WITHOUT REQUIREMENT: {rel}")
            elif not mapping[rel]:
                problems.append(f"EMPTY mapping: {rel}")

    for rel in mapping:
        if rel not in found:
            problems.append(f"MAPPING TO A NONEXISTENT module: {rel}")

    if found:
        cnt = collections.Counter(i for ids in mapping.values() for i in ids)
        for req, n in cnt.items():
            if n / len(found) > MAX_SHARE:
                problems.append(
                    f"RUBBER STAMP: requirement {req} covers {n} of {len(found)} modules "
                    f"(> {int(MAX_SHARE*100)}%) - the mapping has degenerated into a formality")
    return problems


def main() -> int:
    p = check()
    if p:
        sys.stderr.write("\nX T-SCOPE-RATCHET:\n" + "".join(f"  - {x}\n" for x in p))
        return 1
    print("T-SCOPE-RATCHET: clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
