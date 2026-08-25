#!/usr/bin/env python3
"""LAW-EVIDENCE-STAMPED-TREE - every evidence artefact names the tree it was produced against.

WHY. `evidence/*.txt` quotes line numbers, diffs and file paths out of the working tree at the
moment its generator ran. Every one of those citations is a claim about a specific revision, and
until now no artefact SAID which one. The first divergence already landed: RED-032 was written
against line numbers that T-S5 later moved, and nothing in the file itself told a reader that its
citations had gone stale - the artefact still read as current because it carried no date the tree
could be checked against (invariant 1, applied to our own corpus rather than to a subject's).

D-28 forbids editing an old artefact to fix this after the fact: the fix is forward-only, one
generator at a time, starting with this helper existing at all. `*-generator.py` scripts import
`tree_stamp()` and write its return value into the first few lines of what they produce.
`scripts/ratchet_evidence.py` is what holds new artefacts to carrying it.

THREE STATES, NOT TWO (invariant 1, ABI-13-6/ABI-16-11/ABI-33-4 - the same cluster
`src/abs_profile/measured.py` binds, applied here to a different counter that can just as easily
be silently wrong): the tree read clean, the tree read dirty, or git could not be asked at all -
and the last of those is written down as `unreadable` rather than folded into either of the other
two. A generator run in a checkout that cannot be asked about its own state has produced an
artefact whose provenance is not established, which is a fact worth keeping rather than a reason to
guess.

REUSES `publishable_tree._porcelain` FOR THE DIRTY READING RATHER THAN A SECOND COPY (L-2). That
reader already carries the D-33 fix: `git status` warns on stderr and exits 0 when a subtree could
not be entered, so a naive `bool(git status --porcelain)` would report such a tree CLEAN. Importing
the shared reader means this module inherits that fix instead of reintroducing the hole it closed.
"""
from __future__ import annotations

import pathlib
import subprocess

# `scripts/` is on `sys.path` for a script run from it, and the tests put it there explicitly -
# same as `scripts/deploy_label.py`'s identical import of this reader, no path surgery needed here.
from publishable_tree import _porcelain  # shared reader, not a second copy of D-33's fix (L-2)

ROOT = pathlib.Path(__file__).resolve().parents[1]

FULL_SHA_CHARS = 40  # width of what `git rev-parse HEAD` prints; see deploy_label.py's own note


def _head(root: pathlib.Path) -> str | None:
    """The full commit id, or None if git could not be asked. None is a state, not an empty string."""
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(root),
                              capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    sha = out.stdout.decode("utf-8", "replace").strip()
    return sha if len(sha) == FULL_SHA_CHARS else None


def read_tree(root: pathlib.Path = ROOT) -> tuple[str | None, bool | None]:
    """(head sha or None, dirty or None). `None` in a slot means that half is UNREADABLE."""
    return _head(root), (bool(dirty) if (dirty := _porcelain(root)) is not None else None)


def tree_stamp(root: pathlib.Path = ROOT) -> str:
    """One line for an artefact's header. Never silently omits the state it could not read.

    `tree: <sha>`                          - clean at generation time
    `tree: <sha> (dirty)`                  - uncommitted changes were present
    `tree: <sha> (dirty-state unreadable)` - the commit is known, git would not say if it was clean
    `tree: unreadable`                     - git could not be asked at all
    """
    head, dirty = read_tree(root)
    if head is None:
        return "tree: unreadable"
    if dirty is None:
        return f"tree: {head} (dirty-state unreadable)"
    return f"tree: {head} (dirty)" if dirty else f"tree: {head}"


if __name__ == "__main__":
    print(tree_stamp())
