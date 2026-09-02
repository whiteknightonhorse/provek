#!/usr/bin/env python3
"""Produces evidence/RED-041-a-suppressed-ring-could-have-gone-dark-for-everyone.txt.

THE SUBJECT. 4133b08 fixed the operator's iPhone report (T-30-mobile-blue-bars: a full-width blue
bar at the top and bottom of `#main` after a tap navigation on `/registry/` and `/apply/`) by
tracking input modality ourselves and gating a `.no-focus-ring` class the CSS honours, instead of
trusting the browser's own `:focus-visible` heuristic - which cannot tell a script-focused `<div>`
that followed a tap from one that followed a keyboard route change. `tests/
test_focus_ring_hides_tap_not_keyboard.py` checks the fix is present AND checks the two ways it
could be silently undone: the tap artefact returning, and the more dangerous direction the
operator's brief explicitly warned against - keyboard focus disappearing for everyone, which would
look like nothing on a phone.

invariant 5 (CLAUDE.md): "the section exists" is not a test. This file proves the four checks in
that suite are not decorative by making, one at a time, four real edits to the live source - not a
fixture, the actual `web/src/index.css` and `web/src/App.tsx` this project ships - and watching the
matching test and ONLY the matching test go red, before reverting each edit and comparing the file
against its own sha256.

FOUR MUTATIONS, FOUR DISTINCT FAILURE MODES, NOT ONE REPEATED.

  1. Delete the global `:focus-visible` rule from index.css. This is the worst-case regression:
     keyboard focus stops being visible ANYWHERE on the site, not just quietly on #main - and
     nothing about it would be visible in the tap-only symptom the operator originally reported.
  2. Delete `#main.no-focus-ring:focus-visible { outline: none; }` from index.css. This is the
     literal bug returning: the blue bars are back on a tap.
  3. Change the toggle in App.tsx from `!usingKeyboard` to the constant `true`. This is the
     "fix that breaks accessibility to fix a cosmetic bug" the operator's brief named by name -
     a `.no-focus-ring` that is always applied would pass mutations 1 and 2's checks (both CSS
     rules still exist) while blinding a keyboard user on every route change.
  4. Delete the skip-link's `onFocus` clearer. A tap navigation immediately followed by Tab-to-
     skip-link would then land on `#main` still carrying a stale `no-focus-ring` from the tap,
     silencing the one focus ring a keyboard/AT user most needs (the skip target itself).

WHAT THIS FILE DOES NOT DO. It edits `web/src/index.css` and `web/src/App.tsx` in place and
restores each from an in-memory copy in a `finally`, verified byte-for-byte by sha256 afterwards.
It never touches `~/orchestra`, never runs a browser, and does not claim to reproduce the iPhone
rendering itself - only that the regression tests guarding the fix can fail, and fail on the
specific check each mutation targets. It writes one output file under `evidence/`.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp  # noqa: E402

OUT = ROOT / "evidence" / "RED-041-a-suppressed-ring-could-have-gone-dark-for-everyone.txt"
SUITE = "tests/test_focus_ring_hides_tap_not_keyboard.py"
INDEX_CSS = ROOT / "web" / "src" / "index.css"
APP_TSX = ROOT / "web" / "src" / "App.tsx"

MUTATIONS = [
    (
        "global :focus-visible rule deleted - keyboard focus goes dark EVERYWHERE",
        INDEX_CSS,
        ":focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; "
        "border-radius: 1px; }",
        "",
        "test_global_focus_visible_rule_still_rings_something",
    ),
    (
        "#main.no-focus-ring override deleted - the tap-triggered blue bars are back",
        INDEX_CSS,
        "#main.no-focus-ring:focus-visible { outline: none; }",
        "",
        "test_main_tap_suppression_rule_still_present",
    ),
    (
        "toggle hard-coded to a constant - always suppresses, blinding keyboard users too",
        APP_TSX,
        'top.current?.classList.toggle("no-focus-ring", !usingKeyboard);',
        'top.current?.classList.toggle("no-focus-ring", true);',
        "test_suppression_is_gated_on_tracked_modality_not_a_constant",
    ),
    (
        "skip-link's stale-suppression clearer deleted",
        APP_TSX,
        'onFocus={() => document.getElementById("main")?.classList.remove("no-focus-ring")}\n'
        "        ",
        "",
        "test_skip_link_clears_stale_suppression_on_focus",
    ),
]


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120)
    return p.returncode, p.stdout + p.stderr


def failed_tests(output: str) -> frozenset[str]:
    ids = set()
    for line in output.splitlines():
        if not line.startswith("FAILED ") or "::" not in line:
            continue
        ids.add(line[len("FAILED "):].split(" - ", 1)[0].strip().split("::", 1)[1])
    return frozenset(ids)


def main() -> int:
    pristine = {p: p.read_bytes() for p in {INDEX_CSS, APP_TSX}}
    digests = {p: hashlib.sha256(b).hexdigest() for p, b in pristine.items()}

    rc, before = run([sys.executable, "-m", "pytest", SUITE, "-q"])
    if rc != 0:
        print(f"REFUSED: {SUITE} is not green before anything is touched (exit {rc}).\n{before}")
        return 1

    blocks: list[str] = []
    seen: dict[str, str] = {}

    for i, (title, subject, find, repl, expect) in enumerate(MUTATIONS, 1):
        original = pristine[subject].decode("utf-8")
        if original.count(find) != 1:
            print(f"REFUSED: mutation {i} anchor appears {original.count(find)} times in "
                  f"{subject.relative_to(ROOT)}, not once.")
            return 1
        mutated = original.replace(find, repl)
        subject.write_text(mutated, encoding="utf-8")
        try:
            rc, out = run([sys.executable, "-m", "pytest", SUITE, "-q", "-rf"])
        finally:
            subject.write_bytes(pristine[subject])

        if rc != 1:
            print(f"REFUSED: mutation {i} exited {rc}; only exit 1 is a suite that ran and "
                  f"failed.\n{out}")
            return 1
        dead = failed_tests(out)
        if dead != frozenset({expect}):
            print(f"REFUSED: mutation {i} expected exactly {{{expect!r}}} to fail, got "
                  f"{sorted(dead)}.\n{out}")
            return 1
        seen[expect] = f"mutation {i}"

        shown = "".join(f"  - {ln}\n" for ln in find.splitlines() or [""])
        shown += "".join(f"  + {ln}\n" for ln in repl.splitlines()) if repl else "  + (deleted)\n"
        blocks.append(
            f"\n{'=' * 100}\nMUTATION {i} - {title}\n{'=' * 100}\n"
            f"\nApplied to {subject.relative_to(ROOT)}:\n\n{shown}\n"
            f"Test killed: {expect} (and only that one)\n"
            f"\n--- verbatim output of `python -m pytest {SUITE} -q -rf` ---\n\n{out}")

    for p in pristine:
        if hashlib.sha256(p.read_bytes()).hexdigest() != digests[p]:
            print(f"REFUSED: {p} was not restored byte for byte.")
            return 1

    rc, after = run([sys.executable, "-m", "pytest", SUITE, "-q"])
    if rc != 0:
        print(f"REFUSED: {SUITE} is not green after the restore (exit {rc}).\n{after}")
        return 1

    rc, collected_out = run([sys.executable, "-m", "pytest", SUITE, "-q", "--collect-only"])
    collected = {ln.split("::", 1)[1].strip()
                 for ln in collected_out.splitlines() if ln.startswith(SUITE) and "::" in ln}
    uncovered = sorted(collected - set(seen))

    OUT.write_text(
        f"RED-041 - a suppressed ring could have gone dark for everyone\n\n"
        f"{evidence_stamp.tree_stamp()}\n"
        f"DATE (UTC): 2026-09-02\n"
        f"SUBJECT   : web/src/index.css, web/src/App.tsx, judged by {SUITE}\n"
        f"TASK      : T-30-mobile-blue-bars\n"
        f"\n--- `python -m pytest {SUITE} -q` before anything is touched ---\n\n{before.strip()}\n"
        + "".join(blocks)
        + f"\n{'=' * 100}\nWHAT NOTHING ABOVE KILLED\n{'=' * 100}\n\n"
        f"{len(seen)} of {len(collected)} collected tests were targeted, each by exactly one "
        f"mutation.\n"
        + ("".join(f"  - {n}\n" for n in uncovered) or "  (none - every collected test was "
           "targeted by name)\n")
        + f"\n{'=' * 100}\nRESTORE\n{'=' * 100}\n\n"
        f"Both files compared against their own sha256 after every mutation was reverted: "
        f"unchanged.\n"
        f"\n--- `python -m pytest {SUITE} -q` after the restore ---\n\n{after.strip()}\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT.relative_to(ROOT)} - {len(seen)} mutations, all distinct")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
