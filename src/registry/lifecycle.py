"""T-2.8 - verification state machine (ABI-4-5, ABI-15-1..15-6, ABI-33-2..33-4).

FOUR RULES, each existing because of a concrete failure:

1. **An undefined transition is IMPOSSIBLE, not "undocumented"** (ABI-10-5). The difference is
   fundamental: an undocumented transition still executes; an impossible one does not.

2. **`suspended` is NOT "we could not measure"** (ABI-33-4). A verifier that suspends a subject
   for its own blindness punishes someone for its own failure. An unmeasurable subject yields
   `stale`, never `suspended`. A missing measurement is not a violation.

3. **`stale` arrives BY TIME and needs no event** (ABI-15-5). A fact needs a place to expire; a
   fact with no expiry does not go stale, it goes wrong.

4. **History is IMMUTABLE and carries its trigger** (ABI-15-4, ABI-19-3). A record that disappears
   reads as closure to anything that reads absence as resolution.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Status(str, Enum):
    UNVERIFIED = "unverified"
    IN_PROGRESS = "verification_in_progress"
    VERIFIED = "verified"
    STALE = "stale"
    SUSPENDED = "suspended"
    FAILED = "failed_or_rejected"
    WITHDRAWN = "withdrawn"


class Trigger(str, Enum):
    MANDATE_ACCEPTED = "mandate_accepted"
    EVIDENCE_SUFFICIENT = "evidence_sufficient"
    EVIDENCE_INSUFFICIENT = "evidence_insufficient"
    VIOLATION_FOUND = "violation_found"
    VALIDITY_EXPIRED = "validity_expired"
    REMEDIED = "remedied"
    MANDATE_WITHDRAWN = "mandate_withdrawn"
    UNMEASURABLE = "unmeasurable"          # does NOT lead to suspended - see rule 2


ALLOWED: dict[tuple[Status, Trigger], Status] = {
    (Status.UNVERIFIED, Trigger.MANDATE_ACCEPTED): Status.IN_PROGRESS,
    (Status.IN_PROGRESS, Trigger.EVIDENCE_SUFFICIENT): Status.VERIFIED,
    (Status.IN_PROGRESS, Trigger.EVIDENCE_INSUFFICIENT): Status.FAILED,
    (Status.IN_PROGRESS, Trigger.UNMEASURABLE): Status.STALE,
    (Status.VERIFIED, Trigger.VALIDITY_EXPIRED): Status.STALE,
    (Status.VERIFIED, Trigger.VIOLATION_FOUND): Status.SUSPENDED,
    (Status.VERIFIED, Trigger.UNMEASURABLE): Status.STALE,     # NOT suspended (rule 2)
    (Status.STALE, Trigger.MANDATE_ACCEPTED): Status.IN_PROGRESS,
    (Status.SUSPENDED, Trigger.REMEDIED): Status.IN_PROGRESS,
    (Status.FAILED, Trigger.MANDATE_ACCEPTED): Status.IN_PROGRESS,
}
for _s in Status:
    if _s is not Status.WITHDRAWN:
        ALLOWED[(_s, Trigger.MANDATE_WITHDRAWN)] = Status.WITHDRAWN

TERMINAL = frozenset({Status.WITHDRAWN})
NEGATIVE_PUBLIC_VERDICTS = frozenset({Status.SUSPENDED, Status.FAILED})
"""Publishing a negative verdict about a named company is a LEGAL ACT (ABI-19-4, ABI-30-5).
It requires an evidence standard, notice, right of reply and a correction procedure."""


class UndefinedTransition(Exception):
    """Not "undocumented" - IMPOSSIBLE."""


@dataclass(frozen=True)
class Entry:
    at: datetime
    frm: Status
    to: Status
    trigger: Trigger
    evidence_ref: str | None


class Lifecycle:
    """State plus IMMUTABLE history. Records are only ever appended."""

    def __init__(self, status: Status = Status.UNVERIFIED) -> None:
        self._status = status
        self._history: list[Entry] = []

    @property
    def status(self) -> Status:
        return self._status

    @property
    def history(self) -> tuple[Entry, ...]:
        return tuple(self._history)      # a copy: history cannot be rewritten from outside

    def apply(self, trigger: Trigger, at: datetime, evidence_ref: str | None = None) -> Status:
        if self._status in TERMINAL:
            raise UndefinedTransition(f"{self._status.value} is terminal")
        key = (self._status, trigger)
        if key not in ALLOWED:
            raise UndefinedTransition(
                f"transition {self._status.value} --{trigger.value}--> is undefined and therefore "
                f"impossible")
        to = ALLOWED[key]
        if to in NEGATIVE_PUBLIC_VERDICTS and not evidence_ref:
            raise UndefinedTransition(
                f"{to.value} is a public negative verdict about a named company, i.e. a legal act: "
                f"it is not issued without an evidence reference (ABI-19-4)")
        self._history.append(Entry(at, self._status, to, trigger, evidence_ref))
        self._status = to
        return to
