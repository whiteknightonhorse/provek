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


MAX_AGE = {Interval.DAILY: timedelta(days=1), Interval.EVERY_RUN: timedelta(hours=6),
           Interval.EVERY_TASK: timedelta(days=3), Interval.EVERY_DEPLOY: timedelta(days=14)}


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

    def finding(self, now: datetime) -> str | None:
        """A named finding, or None. `None` means "checked and clean", not "did not look"."""
        if self.last_seen is None:
            return (f"SILENCE: {self.component} has never presented evidence of participation "
                    f"({self.expected_evidence}). This is a FINDING, not missing data")
        if now - self.last_seen > MAX_AGE[self.interval]:
            return (f"SILENCE: {self.component} has been silent longer than its "
                    f"{self.interval.value} interval (last seen {self.last_seen.isoformat()})")
        if self.consumer is None:
            return (f"NO CONSUMER: {self.component} produces a result nobody reads - "
                    f"the fifth state of sleeping code")
        return None


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
        return [f for f in (o.finding(now) for o in self._items.values()) if f]

    def watcher_chain(self) -> list[str]:
        """The chain is named explicitly and it ENDS. The terminus is justified in the docstring."""
        return ["components", "liveness", "external_heartbeat"]
