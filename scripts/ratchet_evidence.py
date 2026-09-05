#!/usr/bin/env python3
"""LAW-EVIDENCE-STAMPED-TREE - an evidence artefact with no tree stamp fails the build, unless it
predates this ratchet and is named in `requirements/EVIDENCE_LEGACY.txt`.

WHY A LEGACY LIST, AND WHY IT IS NAMED RATHER THAN A PATTERN. D-28 forbids rewriting an old
artefact to carry a stamp it was never generated with - the fix is forward-only. Every file already
sitting in `evidence/` at the moment this ratchet was written is frozen into
`requirements/EVIDENCE_LEGACY.txt`, once, in this commit, the same way `requirements/ci-tests.txt`
pins a set rather than a glob (D-30): a wildcard exemption ("anything already existing when I ran
this") would silently cover the NEXT hand-added file too, which is the templated exemption
CLAUDE.md's `.gitignore` doctrine refuses. The list does not grow after this commit; a file added
later either carries a stamp or the build goes red over it.

WHAT COUNTS AS AN EVIDENCE FILE. Everything directly under `evidence/` except directories
(`__pycache__`, `TAINTED-SUDO-CORPUS` - a pre-existing corpus of scraped fixtures, not a generator's
output) and `*-generator.py` scripts themselves: those are code that PRODUCES an artefact, not the
artefact, and `scripts/ratchet_scope.py` already holds code to its own requirement - binding it a
second time here would be the same rule in two places (L-2).

THE STAMP MUST BE NEAR THE TOP, NOT ANYWHERE. `HEADER_LINES` bounds the search to where a reader
looks for provenance - the header - rather than matching the literal string `tree:` if it
happens to appear inside 600 lines of quoted tool output further down, which several of these
artefacts carry verbatim.

A `.json` EVIDENCE ARTEFACT NAMES THE TREE IN ITS OWN FORMAT, NOT AS A HEADER LINE (added for
ADR-0011/D-57's `TEMPLATE-RUN-<slug>.json` witnessed-dry-run records). A JSON document with a
comment line above its opening brace is not JSON, so the header-regex convention above is not
available to it, and forcing one would break the very artefact `tests/test_template_was_run.py`
needs to `json.loads` cleanly. The rule stays the same - name the tree an artefact was produced
against - carried in a `tree_stamp` field, of the same string shape `evidence_stamp.tree_stamp()`
returns, checked with the same `STAMP_RE` rather than a second pattern.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
LEGACY = ROOT / "requirements" / "EVIDENCE_LEGACY.txt"
HEADER_LINES = 20
JSON_STAMP_KEY = "tree_stamp"

# Matches every shape `evidence_stamp.tree_stamp()` can produce - see that module's docstring for
# the four states. Deliberately does not accept a bare `tree: dirty` or similar hand-typed
# shorthand: the sha is the citation a reader can check the rest of the artefact against, and a
# stamp without one would satisfy this pattern while giving nothing to verify.
#
# `(?:#\s*)?` because the corpus has no single header convention - some generators comment every
# header line (`# RED-032 - ...`), others write plain prose (`RED-033 - ...`) - and the stamp must
# be recognised inside either, not just at a bare start of line.
STAMP_RE = re.compile(
    r"^(?:#\s*)?tree: (unreadable|[0-9a-f]{40}(?: \(dirty(?:-state unreadable)?\))?)\s*$",
    re.MULTILINE,
)


def _legacy() -> frozenset[str]:
    if not LEGACY.exists():
        return frozenset()
    return frozenset(
        line.strip() for line in LEGACY.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    )


def check() -> list[str]:
    """List of violations. An EMPTY list means clean; None is never returned (invariant 1)."""
    if not EVIDENCE.is_dir():
        return [f"no evidence directory at {EVIDENCE}"]
    legacy = _legacy()
    problems: list[str] = []
    for f in sorted(EVIDENCE.iterdir()):
        if not f.is_file() or f.suffix == ".py":
            continue
        if f.name in legacy:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            problems.append(f"evidence/{f.name}: unreadable ({exc}) - cannot be judged, and an "
                             f"unreadable file is not the same fact as a clean one")
            continue
        if f.suffix == ".json":
            try:
                doc = json.loads(text)
            except json.JSONDecodeError as exc:
                problems.append(f"evidence/{f.name}: not valid JSON ({exc}), so its "
                                 f"'{JSON_STAMP_KEY}' field could not be read")
                continue
            stamp = doc.get(JSON_STAMP_KEY) if isinstance(doc, dict) else None
            if not isinstance(stamp, str) or not STAMP_RE.match(stamp):
                problems.append(
                    f"evidence/{f.name}: no valid '{JSON_STAMP_KEY}' field naming the tree "
                    f"it was produced against, and it is not named in {LEGACY.relative_to(ROOT)}"
                )
            continue
        header = "\n".join(text.splitlines()[:HEADER_LINES])
        if not STAMP_RE.search(header):
            problems.append(
                f"evidence/{f.name}: no 'tree: <sha>' stamp in its first {HEADER_LINES} lines, "
                f"and it is not named in {LEGACY.relative_to(ROOT)}"
            )
    return problems


def main() -> int:
    problems = check()
    if problems:
        print(f"{len(problems)} evidence file(s) missing a tree stamp:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print("evidence ratchet clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
