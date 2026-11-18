#!/usr/bin/env python3
"""T-ID-01 - the door refuses an unpushed commit written under a foreign identity.

On 2026-11-12 a task session committed c57c779 with
`git -c user.name=incubator -c user.email=incubator@localhost commit`. The platform attributed it to
no account, this repository's identity window opened, and its level fell from L3 to L2 for 30 days.

Reads author e-mail and committer e-mail of every commit in `origin/main..HEAD` and nothing else:
pushed history is never read or judged. Standard library only, no network.

  exit 0  `identity: ok <n> commits`        every commit in the range carries an allowed address
  exit 0  `identity: nothing_to_check`      the range is empty
  exit 1  `identity: REFUSED <sha> ...`     one line per offending commit, then the instruction
  exit 2  `identity: unreadable <error>`    git failed or origin/main does not resolve

An unreadable range is never an empty range (invariant 1).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The one tracked list of addresses an unpushed commit may carry, as author AND as committer.
# Adding an address is a reviewed change to this constant, never a flag, an environment variable or
# an edit made on the way to a push.
ALLOWED_EMAILS = frozenset({"noreply@anthropic.com"})

INSTRUCTION = ("on the unpushed commit run `git commit --amend --reset-author --no-edit`; "
               "if it is not HEAD, report to the dispatcher; never force-push")

RANGE = "origin/main..HEAD"


def _git(repo: Path, *args: str) -> tuple[int, str, str]:
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    except OSError as exc:
        return 127, "", str(exc)
    return r.returncode, r.stdout, r.stderr


def _unreadable(why: str) -> int:
    why = " ".join(why.split()) or "no error text"
    print(f"identity: unreadable {why}")
    return 2


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", type=Path, default=ROOT, help="repository to read (for tests)")
    args = ap.parse_args(argv)

    rc, _, err = _git(args.repo, "rev-parse", "--verify", "--quiet", "origin/main^{commit}")
    if rc != 0:
        return _unreadable(err or "origin/main does not resolve")
    rc, out, err = _git(args.repo, "log", "--format=%H%x09%ae%x09%ce", RANGE)
    if rc != 0:
        return _unreadable(err)

    rows = [ln.split("\t") for ln in out.splitlines() if ln.strip()]
    if any(len(r) != 3 for r in rows):
        return _unreadable(f"unexpected git log output: {out[:80]!r}")
    if not rows:
        print("identity: nothing_to_check")
        return 0

    refused = [(sha, a, c) for sha, a, c in rows
               if a not in ALLOWED_EMAILS or c not in ALLOWED_EMAILS]
    if not refused:
        print(f"identity: ok {len(rows)} commits")
        return 0
    for sha, a, c in refused:
        print(f"identity: REFUSED {sha[:7]} author {a} committer {c}")
    print(INSTRUCTION)
    return 1


if __name__ == "__main__":
    sys.exit(main())
