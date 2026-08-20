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

THE SECOND OBLIGATION (T-F7) WATCHES A BLOCKER RATHER THAN A LAPSE. T-2.15b - on-chain publication
into the ERC-8004 Validation Registry - has no target: `docs/MEASUREMENT_QM1.md` measured on
2026-08-20 that the registry is not deployed on any chain. Nothing lapses if that stays true, and
that is exactly why it needed an instrument: an external blocker nobody re-checks stops being
"cannot" and becomes "forgot", silently, because the state changes on somebody else's schedule.
Both obligations are declared into ONE registry, so the door reports the incubator's commitments in
one place rather than in two that can disagree about which of them ran.
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

# The vocabulary of the second obligation's states is IMPORTED rather than restated. Liveness has
# no business knowing what ERC-8004 is, and after this import it still does not: what crosses the
# boundary is the set of names the record can carry, not the standard. A copy of those five strings
# here would be a rule in two places, and the copy that drifts is the one nobody is watching (L-2).
# The AST guarantee this could have broken is about the METHODOLOGY - scorer, control_map,
# passport, ladder - and liveness is not among them (tests/test_transport_independence.py).
from src.transport.erc8004_deployment import (
    BLOCKED_STEP,
    RECORD,
    RecordState,
    TargetState,
    read_record,
)

ROOT = Path(__file__).resolve().parents[2]

WATCH_RECORD = RECORD
"""Renamed on arrival to sit beside `SHIPPED` and `EMITTED`, which are also paths this module
sweeps. The path itself is defined once, where the record's shape is."""

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

WATCH_COMPONENT = "validation_target_watch"
WATCH_EXPECTED_EVIDENCE = ("a run of scripts/watch_validation_registry.py against the ERC-8004 "
                           "deployment list, recorded in " + WATCH_RECORD.as_posix())
WATCH_CONSUMER = (
    "src/transport/erc8004.py: Erc8004Transport.publish() reads the record and refuses citing the "
    "state and the date it was measured, instead of asserting a blocker nobody re-checked")
"""WHO READS THE RESULT - and the honest limit on that sentence.

`publish()` reproduces the reading to its caller; it does not BRANCH on it, because there is no
second branch to take until T-2.15b is built. The actor who acts on the result is a person - the
one who schedules T-2.15b - and the finding below is how it reaches them. That is the terminus the
watcher chain is allowed to have (ABI-16-7) and not a gap in it. What the named consumer buys is
the thing that was actually wrong before: `publish()` refused with a standing claim about the
world, and now refuses with a dated measurement of it."""


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
    # `fromisoformat` REJECTS A TRAILING `Z` ON PYTHON 3.10, which is the interpreter this host and
    # CI both pin (see pyproject). It is also the commonest ISO spelling of UTC there is, so a
    # record written by anything other than this repository's own `isoformat()` would have read as
    # an unusable timestamp - an instrument failure reported as a fact about the artefact.
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
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


@dataclass(frozen=True)
class TargetWatch:
    """What the record of the last Validation Registry check says, on its two separate axes.

    `record` is how the FILE read; `target` is what the SOURCE said when it was read. Collapsing
    them would lose the case this obligation is mostly in: a file that reads perfectly and records
    that the instrument failed.
    """

    record: RecordState
    checked_at: datetime | None = None
    """When the last MEASUREMENT was taken - the only thing that is evidence of participation, and
    so the only thing the interval rides. None means either that no measurement has ever been taken
    or that the field could not be read; `record` says which."""
    target: TargetState | None = None
    addresses: tuple[str, ...] = ()
    rows: tuple[str, ...] = ()
    """The document's own lines behind those addresses. A finding that hands over a bare address
    invites scheduling against a testnet, or against a function signature in a code sample."""
    source_url: str | None = None
    attempt_rows: tuple[str, ...] = ()
    """The lines the LAST RUN could not classify. Separate from `rows` because the finding that
    quotes them is about the attempt, and taking them from the measurement block printed "lines the
    record does not carry" in the only case that ever reaches it - the whole rationale for that
    state being that a reader must see what the instrument saw. Found by Fable."""
    attempt: TargetState | None = None
    """WHAT THE LAST RUN ESTABLISHED, WHICH MAY BE NOTHING - and the reason this field exists is a
    defect, not a symmetry. When the record kept only the measurement, a run reporting that the
    deployment list had become unrecognisable left the file saying `no_target` inside its interval
    and the sweep returned nothing at all: a green gate meaning "did not look", for up to
    twenty-three days. Reported below the moment it is written."""
    attempt_at: datetime | None = None


