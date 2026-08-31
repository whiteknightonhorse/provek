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
PARTS_IN_A_HEADER_LINE = 2
"""Structural, not policy: a header line splits into a key and a value."""

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

# Binary formats that cannot carry prose at all. A PNG has no sentences to be English or not, so
# checking it for Cyrillic is not a check that can fail — but "I could not read it" must never be
# reported as "I read it and it was fine", which is what a bare `continue` on UnicodeDecodeError
# would do for EVERY undecodable file, prose included.
#
# Admission is by MAGIC BYTES, never by extension. A suffix is a claim the file makes about
# itself, and this repository's whole subject is that a claim is not evidence: a file named
# `.png` whose bytes are not a PNG stays UNREADABLE and still refuses the push.
BINARY_MAGIC = {
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".ico": (b"\x00\x00\x01\x00",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".webp": (b"RIFF",),
    ".woff2": (b"wOF2",),
    # An ISO base-media file (`.mp4`) carries its `ftyp` box TYPE at offset 4 - the first four bytes
    # are the box SIZE and differ from file to file - so this one cannot be matched at the head like
    # the others. Rather than loosen the match to "contains", the entry states WHERE to look, and
    # the matcher below reads a magic as (offset, bytes). Admission stays by the file's own bytes:
    # a `.mp4` whose bytes are not an ISO box is still UNREADABLE and still refuses the push.
    ".mp4": ((4, b"ftyp"),),
}


def proven_binary(path: pathlib.Path) -> bool:
    """True only when the file's own first bytes match the format its suffix claims."""
    magics = BINARY_MAGIC.get(path.suffix.lower())
    if not magics:
        return False
    try:
        head = path.open("rb").read(16)
    except OSError:
        return False
    for m in magics:
        offset, sig = m if isinstance(m, tuple) else (0, m)
        if head[offset:offset + len(sig)] == sig:
            return True
    return False


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
        except UnicodeDecodeError:
            if proven_binary(p):
                continue
            problems.append(
                f"UNREADABLE: {rel} — not UTF-8, and its bytes do not match any binary format "
                "this gate can prove carries no prose; cannot be checked, and that is not a pass")
            continue
        except OSError:
            problems.append(f"UNREADABLE: {rel} — cannot be read at all, and that is not a pass")
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
        if len(parts) < PARTS_IN_A_HEADER_LINE:
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
