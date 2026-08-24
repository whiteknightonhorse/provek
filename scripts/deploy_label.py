#!/usr/bin/env python3
"""LAW-DEPLOY-LABEL-TRUE - what a deployment is CALLED must describe what was published.

THE DEFECT THIS CLOSES, MEASURED. `~/orchestra/deploy.sh` built `web/` from the WORKING TREE and
then labelled the result with `git rev-parse --short HEAD`. Those are two different artefacts
whenever the tree is dirty, and the script said so about neither: `--commit-dirty=true` was passed
unconditionally, so Cloudflare could not tell a deliberate dirty publication from a clean one
either. The line `DEPLOY CONFIRMED on <sha>` was therefore true of a commit and false of the site,
and the operator's deploy log - the only record of what is live - carried the commit's name over
somebody else's uncommitted content.

THE DEPLOY OF 2026-08-24 01:41 PASSED THROUGH THAT HOLE WITHOUT FALLING IN, AND THAT IS NOT A
DEFENCE. The tree happened to be clean at that minute because the work in progress was parked in a
stash. `scripts/publishable_tree.py` records the opposite arrangement on the SAME MORNING at 02:59:
a T-A2-5 rewrite of `/apply/` sitting unstashed in the tree, two hours before the scheduler's slot.
A hole that is closed by where the work happened to be lying is not closed.

WHY THIS IS NOT `publishable_tree.py` AGAIN. That gate answers the SCHEDULER's question - "is
anything dirty here other than what this cycle itself writes" - because the cycle authors a note on
every run and a refuse-all rule would stop it every day and be deleted by the first agent it
stopped. This one answers the OPERATOR's question, and the answers differ in both directions: a
human deploy has no cycle-owned exemption (a hand-edited note is content no gate judged, exactly
like a hand-edited page), and a human may deliberately publish a dirty tree, which the unattended
cycle may never do. Two callers, two policies, one shared reading of git's output - imported from
that module rather than copied, because a second `git status` parser would be the same rule written
twice (L-2) and would drift the first time porcelain's format did.

THE PERMISSION AND THE LABEL ARE SEPARATE, AND THE SECOND IS THE POINT. `--allow-dirty` lets the
operator publish an unjudged tree; it does NOT let the deployment keep calling itself by a commit's
name. A dirty publication is labelled `dirty-<digest>` over the content actually on disk, and the
short sha never appears alone in that case. Without the second half the flag would simply reopen
the hole with a nicer spelling.

THREE OUTCOMES, NOT TWO (invariant 1). `labelled`, `refused because the tree is dirty` and `the
tree could not be read` are three facts. Collapsing the third into the first publishes under a name
earned by a check that did not run - a claim stronger than the artefact, which is the defect this
whole project exists to find - and collapsing it into the second manufactures a refusal that sends
the operator to look for uncommitted work that may not exist.

A NAMED LIMIT, MEASURED WHILE WRITING THIS AND ONLY HALF CLOSED HERE. `git status` does not fail on
a directory it cannot read - it prints `warning: could not open directory 'sub/': Permission denied`
to stderr and EXITS 0 with that subtree simply missing from its output. So a tree carrying an
unreadable directory is reported CLEAN by the shared reader. That hole is in
`publishable_tree._porcelain`, which the SCHEDULER's gate depends on as well, so closing it changes
a shipped gate belonging to another task; it is written down in `~/orchestra/FINDINGS.md` for the
judge rather than fixed in passing.

What is closed here is the half this module can reach on its own: the clean path re-reads every file
`git ls-files` names, so a TRACKED file under such a directory turns the tree `unreadable` instead
of signing it with a commit's sha. See the comment on that line for which of the three states each
of these actually produces - all three were built as fixtures and measured, and one of them came out
the opposite way round from the prediction. An UNTRACKED file under an unreadable directory remains
invisible to `ls-files` exactly as it is to `status`, and nothing here sees it.

What this module claims is therefore exactly this: it refuses every dirty path git REPORTS, it
refuses a tree holding a tracked file it cannot read, and it does not claim git reported everything.

Bound to ABI-32-1 (the door is the only way out) and ABI-16-5 (a refusal is a named state).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import subprocess
import sys

# The underscore is deliberate and so is crossing it: `_porcelain` is private to the SCHEDULER's
# gate, and this module borrows the one thing both policies must agree on - how git's porcelain
# output is turned into a list of paths. Reimplementing that here would put the `XY ` prefix and the
# bare second half of a rename in two places, and the second copy would be wrong on the day the
# first one was fixed. `scripts/` is on `sys.path` for a script run from it, and the tests put it
# there explicitly.
from publishable_tree import _porcelain

LABELLED = 0
DIRTY_REFUSED = 3
UNREADABLE = 4

# Prefix and width of the content label. The prefix is the word a reader must be able to see without
# knowing anything about this project, which is why it is a word and not a sigil; the width is
# chosen to be long enough that two different trees in one day's deploy log will not collide by
# accident, and short enough to be read aloud. It is NOT a git object id and must never be mistaken
# for one - a git short sha is hex of the same shape, so the prefix is what keeps the two apart.
DIRTY_PREFIX = "dirty-"
DIGEST_CHARS = 12

# Length of the full commit id `git rev-parse HEAD` prints, and the width Cloudflare's
# `--commit-hash` field expects. Named because a bare 40 in a slice guard reads like a policy
# number: this one is a fact about git's output that the day it changes should be findable by name.
FULL_SHA_CHARS = 40


def _git(root: pathlib.Path, *args: str) -> str | None:
    """One line of git output, or None if git could not be asked.

    None is a THIRD STATE and every caller treats it as one, as `publishable_tree._porcelain` and
    `ratchet_decisions._tracked` do. Returning "" here would report an unreadable repository as one
    with an empty answer, and the answer this module gives is a name that goes on a published site.
    """
    try:
        out = subprocess.run(["git", *args], cwd=str(root), capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.decode("utf-8", "replace").strip()


def content_digest(root: pathlib.Path) -> str | None:
    """A hash of the bytes that would be published, or None if any of them could not be read.

    WHAT IT COVERS IS THE INPUT TO THE BUILD, NOT ITS OUTPUT. `web/dist/` is gitignored and never
    appears here; the site is rebuilt from these files by `deploy.sh` immediately after this runs.
    So the digest names the source a clean checkout would need in order to reproduce the upload,
    which is the fact a label is asked for when it is read back weeks later.

    Every entry is length-prefixed and NUL-terminated so that the serialisation cannot be forged by
    a filename containing the separator - two different trees must not be able to hash alike.
    A path git lists but the filesystem does not hold is a DELETION, which is a state of the content
    and is hashed as one; a path that exists and cannot be READ is a failed instrument, and that
    returns None rather than a digest over what was legible.
    """
    listing = _git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    if listing is None:
        return None
    h = hashlib.sha256()
    for rel in sorted(p for p in listing.split("\0") if p):
        h.update(str(len(rel)).encode())
        h.update(b"\0")
        h.update(rel.encode("utf-8", "surrogateescape"))
        h.update(b"\0")
        path = root / rel
        try:
            if path.is_symlink():
                target = os.readlink(path).encode("utf-8", "surrogateescape")
                h.update(b"symlink\0" + str(len(target)).encode() + b"\0" + target + b"\0")
            elif not path.exists():
                h.update(b"absent\0")
            elif path.is_dir():
                # A gitlink (submodule) or a directory git still lists. It has no bytes of its own
                # here; naming the shape keeps it distinct from an empty file. NAMED LIMIT: the
                # submodule's own commit is NOT hashed, so two different states of one would digest
                # alike. There are no submodules in this repository - `git ls-files` lists none -
                # so the limit is recorded rather than solved; the day one is added, this branch is
                # what has to change. Found by Fable.
                h.update(b"dir\0")
            else:
                data = path.read_bytes()
                h.update(b"file\0" + str(len(data)).encode() + b"\0" + data + b"\0")
        except OSError:
            return None
    return h.hexdigest()


def decide(root: pathlib.Path, allow_dirty: bool) -> tuple[int, dict[str, str], list[str]]:
    """(exit code, fields for the deploy command, dirty paths). Never raises for a dirty tree."""
    dirty = _porcelain(root)
    head = _git(root, "rev-parse", "HEAD")
    if dirty is None or head is None or len(head) != FULL_SHA_CHARS:
        return UNREADABLE, {}, []

    short = head[:7]
    subject = _git(root, "log", "-1", "--pretty=%s")
    if subject is None:
        return UNREADABLE, {}, []

    if not dirty:
        # THE DIGEST IS COMPUTED ON THE CLEAN PATH TOO, AND ITS VALUE IS THROWN AWAY. It is not
        # dead code and it is not computed for the number: what is wanted is the READING. It opens
        # every file git listed, so a file this process cannot read makes the tree `unreadable`
        # instead of signing it with a commit's sha.
        #
        # WHICH HALF OF THE LIMIT ABOVE THIS ACTUALLY COVERS, MEASURED rather than assumed - both
        # states were built as fixtures on this host, and the answer was the opposite of the one
        # predicted when the line was written:
        #
        #   tracked file under a directory this process cannot ENTER
        #       `status` reports NOTHING (it warns and exits 0), so the tree looks clean - and this
        #       reading is the only thing between that tree and a commit's sha. It returns
        #       UNREADABLE. This is the case the line is here for, and it is covered.
        #
        #   tracked file that cannot be READ, in a directory that can be entered
        #       `status` cannot compare it to the index, so git reports it as MODIFIED and the tree
        #       is refused as dirty before this line runs. The refusal is honest - the tree cannot
        #       be shown equal to HEAD - but it names the path as uncommitted work, which it is
        #       not. Named here rather than smoothed over: it sends the operator to `git status`,
        #       which will say the same thing, and not to the permission bit that caused it.
        #
        #   UNTRACKED file under either
        #       invisible to `ls-files` exactly as it is to `status`. NOT covered by anything here.
        #
        # So this narrows the hole named above; it does not close it. Suggested by Fable, which
        # also asked which half it covers - the question that produced the measurement.
        if content_digest(root) is None:
            return UNREADABLE, {}, []
        return LABELLED, {
            "LABEL": short,
            "COMMIT_HASH": head,
            "COMMIT_DIRTY": "false",
            "COMMIT_MESSAGE": f"{short} {subject}",
        }, []

    if not allow_dirty:
        return DIRTY_REFUSED, {}, dirty

    digest = content_digest(root)
    if digest is None:
        return UNREADABLE, {}, dirty
    label = DIRTY_PREFIX + digest[:DIGEST_CHARS]
    # THE COMMIT HASH STAYS, AND THE FLAG BESIDE IT IS WHAT MAKES IT HONEST. Cloudflare's deployment
    # record has exactly three fields for this (`wrangler pages deploy --help`, wrangler 4): a hash,
    # a dirty boolean, and a message. `commit_dirty=true` is that record's own way of saying "this
    # is that commit PLUS uncommitted changes", so the sha is a base and not a claim of identity -
    # but on its own it does not say WHICH changes, which is why the label the operator reads, and
    # the message stored next to the hash, are the content digest instead.
    return LABELLED, {
        "LABEL": label,
        "COMMIT_HASH": head,
        "COMMIT_DIRTY": "true",
        "COMMIT_MESSAGE": (f"DIRTY TREE published on the operator's explicit flag: content {label}, "
                           f"{len(dirty)} path(s) differ from base commit {short}, which does NOT "
                           f"describe what was published"),
    }, dirty


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(pathlib.Path(__file__).resolve().parents[1]),
                    help="repository whose tree is about to be published (default: this one)")
    ap.add_argument("--allow-dirty", action="store_true",
                    help="publish an unjudged tree anyway; the label then names the content, "
                         "never the commit")
    args = ap.parse_args(argv)

    code, fields, dirty = decide(pathlib.Path(args.root), args.allow_dirty)

    if code == UNREADABLE:
        print(f"UNREADABLE: git could not report on {args.root}, so there is no name this "
              f"deployment could truthfully carry. This says NOTHING about whether the tree is "
              f"clean - it is neither a refusal nor a permission.", file=sys.stderr)
        return UNREADABLE

    if code == DIRTY_REFUSED:
        print(f"REFUSED: the working tree is not clean, so a build from it would be published "
              f"under a commit's name while differing from that commit in {len(dirty)} path(s).",
              file=sys.stderr)
        for p in dirty:
            print(f"  - {p}", file=sys.stderr)
        print("Commit the work and deploy again, or pass --allow-dirty to publish it deliberately "
              "- the deployment is then labelled by its content and not by the commit.",
              file=sys.stderr)
        return DIRTY_REFUSED

    for key in ("LABEL", "COMMIT_HASH", "COMMIT_DIRTY", "COMMIT_MESSAGE"):
        print(f"{key}={fields[key]}")
    return LABELLED


if __name__ == "__main__":
    raise SystemExit(main())