def read_watch(path: Path) -> TargetWatch:
    """Read the watch's record. The file's shape is parsed once, in the module that owns it.

    The timestamp is parsed HERE and not there: whether that string is a time only matters to an
    interval, and the interval is this module's business. `erc8004_deployment` hands it over as
    written, so the rule lives in one place.
    """
    r = read_record(path)
    attempt_at = _parse_ts(r.attempt_at_raw)
    common = dict(target=r.target, addresses=r.validation_addresses, rows=r.validation_rows,
                  source_url=r.source_url, attempt=r.attempt, attempt_at=attempt_at,
                  attempt_rows=r.attempt_rows)
    if r.checked_at_raw is None:
        # No measurement block, or none that got this far. `record` already distinguishes "the file
        # says no measurement has ever been taken" (READ) from "the field was unusable".
        return TargetWatch(r.state, **common)
    checked_at = _parse_ts(r.checked_at_raw)
    state = r.state if checked_at is not None else RecordState.BAD_CHECKED_AT
    return TargetWatch(state, checked_at=checked_at, **common)


def declare(run: CohortRun, watch: TargetWatch) -> Registry:
    """The incubator's obligations, as a registry that is NOT empty by construction.

    `Registry.sweep` treats an empty registry as suspicious, so this function returning nothing
    would itself be reported rather than read as clean - which is why the declaration lives here and
    not inside the caller that consumes it.

    BOTH ARGUMENTS ARE REQUIRED, and that is deliberate rather than tidy. A default would let a
    caller build a registry that silently holds one obligation instead of two, and a sweep of an
    obligation nobody declared reports exactly the same nothing as a sweep that found it clean -
    which is the defect the whole module exists to refuse.
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
    r.declare(Obligation(component=WATCH_COMPONENT, expected_evidence=WATCH_EXPECTED_EVIDENCE,
                         interval=Interval.WHILE_BLOCKED,
                         last_seen=watch.checked_at, consumer=WATCH_CONSUMER,
                         # THE FLAG IS ABOUT WHETHER `last_seen` COULD BE READ, which is what its
                         # own docstring in obligations.py insists on - and that is NOT the same as
                         # its being absent. A record that reads perfectly and carries
                         # `measurement: null` has told us, legibly, that no measurement has ever
                         # been taken: `last_seen=None` with the flag DOWN, which prints "has never
                         # presented evidence of participation ... a FINDING, not missing data",
                         # and that is exactly true of it. Only a record we could not read earns
                         # NOT ASSESSED. The first draft flagged both, which put the one conclusion
                         # an unreadable instrument may not draw on top of a state the instrument
                         # had read perfectly well.
                         evidence_unreadable=(watch.checked_at is None
                                              and watch.record is not RecordState.READ)))
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

WATCH_REMEDY = ("Remedy: `python3 scripts/watch_validation_registry.py` (the read itself needs no "
                "credential), `python3 -m src.liveness.commitments` to see the reading, then "
                f"`git commit -m ...` {WATCH_RECORD.as_posix()} and `./scripts/push.sh`. No "
                "deploy: the record is not part of the site. A run that establishes nothing still "
                "writes - into the attempt block, never over the measurement - so it stays "
                "committable and this finding stays visible until a run succeeds.")
"""Runnable unattended, for the same reason `REMEDY` above is: the reader is an agent in a
non-interactive shell.

