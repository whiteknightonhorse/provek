#!/usr/bin/env python3
"""T-DECISION-1 - a ratified decision with no armed gate fails the build.

TWO SYMMETRIC DEFECTS, both paid for in the operator's systems (ABI-16-8, ABI-16-9):
  1. PARTIAL IMPLEMENTATION - the code satisfies an outdated declaration while a ratified decision
     remains unimplemented. Nothing asks whether an accepted law actually landed.
  2. SURVIVED ITS OWN REPEAL - a rule was repealed in one place while an armed copy elsewhere kept
     enforcing. "A rule written in more than one place survives its own repeal."

This gate catches the first: a law in enforced_by.yaml whose gate or test does not exist is
dangling.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LAWS = ROOT / "enforced_by.yaml"


def _tracked() -> set[str] | None:
    """Every path git is tracking, or None if git could not be asked.

    None is a THIRD STATE and the callers treat it as one. "The gate file is not in the repository"
    and "we could not find out" are different facts, and returning an empty set for the second
    would report every law in the file as dangling - a false red, which teaches walking past a gate
    exactly as a false green does (L-5).
    """
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return {p for p in out.stdout.decode("utf-8", "replace").split("\0") if p}


def _load_laws(path: pathlib.Path) -> list[dict]:
    laws, cur = [], None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        s = line.strip()
        if s.startswith("- id:"):
            if cur:
                laws.append(cur)
            cur = {"id": s.split(":", 1)[1].strip()}
        elif cur is not None and ":" in s and not s.startswith("-"):
            k, v = s.split(":", 1)
            cur[k.strip()] = v.strip().strip('"')
    if cur:
        laws.append(cur)
    return laws


def check() -> list[str]:
    if not LAWS.exists():
        return [f"{LAWS} is missing - the law registry is ABSENT, which differs from being empty"]
    problems = []
    laws = _load_laws(LAWS)
    if not laws:
        problems.append("the law registry is EMPTY - a different state from 'no registry', "
                        "and both are suspicious")
    # EXISTS ON THIS DISK IS NOT THE SAME FACT AS REACHES A CLONE.
    #
    # This ratchet asked `Path.exists()` and nothing else, so a law whose gate and test sat
    # untracked - or under an ignored path - passed here and was dangling for everyone else. That
    # state was real in this tree, not hypothetical: four LAW-NOTES-* entries were committed while
    # `web/notes/emit.mjs` and `tests/test_notes*.py` were still untracked, and every gate went
    # green. `push.sh` refuses a dirty tree now, but this is the stronger place to fix it - the
    # door can be walked around, whereas a law that names an unreachable file is wrong wherever it
    # is read. It is also L-3 in its own right: what the consumer receives is the clone.
    tracked = _tracked()
    for law in laws:
        lid = law.get("id", "<no id>")
        for field in ("gate", "test"):
            ref = law.get(field)
            if not ref:
                problems.append(f"DANGLING LAW {lid}: does not name a {field}")
            elif not (ROOT / ref).exists():
                problems.append(f"DANGLING LAW {lid}: {field}={ref} DOES NOT EXIST")
            elif tracked is not None and ref not in tracked:
                problems.append(
                    f"DANGLING LAW {lid}: {field}={ref} exists here but is NOT TRACKED by git, "
                    "so it does not reach a clone and this law is unenforced everywhere else")
    if tracked is None:
        # Named, not swallowed. The check did not run, and that is reported as its own state
        # rather than folded into the clean line (invariant 1).
        problems.append(
            "git could not be asked which files are tracked, so the reachable-in-a-clone half of "
            "this gate DID NOT RUN - that is unknown, not clean")
    return problems


def main() -> int:
    p = check()
    if p:
        sys.stderr.write("\nX T-DECISION-1:\n" + "".join(f"  - {x}\n" for x in p))
        return 1
    # SAY WHAT WAS MEASURED, NOT WHAT ONE WOULD LIKE IT TO MEAN. This line read "N laws, all
    # armed" - but `check()` above resolves two paths and asks whether files EXIST. It cannot
    # tell an armed gate from a present one: four LAW-NOTES-* modules carried
    # `skipif(not sources())` and were counted among the "armed" while every assertion in them
    # skipped, in precisely the state that shipped a defect to the built site. A tool that
    # reports `present` as `armed` is invariant 1 turned on the project's own instrument, and it
    # is the more dangerous instance because this is the tool the others are checked with.
    print(f"T-DECISION-1: clean ({len(_load_laws(LAWS))} laws, every gate and test present)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
