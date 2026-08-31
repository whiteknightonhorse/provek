#!/usr/bin/env python3
"""LAW-STAGED-MEDIA-LANDING-ONLY - D-42's narrow exception is bounded by code, not by a promise.

D-42 lifts the ornament ban (D-07, SPEC S10) for exactly one surface: three video clips on the
landing page, below the first screen, each captioned as a staged illustration. Every other locus
the ban ever stood in - D-18's own paragraph on notes, the evidence pages, SPEC S3.2's registry
density, SPEC S3.1's passport - is untouched, and "untouched" is a claim this gate makes true
rather than a claim the decision text merely makes.

TWO THINGS THIS CHECKS, MATCHING TASK B'S OWN FLOOR:
  1. a media asset served from web/public/media/ (runtime path /media/...) is referenced from
     Landing.tsx ONLY - never from any other file under web/src or web/functions;
  2. if Landing.tsx does reference one, the file must also carry the staged-scene caption
     (D-42 predicate 3) - a video with no caption is not the thing the decision admitted.

WHAT THIS DOES NOT CHECK, NAMED RATHER THAN SILENTLY SKIPPED. Predicates 1 (zero OCR'd
characters), 2 (no interface/document/number in frame) and 5 (no registry.json fact reproduced in
pixels) are properties of the rendered VIDEO FILE, not of the source tree, and no asset exists yet
to run them against (the boundary this task operates under forbids generating or committing one).
A static ratchet that claimed to cover them would be exactly the checker L-31 warns about: more
permissive than the thing it stands in for. Those three stay owed to whatever gate runs at
generation time, and D-42 names that explicitly rather than letting this module's green imply more
than it measures (invariant 1).

WHY web/ IS WALKED HERE AND NOT BY ratchet_scope.py. `T-SCOPE-RATCHET`'s SCAN tuple is
`("src", "scripts", "demo")` - the frontend has never been in its scope, and widening that ratchet
is a different task than this one. This module owns its own walk of `web/src` and `web/functions`
for exactly the two extensions that can hold a JSX/JS media reference.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB_SRC = ROOT / "web" / "src"
WEB_FUNCTIONS = ROOT / "web" / "functions"
LANDING = WEB_SRC / "pages" / "Landing.tsx"

# The five evidence surfaces D-42 says the exception cannot reach, named explicitly rather than
# inferred from "everything but Landing.tsx" - a page added later under web/src/pages/ that is
# NEITHER Landing nor one of these is still caught by the generic "outside Landing" branch below,
# but these five get the sharper message because D-42 discusses them by name.
EVIDENCE_FILES = (
    WEB_SRC / "pages" / "Passport.tsx",
    WEB_SRC / "pages" / "Registry.tsx",
    WEB_SRC / "pages" / "Method.tsx",
    WEB_SRC / "pages" / "Phase2.tsx",
    WEB_FUNCTIONS / "p" / "[id]" / "brief.js",
)

SCAN_EXTS = {".tsx", ".ts", ".jsx", ".js"}

# A `src=`/`href=` (bare, quoted, or inside a `{...}` expression) whose value contains `/media/` -
# the runtime path `web/public/media/*` is served at, per Vite's public-dir convention this project
# already uses for every other asset under web/public/. Does not match Passport.tsx's own
# `<img src="${badgeUrl}">` embed snippet, which points at `/badge/<slug>.svg`, a different
# endpoint - matching on `/media/` rather than on `<img>`/`<video>` generically is what keeps that
# distinction rather than flagging every image tag on the site.
#
# ponytail: matches a src=/href= attribute value, not an ES import statement
# (`import clip from "/media/x.mp4"`). No file in this tree does the latter today - Vite's
# public-dir assets are conventionally referenced by string path, not imported - so widening the
# pattern is deferred until a real import shows up.
MEDIA_REF_RE = re.compile(r"""(?:src|href)\s*=\s*[{"'][^"'{}]*/media/[^"'}\s]+""")

STAGED_CAPTION = "Staged scene — an illustration, not a measurement."


def _scan_files() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for base in (WEB_SRC, WEB_FUNCTIONS):
        if base.is_dir():
            files.extend(p for p in base.rglob("*") if p.is_file() and p.suffix in SCAN_EXTS)
    return sorted(files)


def check() -> list[str]:
    """List of violations. An EMPTY list means clean; None is never returned (invariant 1)."""
    problems: list[str] = []
    evidence_set = set(EVIDENCE_FILES)

    landing_text = LANDING.read_text(encoding="utf-8") if LANDING.exists() else ""
    if MEDIA_REF_RE.search(landing_text) and STAGED_CAPTION not in landing_text:
        problems.append(
            f"{LANDING.relative_to(ROOT)}: references a /media/ asset without the staged-scene "
            f"caption {STAGED_CAPTION!r} - D-42 predicate 3 is void without it"
        )

    for f in _scan_files():
        if f == LANDING:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            problems.append(f"{f.relative_to(ROOT)}: unreadable ({exc})")
            continue
        if not MEDIA_REF_RE.search(text):
            continue
        rel = f.relative_to(ROOT)
        if f in evidence_set:
            problems.append(
                f"{rel}: an evidence surface references a /media/ asset - D-42 predicate 4 "
                f"forbids this absolutely, and the exception admits no locus outside Landing.tsx"
            )
        else:
            problems.append(
                f"{rel}: references a /media/ asset outside Landing.tsx - D-42 confines the "
                f"staged-scene exception to the landing page and nowhere else"
            )
    return problems


def main() -> int:
    problems = check()
    if problems:
        sys.stderr.write("\nX LAW-STAGED-MEDIA-LANDING-ONLY:\n" + "".join(f"  - {p}\n" for p in problems))
        return 1
    print("LAW-STAGED-MEDIA-LANDING-ONLY: clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
