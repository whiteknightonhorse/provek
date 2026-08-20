"""T-F3 - the incubator's OWN obligations, declared into the liveness registry (ABI-16-1, ABI-16-3,
ABI-16-4).

WHY THIS FILE EXISTS. `obligations.py` has been in the tree since T-2.10, with seven passing tests
and two laws pointing at it, and until today nothing declared an obligation into it: every
`Registry` in the repository was constructed inside a test and filled by that same test. Its own
docstring names the state - `produces_result_nobody_reads`, the fifth state of sleeping code - and
its own `sweep()` calls an empty registry suspicious. The layer built to make silence observable was
the silence, and no test could see it, because a test that builds its own registry can never find it
empty. That is the difference between a module being CORRECT and a module PARTICIPATING (ABI-16-3),
and this file is the participation.

WHAT IS WATCHED. Every published row carries its own `valid_until` and lapses to `stale` on it with
no event at all (ABI-15-5, LAW-STALE-IS-COMPUTED-AT-READ-TIME) - 2026-09-19 for all eight rows as of
the run of 2026-08-20 08:30 UTC, and the date is stamped with its reading because it stops being
true the first time this obligation is met. Nothing re-issues
them, and nothing would have said so: a registry of expired verdicts and a registry of fresh ones
are rendered by the same code path and differ only in a word computed at read time. The obligation
declared here is the commitment to re-run `scripts/cohort.py` before that date, on an interval short
enough that the finding arrives while the rows are still valid (`RENEWAL_MARGIN`).

WHAT THIS READS, AND WHAT IT THEREFORE CANNOT SAY. Evidence of participation is taken from
`web/public/data/registry.json` - the copy that enters the build, not the one `cohort.py` writes -
because a file in the repository is not what the consumer receives (L-3). It is still not the LIVE
artefact: publication is a manual `wrangler pages deploy` this host cannot perform (L-9, D-19), so a
reader at provek.dev may hold something older than this file. That last hop is an operator reading
and it is named in `docs/LIVENESS_OPERATIONS.md` rather than claimed here.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path

from src.liveness.obligations import (
    MAX_AGE,
    RENEWAL_MARGIN,
    Interval,
    Obligation,
    Registry,
)

ROOT = Path(__file__).resolve().parents[2]

SHIPPED = Path("web/public/data/registry.json")
"""The copy a reader receives, via `fetch("/data/registry.json")` in `web/src/App.tsx`."""

EMITTED = Path("public/registry/registry.json")
"""The copy `scripts/cohort.py` writes. Compared against SHIPPED below, never read in its place:
the two are kept in step by hand, so "the cohort ran" and "the run reached the build" are two
states of the world."""

COMPONENT = "cohort_reissue"
EXPECTED_EVIDENCE = ("a run of scripts/cohort.py that re-stamps every published row, reaching "
                     "web/public/data/registry.json")
CONSUMER = "web/src/App.tsx, which fetches /data/registry.json for every reader of the registry"


class ReadState(str, Enum):
    """Why a run timestamp is absent. None of these is a zero and none of them is clean.

    `NEVER_RUN` is deliberately NOT among them: this instrument cannot observe it. A registry file
    that does not exist means the cohort has not run OR that the build copy was removed OR that the
    checkout is partial, and collapsing those into "never ran" would be inventing a measurement.
    """

    READ = "read"
    FILE_ABSENT = "check_did_not_run:registry_file_absent"
    NOT_JSON = "unreadable:not_json"
    NO_TIMESTAMP_FIELD = "unreadable:no_generated_at"
    BAD_TIMESTAMP = "unreadable:generated_at_is_not_a_timestamp"
    NO_SUBJECTS_FIELD = "unreadable:no_subjects_array"


@dataclass(frozen=True)
class CohortRun:
    """What one registry file says about the run that produced it."""

    state: ReadState
    generated_at: datetime | None = None
    earliest_valid_until: datetime | None = None
    rows: int | None = None
    """None means NOT COUNTED - the file could not be read. Zero means the file was read and listed
    no subjects, which is a true zero and a different fact."""


def _parse_ts(raw: object) -> datetime | None:
    if not isinstance(raw, str):
        return None
    try:
        ts = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def read_run(path: Path) -> CohortRun:
    """Read one registry file. Every failure gets its own state; nothing collapses to a default."""
    if not path.exists():
        return CohortRun(ReadState.FILE_ABSENT)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return CohortRun(ReadState.NOT_JSON)
    if not isinstance(doc, dict) or "generated_at" not in doc:
        return CohortRun(ReadState.NO_TIMESTAMP_FIELD)
    generated_at = _parse_ts(doc["generated_at"])
    if generated_at is None:
        return CohortRun(ReadState.BAD_TIMESTAMP)
    subjects = doc.get("subjects")
    if not isinstance(subjects, list):
        return CohortRun(ReadState.NO_SUBJECTS_FIELD, generated_at=generated_at)
    lapses = [ts for ts in (_parse_ts(s.get("valid_until")) for s in subjects
                            if isinstance(s, dict)) if ts is not None]
    return CohortRun(ReadState.READ, generated_at=generated_at,
                     earliest_valid_until=min(lapses) if lapses else None,
                     rows=len(subjects))


def declare(run: CohortRun) -> Registry:
    """The incubator's obligations, as a registry that is NOT empty by construction.

    One obligation today. `Registry.sweep` treats an empty registry as suspicious, so this function
    returning nothing would itself be reported rather than read as clean - which is why the
    declaration lives here and not inside the caller that consumes it.
    """
    r = Registry()
    r.declare(Obligation(component=COMPONENT, expected_evidence=EXPECTED_EVIDENCE,
                         interval=Interval.BEFORE_REISSUE,
                         last_seen=run.generated_at, consumer=CONSUMER,
                         # `generated_at is None`, NOT `state is not READ`. `NO_SUBJECTS_FIELD`
                         # carries a timestamp that parsed cleanly: marking it unreadable threw
                         # away a measurement the instrument had taken and reported UNKNOWN over a
                         # quantity it was holding - and dropped the remedy with it. Found by Fable.
                         evidence_unreadable=run.generated_at is None))
    return r


REMEDY = ("Remedy: `python3 scripts/cohort.py`, copy public/registry/ and public/passports/ into "
          "web/public/data/, `git commit -m ...` (push.sh refuses a dirty tree), "
          "`./scripts/push.sh`, then ask the operator to deploy - the full form, runnable "
          "unattended, is in docs/LIVENESS_OPERATIONS.md.")
"""The commit is named because the first draft omitted it and the remedy therefore ended at
`REFUSED: the working tree is not clean` - a finding whose own instructions do not reach the door
it names (L-9). Both registry copies are tracked, so the `cp` always dirties the tree. `-m` is in
the string for the same reason one step down: the reader named in the operations note is an agent
in a non-interactive shell, where a bare `git commit` opens no editor and aborts. Both found by
Fable, one round apart."""

POLICY_TOLERANCE = timedelta(hours=1)
"""Slack on the comparison between the re-issue deadline and the published validity window.

