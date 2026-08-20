"""T-2.12 - mandate for active probing (ABI-6-4, operator ruling A-9).

"Testing someone's production business without a defined mandate is an incident, not a
verification."

A mandate is a legal object, not a checkbox. It must state permitted actions, their limits, the
prohibition on harming the subject's real customers, liability for collateral damage, abort
conditions, and how it is revoked.

FAIL-CLOSED: no mandate, an expired mandate and a revoked mandate all forbid probing equally. But
they differ in the REASON: "never issued" and "revoked" are different states of the world.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Denial(str, Enum):
    NO_MANDATE = "no_mandate"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ACTION_NOT_PERMITTED = "action_not_permitted"
    RATE_EXCEEDED = "rate_exceeded"


@dataclass(frozen=True)
class Mandate:
    ref: str
    """The reference of the signed document this object stands for.

    ADDED WITH THE PROBER, AND THE GAP IT CLOSES IS OLDER THAN THE PROBER. Every passport in the
    published cohort carries `mandate_ref: "self-mandate-0001"`, written as a bare string by
    `scripts/cohort.py`, while this class - the only thing in the repository that models a mandate -
    could not express which mandate it was. So a probe could be permitted by an object that had no
    name, and a passport could name a mandate no object corresponded to. A reading has to carry the
    authority it was taken under, for the reason a verdict carries its `access_channel`: the
    instrument beside the number, or the number cannot be audited later.
    """
    subject_id: str
    permitted_actions: frozenset[str]
    max_calls_per_hour: int
    blast_radius: str                 # what specifically must NOT be affected
    liability: str                    # who answers for collateral damage
    abort_condition: str
    valid_from: datetime
    valid_until: datetime
    revoked_at: datetime | None = None
    notes: list[str] = field(default_factory=list)


def may_probe(m: Mandate | None, action: str, now: datetime,
              calls_last_hour: int = 0) -> tuple[bool, Denial | None]:
    """Is probing permitted? Returns the REASON for refusal, never a bare "no".

    A bare "no" is the same "one return value, two states of the world" defect: "no mandate was
    issued" and "the mandate was revoked" require different actions from the operator.
    """
    if m is None:
        return False, Denial.NO_MANDATE
    if m.revoked_at is not None and now >= m.revoked_at:
        return False, Denial.REVOKED
    if not (m.valid_from <= now < m.valid_until):
        return False, Denial.EXPIRED
    if action not in m.permitted_actions:
        return False, Denial.ACTION_NOT_PERMITTED
    if calls_last_hour >= m.max_calls_per_hour:
        return False, Denial.RATE_EXCEEDED
    return True, None