"NO DEPLOY" IS IN THE STRING because every other liveness remedy here ends with a step only the
operator can perform, and a reader who assumed this one did too would leave it undone. "IF IT
CHANGED" is in it because a re-check that finds the same answer still rewrites the timestamp, and a
reader told to commit unconditionally would be puzzled by a run that did not write at all. And the
last sentence is there because the first draft of this remedy had a state in which following it
exactly left a dirty tree that `push.sh` would not send - a remedy that does not reach the door it
names, which is L-9 and which `REMEDY` above was already rewritten once to close."""

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


def _target_findings(watch: TargetWatch) -> list[str]:
    """What the last check of the ERC-8004 deployment list established - or why it established
    nothing. The INTERVAL is not judged here; that belongs to the obligation.

    THE GOOD NEWS IS A RED, AND THAT IS THE POINT OF THE COMPONENT. `target_present` means the
    external blocker on T-2.15b has lifted, and a blocker that lifts quietly is how "cannot"
    becomes "forgot": the plan goes on saying the step cannot be scheduled, and the documents go on
    saying NOT DEPLOYED, both of them now claims stronger than the artefact. So it stops the build
    until a person has looked, and the finding says what looking consists of.

    THE TWO AXES ARE REPORTED INDEPENDENTLY, and the draft that returned early on the first of them
    was the defect. `checked_at` and `state` fail separately: a record whose timestamp does not
    parse still holds the state that was read - and on Python 3.10, where `fromisoformat` rejects a
    trailing `Z`, that is the commonest ISO spelling there is. That draft printed "neither when the
    list was last read NOR what it said WAS ESTABLISHED" while holding `target_present` and an
    address in the same dataclass: the one finding this whole component exists to raise, suppressed
    by an unrelated field, under a sentence asserting the opposite of what the instrument held.
    Discarding a measurement that WAS taken - the defect this module was rewritten for once
    already, in its `PARTIALLY READ` branch, in the mirror direction. Found by Fable.
    """
    out: list[str] = []
    where = WATCH_RECORD.as_posix()

    if watch.record is not RecordState.READ:
        # FOUR EXPLICIT BRANCHES OVER TWO INDEPENDENT FACTS, and the fourth is written out even
        # though no caller can reach it today: `read_record` yields a target only on a clean read,
        # so "the record is broken and BOTH halves survived" does not occur. The draft this
        # replaced folded it into an f-string that would have interpolated the word `None` into a
        # finding. A branch that cannot be reached costs a sentence; a finding that prints `None`
        # at the door costs a reader's trust in every other line beside it.
        when_known = watch.checked_at is not None
        said_known = watch.target is not None
        if not when_known and not said_known:
            out.append(
                f"NOT MEASURED: the watch record at {where} is {watch.record.value}, so neither "
                "when the ERC-8004 deployment list was last read NOR what it said WAS "
                "ESTABLISHED. The obligation below is NOT ASSESSED for the same reason, and none "
                "of this says the watch failed to run - that is a different fact and this "
                f"instrument cannot see it. {WATCH_REMEDY}")
        elif not when_known:
            out.append(
                f"PARTIALLY READ: the watch record at {where} is {watch.record.value}, so WHEN the "
                "deployment list was last read is unknown and the obligation below is NOT "
                "ASSESSED. What it SAID was read, and is reported on its own line below - a "
                f"timestamp that failed to parse does not unsay it. {WATCH_REMEDY}")
        elif not said_known:
            out.append(
                f"PARTIALLY READ: the watch record at {where} is {watch.record.value}. "
                "`checked_at` was read, so the interval below is assessed on it; what is unknown "
                f"is what the deployment list said. {WATCH_REMEDY}")
        else:
            out.append(
                f"PARTIALLY READ: the watch record at {where} is {watch.record.value}, and yet "
                "both `checked_at` and the state were read. Everything below is assessed on them; "
                f"what is unknown is whatever else the record was meant to carry. {WATCH_REMEDY}")

    # THE TWO BLOCKS ARE RECONCILED, AND NOTHING DID THAT UNTIL NOW.
    #
    # A second source of truth with no comparison between them is the defect the cohort obligation
    # already carries `SHIPPED AHEAD OF THE RUN` for. Here it had a worse shape: the loop below
    # reports only NON-measurements and `TARGET APPEARED` was keyed on the measurement block alone,
    # so a record whose most recent line said `target_present` swept CLEAN. The attempt axis
    # carried bad news and not good news - and good news is the whole reason the component exists.
    # The script cannot write that state; a partial `git checkout <older> -- public/`, a merge
    # taking one block from each side, or any future writer can. Found by Fable.
    if watch.attempt is not None and watch.attempt.is_measured:
        newer = (watch.attempt_at is not None and watch.checked_at is not None
                 and watch.attempt_at > watch.checked_at)
        if watch.target is None or watch.attempt is not watch.target or newer:
            out.append(
                f"BLOCKS DISAGREE: the last attempt measured {watch.attempt.value}"
                f"{' at ' + watch.attempt_at.isoformat() if watch.attempt_at else ''}, and the "
                f"measurement block holds "
                f"{watch.target.value if watch.target else 'nothing'}"
                f"{' from ' + watch.checked_at.isoformat() if watch.checked_at else ''}. A run "
                "that measures something writes BOTH, so these cannot have come from one run of "
                "scripts/watch_validation_registry.py - a partial restore, a merge that took one "
                "block from each side, or a hand edit will do it, and WHICH is not knowable from "
                f"here. Re-run the watch before believing either. {WATCH_REMEDY}")

    if TargetState.TARGET_PRESENT in (watch.attempt, watch.target):
        # FIRED OFF EITHER BLOCK. Which one holds it is a question about the record's consistency,
        # answered by the finding above; that a target was seen at all is news from whichever line
        # saw it, and a reader who has to work out which block to look in has been told too late.
        listed = ", ".join(watch.addresses) or "an address the record does not list"
        quoted = "; ".join(watch.rows or watch.attempt_rows) or "rows the record does not carry"
        out.append(
            f"TARGET APPEARED: the ERC-8004 deployment list carried a Validation Registry address "
            f"({listed}) when it was last read, on these lines: {quoted}. {BLOCKED_STEP} has "
            "somewhere to write for the first time, so the external blocker on it is spent. Read "
            "those lines in the document first - the address alone does not say which chain, and a "
            "testnet is not a target - then name the unaudited-contract risk in an explicit "
            "decision before scheduling the step, and correct every document that still says NOT "
            "DEPLOYED, docs/MEASUREMENT_QM1.md among them. This gate is red on GOOD news "
            "deliberately, because a blocker that lifts in silence becomes a step nobody scheduled")
    # THE LAST RUN, REPORTED THE MINUTE IT HAPPENED, and this block is the whole answer to the
    # draft in which a run that established nothing left the record saying `no_target` and the
    # sweep clean for up to twenty-three days.
    # PAIRED WITH THEIR POSITION, not compared by identity. `state is watch.target` was True on the
    # FIRST iteration whenever both blocks held the same member - which is the ordinary case after a
    # repeated failure - so the attempt was described as "the measurement block, which only a
    # measuring run may write" and quoted the wrong rows. Enum members are singletons; `is` asks
    # which VALUE this is, never which FIELD it came from.
    for state, from_measurement in ((watch.attempt, False), (watch.target, True)):
        if state is None or state.is_measured:
            continue
        last = from_measurement
        when = ("" if last else
                f" on {watch.attempt_at.isoformat()}" if watch.attempt_at else " (undated)")
        where_from = ("the measurement block, which only a measuring run may write - so something "
                      "other than this script wrote it" if last else
                      f"the last run of the watch{when}")
        if state is TargetState.ROW_NOT_CONCLUSIVE:
            # THE HONEST MAYBE, DELIBERATELY NEITHER NEIGHBOUR. Calling it a target sends somebody
            # to schedule on-chain publication against a line in a code sample; calling it an
            # absence hides a registry that deployed under a renamed row.
            #
            # ONE EXIT, NOT TWO, AND THE FIRST DRAFT OFFERED TWO. "Schedule the step" clears
            # nothing: the record still holds the same state and the finding fires again on every
            # sweep, because there is no acknowledgement anywhere in this design and adding one
            # would be a way to mark an unread instrument as read. The parser is the only thing
            # that can change the reading, so tightening it - with a test - is the act, and
            # scheduling follows from what it then says. Found by Fable.
            quoted = ("; ".join(watch.attempt_rows if not last else watch.rows)
                      or "lines the record does not carry")
            out.append(
                f"NOT MEASURED: {where_from} recorded {state.value} - a line naming validation "
                f"beside an address that it could not tell from a code example: {quoted}. Whether "
                f"{BLOCKED_STEP} has a target WAS NOT ESTABLISHED. Open "
                f"{watch.source_url or 'the source named in the record'}, read that line, and "
                "teach src/transport/erc8004_deployment.py to classify the shape - with a test "
                "either way. Only that changes the reading; scheduling the step does not clear "
                "this finding and is not meant to")
        else:
            out.append(
                f"NOT MEASURED: {where_from} recorded {state.value}, so whether a Validation "
                f"Registry address exists WAS NOT ESTABLISHED - and that is not an absence. The "
                "interval is not advanced by a run that measured nothing; what it rides is the "
                f"last one that did. {WATCH_REMEDY}")
    return out


def _with_remedy(finding: str) -> str:
    """Attach the remedy that belongs to the component the finding names.

    ROUTED BY COMPONENT RATHER THAN BY POSITION. `Registry.sweep` returns the obligations in one
    list and knows nothing about either of them; a single remedy appended to everything starting
    with SILENCE would have told a reader whose validation-registry watch had gone quiet to re-run
    the cohort and deploy the site - instructions that do not reach the state they were printed
    for, which is the L-9 defect `REMEDY` above was already rewritten once to close.
    """
    if not finding.startswith("SILENCE"):
        return finding
    return finding + ". " + (WATCH_REMEDY if WATCH_COMPONENT in finding else REMEDY)


def findings(run: CohortRun, now: datetime, watch: TargetWatch,
             emitted: CohortRun | None = None) -> list[str]:
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

    out.extend(declare(run, watch).sweep(now))

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

    out.extend(_target_findings(watch))

    # The finding that fires in the ordinary case is produced by `Registry.sweep`, which knows
    # nothing about cohorts and must not. The remedy is attached here, where the component is known:
    # a named finding whose reader has to go and work out what to do about it gets postponed.
    return [_with_remedy(f) for f in out]


def sweep(now: datetime, root: Path | None = None) -> list[str]:
    """Sweep this repository's obligations. The entry point for the gate and for the operator."""
    base = root or ROOT
    return findings(read_run(base / SHIPPED), now, read_watch(base / WATCH_RECORD),
                    emitted=read_run(base / EMITTED))


def main() -> int:
    problems = sweep(datetime.now(timezone.utc))
    if problems:
        print("X LIVENESS:")
        for p in problems:
            print(f"  - {p}")
        return 1
    run = read_run(ROOT / SHIPPED)
    due = run.generated_at + MAX_AGE[Interval.BEFORE_REISSUE]
    watch = read_watch(ROOT / WATCH_RECORD)
    watch_due = watch.checked_at + MAX_AGE[Interval.WHILE_BLOCKED]
    print(f"LIVENESS: clean (2 obligations; cohort last shipped {run.generated_at.isoformat()}, "
          f"re-issue due by {due.isoformat()}, {run.rows} rows lapse "
          f"{run.earliest_valid_until.isoformat()})")
    # The clean line carries the READING and not only the fact that a check happened. "The watch
    # ran on time" and "there is still nowhere to publish" are two different pieces of news, and a
    # summary that printed the first alone would leave the second to be looked up.
    print(f"          {WATCH_COMPONENT}: {watch.target.value} for {BLOCKED_STEP}, read "
          f"{watch.checked_at.isoformat()}, due again by {watch_due.isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
