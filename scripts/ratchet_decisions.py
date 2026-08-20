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
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LAWS = ROOT / "enforced_by.yaml"


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
    for law in laws:
        lid = law.get("id", "<no id>")
        for field in ("gate", "test"):
            ref = law.get(field)
            if not ref:
                problems.append(f"DANGLING LAW {lid}: does not name a {field}")
            elif not (ROOT / ref).exists():
                problems.append(f"DANGLING LAW {lid}: {field}={ref} DOES NOT EXIST")
    return problems


def main() -> int:
    p = check()
    if p:
        sys.stderr.write("\nX T-DECISION-1:\n" + "".join(f"  - {x}\n" for x in p))
        return 1
    print(f"T-DECISION-1: clean ({len(_load_laws(LAWS))} laws, all armed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
