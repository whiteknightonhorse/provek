"""T-2.10 - obligation registry and silence as an observable state (ABI-16-1..16-11).

WHAT IS NOT EVIDENCE OF PARTICIPATION (ABI-16-3): the presence of a file, importability, a green
unit test. All of these prove the code EXISTS and nothing about whether it participates. Evidence
comes only from actual execution.

FIVE STATES OF SLEEPING CODE (ABI-16-5, ABI-16-6). The fifth exists because a producer verified in
isolation proves nothing about its consumer: the code runs, returns a real result, and NOBODY
READS IT.

SILENCE MUST BECOME A FINDING (ABI-16-4). Expected evidence missing beyond its interval is a named
finding - otherwise silence is indistinguishable from health.

THE WATCHER CHAIN IS FINITE and its terminus is named (ABI-16-7): components -> liveness ->
external heartbeat. It does not continue past that, DELIBERATELY: an endless chain of watchers is
not reliability, it is an unanswered question.

THIS MODULE HELD NONE OF IT IN PRACTICE UNTIL 2026-08-20. Every `Registry` in the tree was built
inside a test and filled by that same test, so the layer that exists to make silence observable had
no obligation of its own and produced nothing anybody read - the fifth state above, turned on the
component that defines it. `src/liveness/commitments.py` is where the incubator's own obligations
are declared; this file stays a mechanism and knows nothing about which components exist.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class Interval(str, Enum):
    EVERY_RUN = "every_run"
    EVERY_TASK = "every_task"
    EVERY_DEPLOY = "every_deploy"
    DAILY = "daily"
    BEFORE_REISSUE = "before_reissue"
    """A verdict lapses by time with no event (ABI-15-5), so the obligation to re-measure has a
    deadline set by the verdict rather than by a habit. Its max age is derived below."""

    WHILE_BLOCKED = "while_blocked"
    """A step of ours is blocked by something outside this repository, so the state changes on
    somebody else's schedule and no event reaches us. Unlike BEFORE_REISSUE this deadline is NOT
    set by the world: nothing lapses if the check is late, only the discovery is. Its max age is
    therefore a habit and is derived from the one habit this project actually has."""


RENEWAL_MARGIN = timedelta(days=7)
"""How much still-valid time a re-issue finding must leave the operator.

ORIGIN: the remedy's dependency chain, not a measurement of it. The last step of re-issuing is a
MANUAL `wrangler pages deploy` that only the operator can perform (L-9, D-19), so the margin has to
be long enough for the operator to be away, come back and still act before the rows lapse. Seven
days is that estimate and it is stated as one. What would move it is a reading of how long the
operator is actually absent between deploys, which nothing in this project records yet. The steps
are enumerated once, in `docs/LIVENESS_OPERATIONS.md`, and not counted again here: a procedure
described in two places drifts in one of them (L-2).

IT ALSO ASSUMES THE FINDING IS SEEN ON THE DAY IT FIRES, which is a second estimate hiding inside
the first. The sweep runs at the door and on a daily schedule in CI; between the run that goes red
and a person reading it there is a lag this project does not measure either.

A margin of zero is the failure this constant exists to prevent: a finding that arrives on the day
of the lapse reports the loss instead of preventing it."""

PASSPORT_VALIDITY = timedelta(days=30)
"""The window `src/passport/passport.py` stamps into `valid_until` (`validity_days: int = 30`).

This is a SECOND COPY of that number, which is the shape L-2 warns about, and it is not imported:
liveness reading the constant would only establish that the two agree by construction. What is
worth knowing is whether the deadline computed here lands before the lapse the SHIPPED rows
actually carry, and `commitments.py` measures exactly that - so a drift becomes a named finding
rather than a silently wrong deadline."""


MAX_AGE = {Interval.DAILY: timedelta(days=1), Interval.EVERY_RUN: timedelta(hours=6),
           Interval.EVERY_TASK: timedelta(days=3), Interval.EVERY_DEPLOY: timedelta(days=14),
           Interval.BEFORE_REISSUE: PASSPORT_VALIDITY - RENEWAL_MARGIN}
"""Written as the subtraction rather than as `timedelta(days=23)`: the derivation is the rule, and
a bare 23 would survive a change to either constant it came from."""

MAX_AGE[Interval.WHILE_BLOCKED] = MAX_AGE[Interval.BEFORE_REISSUE]
"""THE INTERVAL RIDES THE HABIT, and the reference rather than a number is the honest form.

NOTHING IN THE WORLD SETS THIS DEADLINE. A blocked step misses no lapse by being discovered late;
what is lost is only the days between the block lifting and somebody noticing. So there is no
quantity to derive from, and the alternative to deriving is inventing - a round number, stated as
though it had been measured, which is the defect this project is built to find.

