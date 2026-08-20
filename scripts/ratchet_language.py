#!/usr/bin/env python3
"""T-LANGUAGE-RATCHET — everything that reaches GitHub must be in English.

OPERATOR RULING 2026-08-19: the entire GitHub surface — code, comments, docstrings, documents,
commit messages — is English-only. Working documents that live on the operator's laptop stay in
Russian; this gate governs the repository, which is what other people read.

WHY A GATE AND NOT A NOTE. A rule with no armed gate rots into a comment. This project has
already paid for that twice today.

WHAT IS CHECKED: Cyrillic characters in tracked files. Deliberate exceptions are listed
explicitly and named — a checker that silently skips what it does not understand reports success
on what it never examined.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CYRILLIC = re.compile(r"[\u0400-\u04FF\u0500-\u052F]")
"""The range is written as escapes, not as literal characters.

The first version spelled the range with actual Cyrillic letters - and the gate then found
ITSELF. A detector whose own pattern trips it is not wrong about the world, but it can never
report clean, and a gate that can never be satisfied gets disabled by whoever meets it."""

# Explicit, named exceptions. Nothing is skipped silently.
EXEMPT_PATHS = {
    "evidence/",   # archived run output; historical artefacts are not rewritten
}
EXEMPT_REASON = "archived evidence: historical run output is never rewritten"


def tracked_files() -> list[str]:
    r = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True)
    return [f for f in r.stdout.splitlines() if f.strip()]


def check() -> list[str]:
    problems: list[str] = []
    for rel in tracked_files():
        if any(rel.startswith(x) for x in EXEMPT_PATHS):
            continue
        p = ROOT / rel
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            problems.append(f"UNREADABLE: {rel} — cannot be checked, and that is not a pass")
            continue
        hits = [(i, ln) for i, ln in enumerate(text.splitlines(), 1) if CYRILLIC.search(ln)]
        if hits:
            first = hits[0]
            problems.append(f"NON-ENGLISH: {rel} ({len(hits)} lines), first at line {first[0]}")
    return problems


GRANDFATHERED_BEFORE = "987d209"
GRANDFATHER_REASON = (
    "commits authored before the English-only ruling of 2026-08-19 were already pushed. "
    "Rewriting published history is worse than the defect it would fix, and this project's own "
    "doctrine is supersede-never-erase: a record that disappears reads as closure to anything "
    "that reads absence as resolution. They are named here rather than silently skipped.")


def check_commit_messages(limit: int = 30) -> list[str]:
    """Commit messages are part of the GitHub surface and are checked too.

    Commits at or before GRANDFATHERED_BEFORE are exempt, for the reason stated above. The
    exemption is NAMED, not silent - a checker that quietly skips what it cannot fix reports
    success on it.
    """
    r = subprocess.run(["git", "log", f"-{limit}", "--format=%H%x00%s%x00%b"],
                       cwd=ROOT, capture_output=True, text=True)
    out = []
    seen_baseline = False
    for chunk in r.stdout.split("\n\n"):
        parts = chunk.split("\x00")
        if len(parts) < 2:
            continue
        if parts[0].startswith(GRANDFATHERED_BEFORE):
            seen_baseline = True
        if seen_baseline:
            continue                      # this commit and everything older is grandfathered
        if CYRILLIC.search(" ".join(parts[1:])):
            out.append(f"NON-ENGLISH COMMIT: {parts[0][:8]} {parts[1][:60]}")
    return out


def main() -> int:
    p = check()
    c = check_commit_messages()
    if p or c:
        sys.stderr.write("\nX T-LANGUAGE-RATCHET: the GitHub surface must be English-only\n")
        for x in p[:40]:
            sys.stderr.write(f"  - {x}\n")
        for x in c[:10]:
            sys.stderr.write(f"  - {x}\n")
        sys.stderr.write(f"\n  exempt paths: {sorted(EXEMPT_PATHS)} ({EXEMPT_REASON})\n")
        sys.stderr.write(f"  grandfathered commits: at or before {GRANDFATHERED_BEFORE} "
                         f"({GRANDFATHER_REASON})\n")
        return 1
    print("T-LANGUAGE-RATCHET: clean (English-only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
