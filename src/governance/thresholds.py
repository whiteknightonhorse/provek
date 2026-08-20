"""Ratified go/no-go thresholds and the deterministic verdict computed from them.

RATIFIED BY THE OPERATOR 2026-08-19 (Q-D1 closed): 30 candidates, 5 mandates, 90 days.

THESE NUMBERS ARE ASSIGNED, NOT MEASURED - and that is stated rather than hidden. The project's
rule "a threshold is derived from a measurement whose procedure is recorded, never chosen to make
a test pass" does not apply here: there is nothing to measure in a decision about when to stop.
What the rule DOES demand is that an assigned number be labelled as assigned, so nobody later
mistakes it for a finding.

WHY THE VERDICT IS CODE AND NOT A DISCUSSION. A go/no-go argued in prose is decided by whoever
argues last. Computed from recorded inputs, it is decided by the inputs - and the inputs carry
their own "not measured" states, so a missing input can never masquerade as a pass.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.abs_profile.measured import Measurement

CANDIDATES_GO = 30
"""ASSIGNED. External subjects qualifying under spec 2.7 needed to proceed."""

CANDIDATES_REVISIT = 10
"""ASSIGNED. Below this the answer is REVISIT with a growth axis, never a terminal stop.

Revision 1.1 fixed this: the 2.7 definition is deliberately strict and the market is young, so a
terminal stop here would kill the project for being early. A terminal stop requires the ABSENCE OF
GROWTH measured over a second window, not a low first reading."""

MANDATES_GO = 5
"""ASSIGNED. Subjects that must actually grant a mandate - consent, not interest."""

CLOCK_DAYS = 90
"""ASSIGNED. The window for mandates, counted from the FIRST 10 OFFERS MADE.

Not from "intake opened": that would measure our own outreach delay and call it demand."""

OFFERS_BEFORE_CLOCK = 10


class Verdict(str, Enum):
    GO = "go"
    REVISIT = "revisit"
    STOP = "stop"
    NOT_MEASURED = "not_measured"


@dataclass(frozen=True)
class Inputs:
    """Everything the verdict reads. Each may be absent, and absence is not a zero."""
    qualifying_candidates: Measurement
    mandates_granted: Measurement
    days_since_clock_start: Measurement
    growth_observed: bool | None = None      # None = the second window has not run yet


def evaluate(i: Inputs) -> tuple[Verdict, str]:
    """Compute the verdict. Returns (verdict, the reason in one sentence).

    A missing input yields NOT_MEASURED - never GO and never STOP. A verifier that decides on data
    it does not have is the defect this whole product exists to expose.
    """
    if not i.qualifying_candidates.is_measured:
        return Verdict.NOT_MEASURED, (
            "qualifying candidates were not measured: the 2.7 filter over the registry population "
            "has not been run, and an unmeasured input may not decide")

    n = i.qualifying_candidates.value
    if n < CANDIDATES_REVISIT:
        if i.growth_observed is None:
            return Verdict.REVISIT, (
                f"{n} candidates is below {CANDIDATES_REVISIT}, but growth has not been measured "
                f"yet - a young market is not a dead one, so this is a revisit, not a stop")
        if not i.growth_observed:
            return Verdict.STOP, (
                f"{n} candidates and NO growth across the second window - the market is absent, "
                f"not merely early")
        return Verdict.REVISIT, f"{n} candidates but growth is present - measure again"

    if n < CANDIDATES_GO:
        return Verdict.REVISIT, f"{n} candidates is below the go threshold of {CANDIDATES_GO}"

    if not i.mandates_granted.is_measured:
        return Verdict.NOT_MEASURED, "mandates granted were not measured"
    if not i.days_since_clock_start.is_measured:
        return Verdict.NOT_MEASURED, (
            "the clock has not started: it starts at the first "
            f"{OFFERS_BEFORE_CLOCK} offers made, not when intake opened")

    if i.mandates_granted.value >= MANDATES_GO:
        return Verdict.GO, (
            f"{n} candidates and {i.mandates_granted.value} mandates granted - both thresholds met")
    if i.days_since_clock_start.value >= CLOCK_DAYS:
        return Verdict.STOP, (
            f"{CLOCK_DAYS} days elapsed with {i.mandates_granted.value} mandates of "
            f"{MANDATES_GO} - the voluntariness hypothesis is refuted")
    return Verdict.REVISIT, (
        f"{i.mandates_granted.value} of {MANDATES_GO} mandates, "
        f"{int(i.days_since_clock_start.value)} of {CLOCK_DAYS} days - still inside the window")