WHAT IS REAL IS THE CADENCE AT WHICH ANYBODY IS ACTUALLY IN THIS TREE PERFORMING LIVENESS WORK,
and that is `BEFORE_REISSUE`: the re-issue habit is the only recurring appointment this repository
has. A check that fires on the same beat is one somebody is already standing there to perform. A
faster one would be red most mornings with no act available to clear it, and a gate that cries
every day teaches the reader to walk past it - the reason `docs/LIVENESS_OPERATIONS.md` refuses an
obligation for the deploy.

THE COUPLING IT CREATES IS NAMED RATHER THAN HIDDEN: shorten the passport's validity and this
interval shortens too, for a reason that has nothing to do with the blocked step. That is the
correct direction anyway - both are habits, and the habit moved. It is a defect only if this
deadline ever acquires a source of its own, and then the answer is its own entry above, not a
literal here.
"""


class SleepState(str, Enum):
    """Five states of sleeping code. Collapsing them into "works / does not work" is forbidden."""
    UNCOMMITTED = "code_exists_not_committed"
    UNDEPLOYED = "committed_not_deployed"
    UNINVOKED = "deployed_not_invoked"
    ALWAYS_SKIPS = "invoked_but_always_no_op"
    UNREAD = "produces_result_nobody_reads"     # the fifth: no consumer


@dataclass
class Obligation:
    component: str
    expected_evidence: str
    interval: Interval
    last_seen: datetime | None = None
    consumer: str | None = None        # who READS the result; None = the fifth state
    evidence_unreadable: bool = False
    """THE THIRD STATE OF `last_seen`, and it was missing until 2026-08-20.

    `None` meant "this component has never presented evidence" AND "we could not look" - one value
    for two states of the world, invariant 1 inside the dataclass built to enforce it. The first
    caller to read evidence off a file (`commitments.py`) hit it immediately: an absent registry
    produced the message "has never presented evidence of participation ... This is a FINDING, not
    missing data", which is exactly what an unreadable instrument may not conclude. Found by Fable.

    IT MEANS "`last_seen` COULD NOT BE READ", not "something about the source was wrong". A caller
    whose file parsed far enough to yield a timestamp must leave this False even if the rest of the
    document was unusable - otherwise a measurement that WAS taken is thrown away and the sweep
    reports UNKNOWN over a quantity it holds. That is the second thing Fable caught here.
    """

    def findings(self, now: datetime) -> list[str]:
        """EVERY named finding that applies. An empty list means "checked and clean", not "did not
        look".

        THIS RETURNED ONE STRING UNTIL 2026-08-20, AND THAT WAS THE BUG UNDERNEATH TWO OTHERS.
        Three of these conditions can be true at once, and a single return value made them race:
        whichever was tested first silenced the rest. The race was found twice in one day, once in
        each direction - first `SILENCE` hid a missing consumer, then reordering made a missing
        consumer hide a four-hundred-day outage, which is the worse trade, because a string that
        was never filled in would have silenced a measured fact. Neither ordering is right. The
        argument for testing the declaration first - that it is knowable with no evidence read - is
        an argument for REPORTING BOTH, and the second draft of this method mistook it for an
        argument about precedence. Both found by Fable, one round apart.

        The order below is now only the order they are printed in.
        """
        out: list[str] = []
        if self.consumer is None:
            out.append(f"NO CONSUMER: {self.component} produces a result nobody reads - "
                       f"the fifth state of sleeping code")
        if self.evidence_unreadable:
            out.append(f"NOT ASSESSED: {self.component}'s evidence ({self.expected_evidence}) "
                       f"could not be read, so whether it met its {self.interval.value} interval "
                       f"IS UNKNOWN - which is neither silence nor health")
        elif self.last_seen is None:
            out.append(f"SILENCE: {self.component} has never presented evidence of participation "
                       f"({self.expected_evidence}). This is a FINDING, not missing data")
        elif now - self.last_seen > MAX_AGE[self.interval]:
            out.append(f"SILENCE: {self.component} has been silent longer than its "
                       f"{self.interval.value} interval (last seen {self.last_seen.isoformat()})")
        return out


class Registry:
    """The obligation registry. An EMPTY registry is a suspicious state, not a clean one."""

    def __init__(self) -> None:
        self._items: dict[str, Obligation] = {}

    def declare(self, o: Obligation) -> None:
        self._items[o.component] = o

    def sweep(self, now: datetime) -> list[str]:
        if not self._items:
            return ["EMPTY OBLIGATION REGISTRY: there was nothing to check - which is not the "
                    "same thing as everything being clean"]
        return [f for o in self._items.values() for f in o.findings(now)]

    def watcher_chain(self) -> list[str]:
        """The chain is named explicitly and it ENDS. The terminus is justified in the docstring."""
        return ["components", "liveness", "external_heartbeat"]
