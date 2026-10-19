#!/usr/bin/env python3
"""T-MY-01 - read every dated promise in the CI workflow BEFORE the door reads it for us.

WHY THIS EXISTS. The mypy advisory deadline (`ADVISORY-UNTIL: 2026-10-15`) was armed with a clock -
`tests/test_door_matches_ci.py` goes red when it passes - and nothing that read the clock ahead of
time. It fired on 2026-10-16, stopped the nightly chain at the door and left the published registry
four nights stale. The test is the bomb; this is the missing reading of how long the fuse is.

One line per promise, `<step name>: until <date>, <k> days left, stage=OK|WARN|LAST_DAY|EXPIRED`.

  exit 0  every promise is OK
  exit 1  any promise is WARN, LAST_DAY or EXPIRED - the remedy is printed, and it is a decision:
          ratify a new date in DECISIONS.md with the count, or make the step blocking
  exit 2  the file is unreadable or carries no sentinel at all. That is `not_measured`, never
          "nothing due": a reader that finds no promises in a file that used to hold one has not
          found that nothing is promised.

The margin is `RENEWAL_MARGIN` from src.liveness.obligations - one constant (L-2). The sentinel text
is restated here rather than imported from tests/, which this script must not depend on.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.liveness.obligations import RENEWAL_MARGIN  # noqa: E402

WORKFLOW = ROOT / ".github" / "workflows" / "gates.yml"
SENTINEL = "ADVISORY-UNTIL:"
_DATE = re.compile(re.escape(SENTINEL) + r"\s*(\d{4}-\d{2}-\d{2})")
_STEP = re.compile(r"^\s*-\s*name:\s*(.+?)\s*$")

REMEDY = ("remedy, BEFORE the door goes red: ratify a new date in DECISIONS.md with the count that "
          "justifies it, or make the step blocking and add it to scripts/push.sh in the same commit")


def promises(text: str) -> list[tuple[str, date]]:
    """(label, date) for each sentinel; label is the enclosing step's name, else `line N`."""
    found: list[tuple[str, date]] = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = _DATE.search(line)
        if not m:
            continue
        label = f"line {i + 1}"
        for j in range(i, -1, -1):
            s = _STEP.match(lines[j])
            if s:
                label = s.group(1).strip("'\"")
                break
        found.append((label, date.fromisoformat(m.group(1))))
    return found


def stage(days_left: int) -> str:
    if days_left < 0:
        return "EXPIRED"
    if days_left <= 1:
        return "LAST_DAY"
    if days_left <= RENEWAL_MARGIN.days:
        return "WARN"
    return "OK"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--today", help="YYYY-MM-DD, for tests")
    ap.add_argument("--file", default=str(WORKFLOW), help="workflow file to read")
    args = ap.parse_args(argv)
    today = (date.fromisoformat(args.today) if args.today
             else datetime.now(timezone.utc).date())
    try:
        text = Path(args.file).read_text(encoding="utf-8")
    except OSError as e:
        print(f"not_measured: cannot read {args.file}: {e}")
        return 2
    found = promises(text)
    if not found:
        print(f"not_measured: no {SENTINEL} sentinel in {args.file} - that is a reading failure, "
              "not 'nothing due'")
        return 2
    bad = False
    for label, until in found:
        left = (until - today).days
        st = stage(left)
        when = f"{left} days left" if left >= 0 else f"expired {-left} days ago"
        print(f"{label}: until {until.isoformat()}, {when}, stage={st}")
        bad = bad or st != "OK"
    if bad:
        print(REMEDY)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
