#!/usr/bin/env python3
"""LAW-PUBLISH-JUDGED-TREE - the unattended publisher ships only a tree the gates judged.

WHY THIS EXISTS, AND WHY IT EXISTS TODAY. `scripts/push.sh` already refuses a dirty tree, and says
why: "the gates judged the working tree, what goes out is the commit", so a tree that is not equal
to HEAD means the gates proved nothing about the artefact leaving the host. Until T-C5 the SITE had
no equivalent, and it did not need one - `~/orchestra/notes_cron.py` could never actually deploy
(it looked for a `wrangler` binary this host does not have), so the daily cycle reached
`blocked_no_tool` and published nothing at all. T-C5 makes that step work. The hazard is therefore
one this change CREATES rather than one it inherits, which is why the guard ships in the same
commit as the fix instead of being written down as a risk.

WHAT IT IS GUARDING AGAINST IS ROUTINE HERE, NOT HYPOTHETICAL. Work in progress is parked in this
working tree between tasks on purpose - a stash restored "byte-identical" is the established habit,
and on 2026-08-24 at 02:59 a parked T-A2-5 change to `/apply/` sat in the tree, unpushed and unseen
by any gate, two hours before the day's publication slot. Nobody is at the keyboard at 05:22 UTC.
Without this check the scheduler would have published that copy to provek.dev, and the cycle would
have reported itself green for doing it.

`--commit-dirty=true` IS PASSED BY `~/orchestra/deploy.sh` AND THAT IS NOT THE SAME PERMISSION.
There, a human agent has just run the gates and knows what is in the tree; the flag suppresses a
warning about a state that was deliberately chosen. Here there is no chooser. The same flag under a
cron entry means "publish whatever happens to be lying on disk", and the difference between those
two is the entire subject of this file.

THE CYCLE DIRTIES THE TREE BY DESIGN, SO "CLEAN" IS THE WRONG QUESTION. `step_capture` writes a new
note into `web/notes/src/` and rewrites `web/notes/manifest.json`; the build rewrites
`web/dist-ssr/`. A rule of "refuse anything dirty" would block every cycle forever, which is a gate
that gets deleted by the first person it stops. The measured question is narrower and answerable:
is anything dirty here OTHER than what this cycle itself produced? Those paths are listed once,
below, and everything else is foreign.

THREE OUTCOMES, NOT TWO (invariant 1). "publishable", "foreign work is present" and "we could not
read the tree" are three different facts. Collapsing the third into the first publishes on the
strength of a check that did not run - which is the shape this project exists to catch - and
collapsing it into the second manufactures a daily false red that teaches walking past the gate
(L-5). Each gets its own exit code and its own printed line.

Bound to ABI-32-1 (the door is the only way out) and ABI-16-5 (a refusal is a named state).
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

# Paths the publication cycle itself writes. A dirty path under one of these is the cycle's own
# output; a dirty path anywhere else is somebody's parked work.
#
# `web/dist-ssr/` and `web/dist/` are build products - the first is tracked and rewritten by every
# `npm run build`, the second is gitignored and never appears here at all. Listing a generated
# directory as cycle-owned means a hand edit inside it would also pass, and that is accepted rather
# than glossed: the next build overwrites it, so an edit there is not content a reader can receive.
CYCLE_OWNED = (
    "web/notes/src/",
    "web/notes/manifest.json",
    "web/dist/",
    "web/dist-ssr/",
)

PUBLISHABLE = 0
FOREIGN_WORK = 3
UNREADABLE = 4

# Width of porcelain v1's status field: two status letters and the space that follows them, as in
# `" M web/src/pages/Apply.tsx"`. Named because `test_no_threshold_is_a_bare_number_at_the_point_of
# _comparison` refused it as a literal, and it was right to: read as a bare `3` in a slice guard it
# is indistinguishable from a policy number, and this one is a fact about git's output format that
# the day it changes should be findable by its name.
PORCELAIN_STATUS_WIDTH = 3


def _porcelain(root: pathlib.Path) -> list[str] | None:
    """Dirty paths, or None if git could not be asked.

    None is a THIRD STATE and every caller treats it as one, exactly as `ratchet_decisions._tracked`
    does. An empty list here would say "the tree is clean" about a directory we failed to read.
    """
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "-z", "--untracked-files=all"],
            cwd=str(root), capture_output=True, timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None

    paths: list[str] = []
    for entry in out.stdout.decode("utf-8", "replace").split("\0"):
        if not entry:
            continue
        # Porcelain v1 is "XY<space>path". Renames emit "XY old\0new" - the NUL split hands us the
        # old name as its own bare entry, which has no status prefix. Both halves of a rename are
        # dirty paths, so the bare form is kept rather than skipped.
        has_status = len(entry) > PORCELAIN_STATUS_WIDTH and entry[PORCELAIN_STATUS_WIDTH - 1] == " "
        paths.append(entry[PORCELAIN_STATUS_WIDTH:] if has_status else entry)
    return paths


def classify(root: pathlib.Path) -> tuple[int, list[str], list[str]]:
    """(exit code, foreign paths, cycle-owned paths). Never raises for a dirty or unreadable tree."""
    dirty = _porcelain(root)
    if dirty is None:
        return UNREADABLE, [], []
    owned = [p for p in dirty if any(p.startswith(prefix) for prefix in CYCLE_OWNED)]
    foreign = [p for p in dirty if p not in owned]
    return (FOREIGN_WORK if foreign else PUBLISHABLE), foreign, owned


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(pathlib.Path(__file__).resolve().parents[1]),
                    help="repository to judge (default: this repository)")
    args = ap.parse_args(argv)

    code, foreign, owned = classify(pathlib.Path(args.root))
    if code == UNREADABLE:
        print(f"UNREADABLE: git could not report the state of {args.root}. This says NOTHING about "
              f"whether the tree is publishable - it is not a clean tree and not a dirty one.",
              file=sys.stderr)
        return UNREADABLE
    if code == FOREIGN_WORK:
        print(f"FOREIGN WORK IN THE TREE ({len(foreign)} path(s)): an unattended publisher would "
              f"ship changes no gate has judged.", file=sys.stderr)
        for p in foreign:
            print(f"  - {p}", file=sys.stderr)
        return FOREIGN_WORK
    print(f"PUBLISHABLE: nothing dirty outside the {len(CYCLE_OWNED)} cycle-owned paths "
          f"({len(owned)} cycle-owned path(s) dirty).")
    return PUBLISHABLE


if __name__ == "__main__":
    raise SystemExit(main())
