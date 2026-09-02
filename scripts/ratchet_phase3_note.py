#!/usr/bin/env python3
"""LAW-PHASE-THREE-NOTE-SYNCED - the two copies of the phase-renumbering note in SPEC.md are one
fact, and a checker that reads only one of them cannot see the other go stale.

WHY. Specification revision 1.4 renumbered the phase grid: Funding Tasks (specification §8) moved
from "phase 2" to phase 3, and the Provider Catalog (specification §4.2-bis) became phase 2.
`SPEC.md` §4 states this twice - once framing the whole section, once inside §4.1's own
re-derivation warning - because a reader who lands on either half by a search or an anchor link
needs the fact without having read the other half first. LAW #ONE-PLACE names the risk this
duplication buys: "a rule written in more than one place survives its own repeal" - an editor who
updates one copy and not the other leaves a document that is wrong exactly where a reader is
likely to land, and every other gate in this repository is blind to it, because neither copy is
missing and neither is malformed on its own.

WHAT THIS CHECKS. `SPEC.md` marks each copy with matching `<!-- PHASE3-NOTE-START -->` /
`<!-- PHASE3-NOTE-END -->` HTML comments. This module extracts every marked block and requires:
  1. at least two blocks exist (a note reduced to one copy, or deleted outright, is caught here -
     the requirement this law exists to state disappears silently otherwise);
  2. every block is byte-for-byte identical to the first.

WHAT THIS DOES NOT CHECK. It does not read the master specification
(`SPEC_AI_Business_Incubator_v1.md`) at all - that document lives on the operator's laptop, is not
tracked by this repository, and no gate here can open it (the same limit `SPEC.md` §4.1 itself
names for its own re-derivation duty). This ratchet only holds the two copies IN THIS REPOSITORY
in agreement with each other; it cannot prove either one still agrees with the laptop-only source.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = ROOT / "SPEC.md"

START = "<!-- PHASE3-NOTE-START -->"
END = "<!-- PHASE3-NOTE-END -->"
_BLOCK_RE = re.compile(re.escape(START) + r"(.*?)" + re.escape(END), re.DOTALL)

MIN_COPIES = 2  # a note stated in only one place is exactly the drift risk this gate exists for


def _blocks(text: str) -> list[str]:
    return [m.group(1) for m in _BLOCK_RE.finditer(text)]


def check() -> list[str]:
    if not SPEC.exists():
        return [f"{SPEC} is missing - the phase-3 note has no file to live in"]
    text = SPEC.read_text(encoding="utf-8")
    blocks = _blocks(text)
    problems = []
    if len(blocks) < MIN_COPIES:
        problems.append(
            f"PHASE-3 NOTE: found {len(blocks)} marked cop{'y' if len(blocks) == 1 else 'ies'} of "
            f"the phase-renumbering note in {SPEC.name}, need at least {MIN_COPIES} - a copy was "
            "deleted or the markers were damaged, and the fact it states can now go stale unnoticed"
        )
    else:
        first = blocks[0]
        for i, b in enumerate(blocks[1:], start=2):
            if b != first:
                problems.append(
                    f"PHASE-3 NOTE: copy {i} of the phase-renumbering note in {SPEC.name} does "
                    "not match copy 1 - the two copies have drifted apart"
                )
    return problems


def main() -> int:
    p = check()
    if p:
        sys.stderr.write("\nX LAW-PHASE-THREE-NOTE-SYNCED:\n" + "".join(f"  - {x}\n" for x in p))
        return 1
    print(f"LAW-PHASE-THREE-NOTE-SYNCED: clean ({len(_blocks(SPEC.read_text(encoding='utf-8')))} "
          "copies, all identical)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