WHAT IT IS FOR. Both quantities are POLICIES STATED IN DAYS, but what is measured is the gap
between two timestamps, and those agree exactly only because `scripts/cohort.py` happens to hold a
single module-level `now`. Any refactor that took the clock twice - the natural shape - would move
the observed window by seconds, and with no slack the check fired `DEADLINE TOO LATE TO ACT ON` on
the day the obligation was PERFORMED, over a difference of two seconds. A false red teaches walking
past a gate exactly as a false green does (L-5), and this one would have done it at the moment the
habit was being obeyed.

WHY AN HOUR AND NOT A DAY. The first fix used a day, and a day is the size of the drift the check
exists to catch: a `validity_days` of 29 passed silently, which is the most likely change to a
policy stated in whole days and precisely the L-2 divergence `PASSPORT_VALIDITY` is a copy of. The
quantity being tolerated is the elapsed time inside ONE cohort run - twenty-four GitHub reads,
seconds - so an hour is three orders of magnitude above the noise and a full day below the smallest
real change. Both the hole and the false red were found by Fable, one round apart."""


def findings(run: CohortRun, now: datetime, emitted: CohortRun | None = None) -> list[str]:
    """Named findings, or an empty list. Empty means CHECKED AND CLEAN, never "did not look"."""
    out: list[str] = []

    if run.state is not ReadState.READ and run.generated_at is None:
        out.append(
            f"NOT MEASURED: the shipped registry at {SHIPPED.as_posix()} is {run.state.value}, so "
            "how long ago the cohort last ran WAS NOT ESTABLISHED. The obligation below is "
            "reported as NOT ASSESSED for the same reason, and neither line says the cohort failed "
            "to run - that is a different fact and this instrument cannot see it")
    elif run.state is not ReadState.READ:
        # A partial read is not a failed one. `generated_at` parsed, so the interval below IS
        # assessed on a real measurement, and only the rest of the document is missing.
        out.append(
            f"PARTIALLY READ: the shipped registry at {SHIPPED.as_posix()} is {run.state.value}. "
            "`generated_at` was read, so the interval below is assessed on it; what is unknown is "
            "everything the missing part would have said")

    out.extend(declare(run).sweep(now))

    # THE DEADLINE MUST LAND BEFORE THE LAPSE IT EXISTS TO PREVENT.
    #
    # `MAX_AGE[BEFORE_REISSUE]` is derived from a copy of the passport's validity window. This is
    # the measurement that keeps the copy honest: it compares the interval against the window the
    # SHIPPED rows actually carry, so shortening the validity anywhere turns into a finding here
    # instead of into a warning that arrives after the rows have already gone stale.
    #
    # The comparison is between two WINDOWS rather than between two instants, so that it does not
    # silently depend on `cohort.py` stamping `generated_at` and `valid_until` from one clock read.
    if run.generated_at is not None and run.earliest_valid_until is not None:
        published_window = run.earliest_valid_until - run.generated_at
        needed = MAX_AGE[Interval.BEFORE_REISSUE] + RENEWAL_MARGIN
        if needed > published_window + POLICY_TOLERANCE:
            out.append(
                f"DEADLINE TOO LATE TO ACT ON: the {Interval.BEFORE_REISSUE.value} interval plus a "
                f"{RENEWAL_MARGIN.days}-day margin needs {needed.days} days of validity, and the "
                f"shipped rows carry {published_window.days}. The re-issue finding would arrive "
                f"with less than {RENEWAL_MARGIN.days} days left to act on it: the interval and "
                "the published validity window have diverged")

    if run.rows == 0:
        out.append("EMPTY SHIPPED REGISTRY: the file was read and lists no subjects. That is a "
                   "measured zero, not an unread file, and no row can be re-issued from it")
    elif run.rows and run.earliest_valid_until is None:
        out.append(
            f"NOT MEASURED: {run.rows} rows ship and not one carries a readable `valid_until`, so "
            "the date this obligation exists to beat IS UNKNOWN. The interval above still fires on "
            "time; what cannot be checked is whether firing on time is early enough")

    # "The cohort ran" and "the run reached the artefact that ships" are separate facts, and the
    # copy between them is made by hand. A fresh emitted file beside a stale shipped one is the
    # state in which the obligation above reads clean for the wrong reason.
    if emitted is not None and run.state is ReadState.READ:
        if emitted.state is not ReadState.READ:
            # A comparison that stands down when half its input is missing prints the same nothing
            # as a comparison that ran and found the copies in step. This module gives six names to
            # failures of one file and gave none to failures of the other. Found by Fable.
            out.append(
                f"NOT COMPARED: {EMITTED.as_posix()} is {emitted.state.value}, so whether the last "
                "cohort run reached the copy that ships WAS NOT CHECKED")
        elif emitted.generated_at > run.generated_at:
            out.append(
                f"RUN NOT SHIPPED: {EMITTED.as_posix()} was generated at "
                f"{emitted.generated_at.isoformat()}, later than the build copy at "
                f"{run.generated_at.isoformat()}. The cohort ran and the reader still holds the "
                "older verdicts")
        elif emitted.generated_at < run.generated_at:
            # THE OTHER DIRECTION, AND IT IS THE ONLY CROSS-CHECK THIS GATE HAS THE DATA FOR.
            # Every reading above is taken from the shipped copy. Nothing else could say whether
            # that file came out of a cohort run at all - except the file cohort.py actually
            # writes, sitting beside it. Reading only one direction left a shipped copy that no
            # run produced indistinguishable from a re-issued one. Found by Fable.
            #
            # The message names the READING and not a cause. A hand edit produces this state; so
            # does `git checkout <older> -- public/`, a partial restore, or a revert that touches
            # one path. `ReadState` above declines to name `NEVER_RUN` for exactly this reason,
            # and the first draft of this line called the state a forgery two hundred lines below
            # that refusal.
            out.append(
                f"SHIPPED AHEAD OF THE RUN: the build copy is stamped "
                f"{run.generated_at.isoformat()}, later than anything scripts/cohort.py emitted "
                f"({emitted.generated_at.isoformat()}). Something other than a cohort run last "
                "wrote the file this gate takes all of its evidence from, and which is not "
                "knowable from here")

    # The finding that fires in the ordinary case is produced by `Registry.sweep`, which knows
    # nothing about cohorts and must not. The remedy is attached here, where the component is known:
    # a named finding whose reader has to go and work out what to do about it gets postponed.
    return [f + ". " + REMEDY if f.startswith("SILENCE") else f for f in out]


def sweep(now: datetime, root: Path | None = None) -> list[str]:
    """Sweep this repository's obligations. The entry point for the gate and for the operator."""
    base = root or ROOT
    return findings(read_run(base / SHIPPED), now, emitted=read_run(base / EMITTED))


def main() -> int:
    problems = sweep(datetime.now(timezone.utc))
    if problems:
        print("X LIVENESS:")
        for p in problems:
            print(f"  - {p}")
        return 1
    run = read_run(ROOT / SHIPPED)
    due = run.generated_at + MAX_AGE[Interval.BEFORE_REISSUE]
    print(f"LIVENESS: clean (1 obligation; cohort last shipped {run.generated_at.isoformat()}, "
          f"re-issue due by {due.isoformat()}, {run.rows} rows lapse "
          f"{run.earliest_valid_until.isoformat()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
